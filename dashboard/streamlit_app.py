"""
Streamlit dashboard for the Privacy-Preserving Complaint Intelligence Platform.

Ties together every project layer into one view:
- Overview statistics
- Category-wise complaint volume and trends
- Privacy Protection panel: PII entities redacted + k-anonymity audit results
- Root-Cause Insights panel: causal graph visualization + top ranked root causes
- Preventive measures / recommendations based on category volume spikes

Usage
-----
    streamlit run dashboard/streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure the project root is on sys.path so 'src' is importable when
# Streamlit is launched from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.classification.live_predict import LiveComplaintProcessor

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RESULTS_PATH = Path("data/processed/pipeline_results.csv")
CAUSAL_PAIRS_PATH = Path("data/processed/causal_pairs.json")
CAUSAL_GRAPH_PATH = Path("models/saved/causal_graph.gexf")
LIVE_SUBMISSIONS_PATH = Path("data/processed/live_submissions.csv")
RESOLVED_COLUMN = "resolved"

ENTITY_TYPES = (
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ACCOUNT_NUMBER",
    "AADHAAR_NUMBER", "COMPLAINT_ID", "CREDIT_CARD", "CREDENTIAL",
)

SPIKE_THRESHOLD = 0.30

RECOMMENDATION_RULES = {
    "Debt collection": "Consider reviewing collection call scripts and staff training.",
    "Credit reporting": "Review recent changes to reporting/verification procedures.",
    "Credit/Prepaid card": "Check for recent card-related system outages or fee changes.",
    "Bank account/service": "Investigate recent changes to account terms or mobile banking stability.",
    "Mortgage": "Review recent servicing transfers or rate-adjustment communications.",
    "Student loan": "Check for recent servicer changes or repayment-plan communication issues.",
    "Personal/Payday loan": "Review recent changes to loan terms or collection practices.",
    "Money transfer": "Check for recent outages or delays in transfer processing systems.",
    "Vehicle loan or lease": "Review recent changes to payment processing or collection practices.",
}
DEFAULT_RECOMMENDATION = "Volume increase detected -- recommend a manual review of recent process or system changes."

# K-anonymity results (from src/privacy/k_anonymity_audit.py and
# k_anonymity_mitigation.py console output -- not saved to a file,
# hardcoded here as already-confirmed project results).
KANON_BASELINE_PCT_UNIQUE = 47.38
KANON_BASELINE_PCT_AT_RISK = 82.02
KANON_MITIGATED_PCT_UNIQUE = 12.95
KANON_MITIGATED_PCT_AT_RISK = 44.73
KANON_MITIGATION_STRATEGY = "quarter_binning + drop_subproduct"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_results(path: Path = RESULTS_PATH) -> pd.DataFrame:
    """Load the processed pipeline results (redaction + classification output)."""
    if not path.exists():
        st.error(f"Results file not found at {path}. Run scripts/run_pipeline_batch.py first.")
        st.stop()
    return pd.read_csv(path)


@st.cache_data(ttl=5)
def load_merged_results() -> pd.DataFrame:
    """Load and merge batch pipeline results with live submissions.

    Combines the static batch-processed dataset (pipeline_results.csv)
    with any complaints submitted live through the dashboard
    (live_submissions.csv), producing one unified DataFrame with a
    consistent schema so downstream stats/charts reflect both sources.
    Cached with a short TTL (5 seconds) rather than indefinitely, so
    newly submitted complaints appear in the dashboard shortly after
    submission without requiring a full app restart.

    Returns:
        A DataFrame combining both sources. If live_submissions.csv does
        not exist yet, returns just the batch results.
    """
    batch_df = load_results()

    entity_cols = list(ENTITY_TYPES)
    keep_cols = ["date", "predicted_category", "predicted_sub_issue",
                 "domain_confidence"] + entity_cols
    batch_subset = batch_df[[c for c in keep_cols if c in batch_df.columns]].copy()
    batch_subset["source"] = "batch"

    if LIVE_SUBMISSIONS_PATH.exists():
        live_df = pd.read_csv(LIVE_SUBMISSIONS_PATH)
        live_subset = pd.DataFrame()
        live_subset["date"] = live_df.get("timestamp")
        live_subset["predicted_category"] = live_df.get("predicted_category")
        live_subset["predicted_sub_issue"] = live_df.get("predicted_sub_issue")
        live_subset["domain_confidence"] = live_df.get("domain_confidence")
        for etype in entity_cols:
            live_subset[etype] = live_df[etype] if etype in live_df.columns else 0
        live_subset["source"] = "live"

        merged = pd.concat([batch_subset, live_subset], ignore_index=True)
    else:
        merged = batch_subset

    return merged


@st.cache_data
def load_causal_pairs(path: Path = CAUSAL_PAIRS_PATH) -> list:
    """Load the causal extraction sample data."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource
def load_causal_graph(path: Path = CAUSAL_GRAPH_PATH):
    """Load the saved causal graph, if available."""
    if not path.exists():
        return None
    return nx.read_gexf(path)


@st.cache_resource
def load_live_processor() -> LiveComplaintProcessor:
    """Load the live complaint processor once per session (expensive to init)."""
    return LiveComplaintProcessor()


def save_live_submission(result: dict) -> None:
    """Append a processed live complaint to the persistent submissions log.

    Args:
        result: The dict returned by LiveComplaintProcessor.process().
    """
    row = {
        "complaint_id": result["complaint_id"],
        "timestamp": result["timestamp"],
        "redacted_text": result["redacted_text"],
        "predicted_category": result["final_classification"]["domain"],
        "predicted_sub_issue": result["final_classification"]["sub_issue"],
        "domain_confidence": result["final_classification"]["domain_confidence"],
        "tfidf_prediction": result["model_comparison"]["tfidf_svm"]["category"],
        "sbert_prediction": result["model_comparison"]["sentence_bert_logreg"]["category"],
        "distilbert_prediction": result["model_comparison"]["distilbert"]["category"],
        "needs_review": result["agreement"]["needs_review"],
        "review_reason": result["agreement"]["review_reason"],
        "num_entities_redacted": len(result["entities_redacted"]),
    }

    entity_counts = {etype: 0 for etype in ENTITY_TYPES}
    for entity in result["entities_redacted"]:
        etype = entity.get("entity_type")
        if etype in entity_counts:
            entity_counts[etype] += 1
    row.update(entity_counts)

    LIVE_SUBMISSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)

    if LIVE_SUBMISSIONS_PATH.exists():
        existing = pd.read_csv(LIVE_SUBMISSIONS_PATH)
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    else:
        updated = pd.DataFrame([row])

    updated.to_csv(LIVE_SUBMISSIONS_PATH, index=False)


def clean_cause_value(value):
    """Normalize a cause field, treating null-like values as None."""
    if value is None:
        return None
    stripped = str(value).strip()
    if stripped == "" or stripped.lower() == "null":
        return None
    return stripped


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def compute_overview_stats(df: pd.DataFrame) -> dict:
    """Compute top-level summary statistics."""
    entity_cols = [c for c in ENTITY_TYPES if c in df.columns]
    total_pii = int(df[entity_cols].sum().sum()) if entity_cols else 0
    return {
        "total_complaints": len(df),
        "total_categories": df["predicted_category"].nunique(),
        "total_pii_redacted": total_pii,
    }


def compute_entity_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Compute total redacted-entity counts by entity type."""
    entity_cols = [c for c in ENTITY_TYPES if c in df.columns]
    if not entity_cols:
        return pd.DataFrame(columns=["entity_type", "count"])
    totals = df[entity_cols].sum().sort_values(ascending=False)
    return pd.DataFrame({"entity_type": totals.index, "count": totals.values})


def compute_category_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Flag categories with a volume spike and attach a recommendation."""
    if "date" not in df.columns:
        return pd.DataFrame(columns=["category", "volume", "pct_change", "recommendation"])

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return pd.DataFrame(columns=["category", "volume", "pct_change", "recommendation"])

    latest_period = df["date"].max().to_period("M")
    df["period"] = df["date"].dt.to_period("M")
    period_counts = df.groupby(["predicted_category", "period"]).size().reset_index(name="count")

    flagged = []
    for category in df["predicted_category"].unique():
        cat_counts = period_counts[period_counts["predicted_category"] == category]
        if len(cat_counts) < 2:
            continue
        latest_count = cat_counts[cat_counts["period"] == latest_period]["count"]
        if latest_count.empty:
            continue
        latest_count = latest_count.values[0]
        historical_avg = cat_counts[cat_counts["period"] != latest_period]["count"].mean()
        if historical_avg == 0:
            continue
        pct_change = (latest_count - historical_avg) / historical_avg
        if pct_change >= SPIKE_THRESHOLD:
            rec = RECOMMENDATION_RULES.get(category, DEFAULT_RECOMMENDATION)
            flagged.append({
                "category": category, "volume": int(latest_count),
                "pct_change": round(pct_change * 100, 1), "recommendation": rec,
            })
    return pd.DataFrame(flagged)


def build_causal_summary(causal_pairs: list) -> pd.DataFrame:
    """Build a simple root-cause frequency table from the causal pairs sample."""
    rows = []
    for record in causal_pairs:
        root = clean_cause_value(record.get("root_cause"))
        if root is not None:
            rows.append({"root_cause": root, "category": record["category"]})
    if not rows:
        return pd.DataFrame(columns=["root_cause", "count"])
    df = pd.DataFrame(rows)
    vc = df["root_cause"].value_counts().reset_index()
    # In newer pandas versions, value_counts().reset_index() already gives
    # 'root_cause' and 'count' as columns. By explicitly assigning them, we
    # handle both legacy and modern pandas without renaming errors.
    vc.columns = ["root_cause", "count"]
    return vc.head(10)


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def render_overview(df: pd.DataFrame) -> None:
    """Render the top-level overview metrics row."""
    stats = compute_overview_stats(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Complaints Processed", f"{stats['total_complaints']:,}")
    col2.metric("Categories Detected", stats["total_categories"])
    col3.metric("PII Entities Redacted", f"{stats['total_pii_redacted']:,}")


def render_category_insights(df: pd.DataFrame) -> None:
    """Render category volume charts and hierarchical drill-down."""
    st.subheader("Complaint Volume by Category")
    category_counts = df["predicted_category"].value_counts().reset_index()
    category_counts.columns = ["category", "count"]

    fig = px.bar(category_counts, x="category", y="count", color="category",
                 title="Complaints by Category")
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Complaints")
    st.plotly_chart(fig, use_container_width=True)

    selected_category = st.selectbox(
        "Drill down into a category's sub-issues:", category_counts["category"].tolist()
    )
    sub_issues = (
        df[df["predicted_category"] == selected_category]["predicted_sub_issue"]
        .dropna().value_counts().reset_index()
    )
    sub_issues.columns = ["sub_issue", "count"]
    if not sub_issues.empty:
        fig_sub = px.bar(sub_issues, x="sub_issue", y="count", title=f"Sub-issues in {selected_category}")
        fig_sub.update_layout(xaxis_title="", yaxis_title="Complaints")
        st.plotly_chart(fig_sub, use_container_width=True)
    else:
        st.info("No sub-issue predictions available for this category.")

    if "date" in df.columns:
        st.subheader("Complaint Volume Over Time")
        df_trend = df.copy()
        df_trend["date"] = pd.to_datetime(df_trend["date"], errors="coerce")
        df_trend = df_trend.dropna(subset=["date"])
        if not df_trend.empty:
            trend = (
                df_trend.groupby([df_trend["date"].dt.to_period("M").astype(str), "predicted_category"])
                .size().reset_index(name="count")
            )
            trend.columns = ["month", "category", "count"]
            fig2 = px.line(trend, x="month", y="count", color="category", markers=True,
                          title="Monthly Complaint Trend by Category")
            st.plotly_chart(fig2, use_container_width=True)


def render_privacy_panel(df: pd.DataFrame) -> None:
    """Render the Privacy Protection panel: redaction + k-anonymity results."""
    st.subheader("Privacy Protection")

    stats = compute_overview_stats(df)
    col1, col2 = st.columns(2)
    col1.metric("Privacy Breaches Prevented", f"{stats['total_pii_redacted']:,}",
                help="Sensitive entities (names, emails, phone numbers, etc.) "
                     "redacted before any downstream analysis.")
    col2.metric("K-Anonymity Risk Reduction",
                f"{KANON_BASELINE_PCT_AT_RISK}% -> {KANON_MITIGATED_PCT_AT_RISK}%",
                help=f"Percentage of records at re-identification risk (k<5), "
                     f"before vs after mitigation ({KANON_MITIGATION_STRATEGY}).")

    breakdown = compute_entity_breakdown(df)
    if not breakdown.empty:
        fig = px.bar(breakdown, x="entity_type", y="count", color="entity_type",
                     title="Redacted Entities by Type")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Entities Redacted")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**K-Anonymity Audit Summary**")
    kanon_df = pd.DataFrame({
        "Metric": ["Uniquely identifiable (k=1)", "At-risk records (k<5)"],
        "Baseline": [f"{KANON_BASELINE_PCT_UNIQUE}%", f"{KANON_BASELINE_PCT_AT_RISK}%"],
        f"Mitigated ({KANON_MITIGATION_STRATEGY})": [
            f"{KANON_MITIGATED_PCT_UNIQUE}%", f"{KANON_MITIGATED_PCT_AT_RISK}%"
        ],
    })
    st.table(kanon_df)


def render_causal_panel(causal_pairs: list, graph) -> None:
    """Render the Root-Cause Insights panel."""
    st.subheader("Root-Cause Insights")

    if not causal_pairs:
        st.info("No causal extraction data found. Run src.causal.extract_causes first.")
        return

    st.caption(
        f"Based on a sample of {len(causal_pairs)} complaints analyzed via a "
        "locally-running LLM (no data sent to external services)."
    )

    summary = build_causal_summary(causal_pairs)
    if not summary.empty:
        fig = px.bar(summary, x="root_cause", y="count", title="Top Root Causes (sample analysis)")
        fig.update_layout(xaxis_title="", yaxis_title="Occurrences")
        st.plotly_chart(fig, use_container_width=True)

    if graph is not None:
        st.markdown(f"**Causal graph**: {graph.number_of_nodes()} nodes, "
                    f"{graph.number_of_edges()} edges (see project files for full graph export).")


def render_recommendations(df: pd.DataFrame) -> None:
    """Render the preventive measures / recommendations panel."""
    st.subheader("Preventive Measures")
    recommendations = compute_category_recommendations(df)
    if recommendations.empty:
        st.info("No category volume spikes detected in the current data.")
        return
    for _, row in recommendations.iterrows():
        st.warning(f"**{row['category']}** -- volume up {row['pct_change']}% "
                   f"({row['volume']} complaints this period)\n\n{row['recommendation']}")


def render_live_submission_panel() -> None:
    """Render the interactive 'Submit New Complaint' panel."""
    st.subheader("Submit a New Complaint")
    st.caption(
        "Paste a complaint below to see it processed live: PII redaction, "
        "a three-model classification comparison, and automatic "
        "disagreement detection -- all running locally."
    )

    complaint_text = st.text_area(
        "Complaint text:",
        height=140,
        placeholder="e.g. I was charged twice for my credit card bill and support won't respond...",
    )

    if st.button("Process Complaint", type="primary"):
        if not complaint_text.strip():
            st.warning("Please enter some complaint text first.")
            return

        with st.spinner("Loading models (first run may take a minute)..."):
            processor = load_live_processor()

        with st.spinner("Processing complaint..."):
            result = processor.process(complaint_text)

        save_live_submission(result)

        st.success(f"Complaint ID: **{result['complaint_id']}** Processed.")

        st.subheader("Redacted text:")
        st.info(result["redacted_text"])

        st.divider()

        st.subheader("AI Summary:")
        st.info(result["summary"])

        st.divider()

        if result["entities_redacted"]:
            st.subheader(f"**{len(result['entities_redacted'])} PII entities redacted:**")
            entity_summary = pd.DataFrame(result["entities_redacted"])[["entity_type", "text"]]
            entity_summary.columns = ["Entity Type", "Detected Text"]
            st.table(entity_summary)
        
        st.divider()

        st.markdown("**Model Comparison:**")
        comparison_rows = []
        for model_name, pred in result["model_comparison"].items():
            comparison_rows.append({
                "Model": model_name.replace("_", " ").title(),
                "Predicted Category": pred["category"],
                "Confidence": f"{pred['confidence']:.2%}",
            })
        st.table(pd.DataFrame(comparison_rows))

        agreement = result["agreement"]
        if agreement["needs_review"]:
            st.warning(f"⚠️ **Flagged for human review**: {agreement['review_reason']}")
        else:
            st.success(f"✅ Unanimous model agreement (avg confidence: {agreement['average_confidence']:.2%})")

        st.divider()

        st.subheader("**Final Classification (Hierarchical):**")
        col1, col2 = st.columns(2)
        col1.metric("Domain", result["final_classification"]["domain"])
        col2.metric("Sub-Issue", result["final_classification"]["sub_issue"] or "N/A")

def render_review_queue_panel() -> None:
    """Render the panel listing complaints flagged for human review."""
    st.subheader("Complaints Needing Review")

    if not LIVE_SUBMISSIONS_PATH.exists():
        st.info("No live submissions yet.")
        return

    live_df = pd.read_csv(LIVE_SUBMISSIONS_PATH)

    if RESOLVED_COLUMN not in live_df.columns:
        live_df[RESOLVED_COLUMN] = False

    needs_review_mask = (live_df["needs_review"] == True) & (live_df[RESOLVED_COLUMN] != True)
    flagged = live_df[needs_review_mask]

    if flagged.empty:
        st.success("No complaints currently need review.")
        return

    st.warning(f"{len(flagged)} complaint(s) flagged for review.")

    for idx, row in flagged.iterrows():
        with st.expander(f"{row['complaint_id']} — {row['review_reason']}"):
            st.write("**Redacted text:**", row["redacted_text"])
            st.write("**TF-IDF prediction:**", row.get("tfidf_prediction"))
            st.write("**Sentence-BERT prediction:**", row.get("sbert_prediction"))
            st.write("**DistilBERT prediction:**", row.get("distilbert_prediction"))
            st.write("**Current category:**", row["predicted_category"])

            if st.button("Mark as Resolved", key=f"resolve_{row['complaint_id']}"):
                live_df.loc[live_df["complaint_id"] == row["complaint_id"], RESOLVED_COLUMN] = True
                live_df.to_csv(LIVE_SUBMISSIONS_PATH, index=False)
                st.rerun()



# ---------------------------------------------------------------------------
# App entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    """Configure and render the full Streamlit dashboard."""
    st.set_page_config(page_title="Complaint Intelligence Dashboard", layout="wide")
    st.title("PII Redact Complaint Intelligence Dashboard")
    st.caption("All insights below are generated from complaints after PII redaction.")

    df = load_merged_results()
    causal_pairs = load_causal_pairs()
    graph = load_causal_graph()

    render_live_submission_panel()
    st.divider()
    render_overview(df)
    st.divider()
    render_review_queue_panel()
    st.divider()
    render_category_insights(df)
    st.divider()
    render_privacy_panel(df)
    st.divider()
    render_causal_panel(causal_pairs, graph)
    st.divider()
    render_recommendations(df)


if __name__ == "__main__":
    main()

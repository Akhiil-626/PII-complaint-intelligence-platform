"""FastAPI backend for the Complaint Intelligence Platform.

Serves the batch results, live submissions, privacy metrics and causal
analysis as JSON for the React dashboard, and exposes the live
processing pipeline. Models are loaded once at startup.

Run from the project root:
    uvicorn api.main:app --port 8000
"""

from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

import networkx as nx
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.classification.live_predict import LiveComplaintProcessor

RESULTS_PATH = Path("data/processed/pipeline_results.csv")
LIVE_PATH = Path("data/processed/live_submissions.csv")
CAUSAL_PAIRS_PATH = Path("data/processed/causal_pairs.json")
CAUSAL_GRAPH_PATH = Path("models/saved/causal_graph.gexf")

ENTITY_TYPES = (
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ACCOUNT_NUMBER",
    "AADHAAR_NUMBER", "COMPLAINT_ID", "CREDIT_CARD", "CREDENTIAL",
)

SPIKE_THRESHOLD = 0.30
RECOMMENDATION_RULES = {
    "Debt collection": "Review collection call scripts and staff training.",
    "Credit reporting": "Review recent changes to reporting/verification procedures.",
    "Credit/Prepaid card": "Check for card-related outages or fee changes.",
    "Bank account/service": "Investigate recent account-term or mobile banking changes.",
    "Mortgage": "Review recent servicing transfers or rate-adjustment communications.",
    "Student loan": "Check for servicer changes or repayment-plan communication issues.",
    "Personal/Payday loan": "Review recent loan-term or collection-practice changes.",
    "Money transfer": "Check for outages or delays in transfer processing.",
    "Vehicle loan or lease": "Review recent payment-processing or collection changes.",
}
DEFAULT_RECOMMENDATION = "Volume increase detected; review recent process or system changes."

# Confirmed k-anonymity audit results (printed by src/privacy/ scripts).
KANON = {
    "strategy": "quarter_binning + drop_subproduct",
    "baseline": {"pct_unique": 47.38, "pct_at_risk": 82.02},
    "mitigated": {"pct_unique": 12.95, "pct_at_risk": 44.73},
}

state: Dict[str, Any] = {}


def _load_models_worker() -> None:
    print("Loading models (30-60s)...")
    proc = LiveComplaintProcessor()
    proc.process("warm up complaint text")
    state["processor"] = proc
    print("Models ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the heavy models once at server startup in a background thread."""
    thread = threading.Thread(target=_load_models_worker, daemon=True)
    thread.start()
    yield
    state.clear()


app = FastAPI(title="Complaint Intelligence API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComplaintRequest(BaseModel):
    """Request body for submitting a new complaint."""

    text: str


# ---------------------------------------------------------------- helpers

def to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert a DataFrame to JSON-safe records (NaN -> None)."""
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


def as_bool(series: pd.Series) -> pd.Series:
    """Robustly interpret a CSV column as booleans."""
    return series.astype(str).str.strip().str.lower() == "true"


def load_batch() -> pd.DataFrame:
    """Load batch pipeline results with parsed dates and entity columns."""
    if not RESULTS_PATH.exists():
        raise HTTPException(500, f"Missing {RESULTS_PATH}")
    df = pd.read_csv(RESULTS_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for e in ENTITY_TYPES:
        if e not in df.columns:
            df[e] = 0
    return df


def load_live() -> pd.DataFrame:
    """Load live submissions (empty DataFrame if none yet)."""
    if not LIVE_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(LIVE_PATH)
    for col, default in (("needs_review", False), ("resolved", False), ("summary", None)):
        if col not in df.columns:
            df[col] = default
    for e in ENTITY_TYPES:
        df[e] = df[e].fillna(0) if e in df.columns else 0
    return df


def load_merged() -> pd.DataFrame:
    """Merge batch and live data into one schema for analytics endpoints."""
    cols = ["date", "predicted_category", "predicted_sub_issue", "domain_confidence", *ENTITY_TYPES]
    merged = load_batch()[cols].copy()
    live = load_live()
    if not live.empty:
        part = pd.DataFrame({
            "date": pd.to_datetime(live["timestamp"], errors="coerce"),
            "predicted_category": live["predicted_category"],
            "predicted_sub_issue": live["predicted_sub_issue"],
            "domain_confidence": live["domain_confidence"],
        })
        for e in ENTITY_TYPES:
            part[e] = live[e]
        merged = pd.concat([merged, part], ignore_index=True)
    return merged


def clean_cause(value: Any) -> Any:
    """Treat None / 'null' / blank cause values as missing."""
    if value is None:
        return None
    s = str(value).strip()
    return None if s == "" or s.lower() == "null" else s


def save_submission(result: Dict[str, Any]) -> None:
    """Append a processed live complaint to the persistent log."""
    counts = {e: 0 for e in ENTITY_TYPES}
    for ent in result["entities_redacted"]:
        if ent.get("entity_type") in counts:
            counts[ent["entity_type"]] += 1
    row = {
        "complaint_id": result["complaint_id"],
        "timestamp": result["timestamp"],
        "redacted_text": result["redacted_text"],
        "summary": result.get("summary"),
        "predicted_category": result["final_classification"]["domain"],
        "predicted_sub_issue": result["final_classification"]["sub_issue"],
        "domain_confidence": result["final_classification"]["domain_confidence"],
        "tfidf_prediction": result["model_comparison"]["tfidf_svm"]["category"],
        "sbert_prediction": result["model_comparison"]["sentence_bert_logreg"]["category"],
        "distilbert_prediction": result["model_comparison"]["distilbert"]["category"],
        "needs_review": result["agreement"]["needs_review"],
        "review_reason": result["agreement"]["review_reason"],
        "num_entities_redacted": len(result["entities_redacted"]),
        "resolved": False,
        **counts,
    }
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    if LIVE_PATH.exists():
        new = pd.concat([pd.read_csv(LIVE_PATH), new], ignore_index=True)
    new.to_csv(LIVE_PATH, index=False)


# -------------------------------------------------------------- endpoints

@app.get("/api/health")
def health() -> Dict[str, Any]:
    """Report whether the models are loaded."""
    return {"status": "ok", "models_loaded": "processor" in state}


@app.get("/api/overview")
def overview() -> Dict[str, Any]:
    """Headline stats across batch + live data."""
    df = load_merged()
    live = load_live()
    pending = 0
    if not live.empty:
        pending = int((as_bool(live["needs_review"]) & ~as_bool(live["resolved"])).sum())
    return {
        "total_complaints": int(len(df)),
        "total_categories": int(df["predicted_category"].nunique()),
        "total_pii_redacted": int(df[list(ENTITY_TYPES)].sum().sum()),
        "live_submissions": int(len(live)),
        "pending_review": pending,
    }


@app.get("/api/categories")
def categories() -> List[Dict[str, Any]]:
    """Complaint volume per category."""
    counts = load_merged()["predicted_category"].value_counts()
    return [{"category": k, "count": int(v)} for k, v in counts.items()]


@app.get("/api/sub-issues")
def sub_issues(category: str) -> List[Dict[str, Any]]:
    """Sub-issue breakdown for one category (query param: names contain '/')."""
    df = load_merged()
    sub = df[df["predicted_category"] == category]["predicted_sub_issue"].dropna().value_counts()
    return [{"sub_issue": k, "count": int(v)} for k, v in sub.items()]


@app.get("/api/trend")
def trend() -> List[Dict[str, Any]]:
    """Monthly complaint counts per category."""
    df = load_merged().dropna(subset=["date"]).copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    out = df.groupby(["month", "predicted_category"]).size().reset_index(name="count")
    out = out.rename(columns={"predicted_category": "category"})
    return to_records(out.sort_values("month"))


@app.get("/api/privacy")
def privacy() -> Dict[str, Any]:
    """Redaction breakdown plus k-anonymity audit results."""
    df = load_merged()
    totals = df[list(ENTITY_TYPES)].sum()
    breakdown = [{"entity_type": k, "count": int(v)} for k, v in totals.items()]
    return {
        "total_redacted": int(totals.sum()),
        "breakdown": sorted(breakdown, key=lambda x: x["count"], reverse=True),
        "k_anonymity": KANON,
    }


@app.get("/api/recommendations")
def recommendations() -> List[Dict[str, Any]]:
    """Categories whose latest-month volume spiked vs their history."""
    df = load_merged().dropna(subset=["date"]).copy()
    if df.empty:
        return []
    df["period"] = df["date"].dt.to_period("M")
    latest = df["period"].max()
    counts = df.groupby(["predicted_category", "period"]).size().reset_index(name="count")
    out = []
    for cat, g in counts.groupby("predicted_category"):
        if len(g) < 2:
            continue
        cur = g.loc[g["period"] == latest, "count"]
        hist = g.loc[g["period"] != latest, "count"].mean()
        if cur.empty or hist == 0:
            continue
        change = (cur.iloc[0] - hist) / hist
        if change >= SPIKE_THRESHOLD:
            out.append({
                "category": cat,
                "volume": int(cur.iloc[0]),
                "pct_change": round(float(change) * 100, 1),
                "recommendation": RECOMMENDATION_RULES.get(cat, DEFAULT_RECOMMENDATION),
            })
    return out


@app.get("/api/causal/root-causes")
def root_causes() -> List[Dict[str, Any]]:
    """Top root causes from the saved causal graph."""
    if not CAUSAL_GRAPH_PATH.exists():
        return []
    g = nx.read_gexf(CAUSAL_GRAPH_PATH)
    scores = {}
    for n, d in g.nodes(data=True):
        if d.get("node_type") == "root_cause":
            weight = sum(edge_data.get("weight", 1.0) for _, _, edge_data in g.out_edges(n, data=True))
            scores[str(n)] = int(weight)
    top10 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"root_cause": k, "count": v} for k, v in top10]


@app.get("/api/causal/graph")
def causal_graph() -> Dict[str, Any]:
    """Nodes and edges of the saved causal graph."""
    if not CAUSAL_GRAPH_PATH.exists():
        return {"nodes": [], "edges": []}
    g = nx.read_gexf(CAUSAL_GRAPH_PATH)
    return {
        "nodes": [{"id": n, "type": d.get("node_type")} for n, d in g.nodes(data=True)],
        "edges": [
            {"source": u, "target": v, "weight": d.get("weight", 1)}
            for u, v, d in g.edges(data=True)
        ],
    }


@app.get("/api/submissions")
def submissions(limit: int = 20) -> List[Dict[str, Any]]:
    """Most recent live submissions (redacted text only)."""
    live = load_live()
    if live.empty:
        return []
    return to_records(live.tail(limit).iloc[::-1])


@app.post("/api/complaints")
def submit_complaint(req: ComplaintRequest) -> Dict[str, Any]:
    """Run a new complaint through the full pipeline and log it.

    Declared as a plain `def` so FastAPI runs it in a worker thread; the
    pipeline (especially the local LLM summary) is slow and blocking.
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Complaint text is empty.")
    if "processor" not in state:
        raise HTTPException(503, "Models are still loading.")
    result = state["processor"].process(text)
    save_submission(result)
    # Privacy-first: never send the raw, unredacted text back over the wire.
    result.pop("original_text", None)
    return result


@app.get("/api/review-queue")
def review_queue() -> List[Dict[str, Any]]:
    """Unresolved complaints flagged for human review."""
    live = load_live()
    if live.empty:
        return []
    mask = as_bool(live["needs_review"]) & ~as_bool(live["resolved"])
    return to_records(live[mask])


@app.post("/api/review-queue/{complaint_id}/resolve")
def resolve(complaint_id: str) -> Dict[str, str]:
    """Mark a flagged complaint as resolved."""
    live = load_live()
    if live.empty or complaint_id not in set(live["complaint_id"]):
        raise HTTPException(404, "Complaint not found.")
    live.loc[live["complaint_id"] == complaint_id, "resolved"] = True
    live.to_csv(LIVE_PATH, index=False)
    return {"status": "resolved", "complaint_id": complaint_id}

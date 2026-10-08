"""Routes for dashboard metrics, aggregated privacy stats, and visual insights."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter

from src.utils.config import (
    CAUSAL_PAIRS_PATH,
    ENTITY_TYPES,
    LIVE_SUBMISSIONS_PATH,
    PIPELINE_RESULTS_PATH,
)

router = APIRouter()

# Audited K-Anonymity metrics (from src.privacy.k_anonymity_mitigation)
KANON_AUDIT_DATA = {
    "baseline": {
        "strategy": "Product_clean, Sub-product, Issue, received_month",
        "unique_pct": 47.38,
        "at_risk_pct": 82.02,
        "mean_k": 3.03,
        "median_k": 2.0,
    },
    "mitigated": {
        "strategy": "quarter_binning + drop_subproduct",
        "unique_pct": 12.95,
        "at_risk_pct": 44.73,
        "mean_k": 8.44,
        "median_k": 5.0,
        "risk_reduction_points": 37.29,
    },
}


def _load_unified_data() -> pd.DataFrame:
    """Load combined batch and live submission data."""
    frames: List[pd.DataFrame] = []

    if PIPELINE_RESULTS_PATH.exists():
        batch_df = pd.read_csv(PIPELINE_RESULTS_PATH)
        frames.append(batch_df)

    if LIVE_SUBMISSIONS_PATH.exists():
        live_df = pd.read_csv(LIVE_SUBMISSIONS_PATH)
        frames.append(live_df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


@router.get("/dashboard-data")
def get_dashboard_data() -> Dict[str, Any]:
    """Return aggregated overview statistics, category distributions, and privacy metrics."""
    df = _load_unified_data()

    if df.empty:
        return {
            "total_complaints": 0,
            "total_categories": 0,
            "total_pii_redacted": 0,
            "pending_reviews": 0,
            "category_distribution": [],
            "entity_breakdown": [],
            "k_anonymity": KANON_AUDIT_DATA,
            "top_root_causes": [],
        }

    category_col = "predicted_category" if "predicted_category" in df.columns else "Product"
    total_complaints = len(df)
    total_categories = int(df[category_col].nunique()) if category_col in df.columns else 0

    # Count total redacted PII
    entity_cols = [c for c in ENTITY_TYPES if c in df.columns]
    total_pii_redacted = int(df[entity_cols].sum().sum()) if entity_cols else 0

    # Pending reviews count
    pending_reviews = 0
    if "needs_review" in df.columns:
        resolved_col = df["resolved"] if "resolved" in df.columns else False
        pending_reviews = int(((df["needs_review"] == True) & (resolved_col != True)).sum())

    # Category breakdown
    cat_counts = df[category_col].value_counts().head(10).to_dict() if category_col in df.columns else {}
    category_distribution = [{"category": k, "count": int(v)} for k, v in cat_counts.items()]

    # Entity breakdown
    entity_breakdown = []
    if entity_cols:
        totals = df[entity_cols].sum().sort_values(ascending=False)
        entity_breakdown = [{"entity_type": k, "count": int(v)} for k, v in totals.items()]

    # Root causes from causal pairs
    top_root_causes: List[Dict[str, Any]] = []
    if CAUSAL_PAIRS_PATH.exists():
        try:
            with open(CAUSAL_PAIRS_PATH, "r", encoding="utf-8") as f:
                pairs = json.load(f)
            causes = [
                p.get("root_cause")
                for p in pairs
                if p.get("root_cause") and str(p.get("root_cause")).lower() != "null"
            ]
            cause_series = pd.Series(causes).value_counts().head(5)
            top_root_causes = [{"cause": k, "count": int(v)} for k, v in cause_series.items()]
        except Exception:
            top_root_causes = []

    return {
        "total_complaints": total_complaints,
        "total_categories": total_categories,
        "total_pii_redacted": total_pii_redacted,
        "pending_reviews": pending_reviews,
        "category_distribution": category_distribution,
        "entity_breakdown": entity_breakdown,
        "k_anonymity": KANON_AUDIT_DATA,
        "top_root_causes": top_root_causes,
    }

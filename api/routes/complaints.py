"""Routes for complaint ingestion, processing, and review queue management."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.complaint_schema import ComplaintRequest, ComplaintResponse
from src.pipeline.full_pipeline import ComplaintPipeline
from src.utils.config import ENTITY_TYPES, LIVE_SUBMISSIONS_PATH

router = APIRouter()


def _save_submission_to_csv(result: Dict[str, Any], source: str = "api") -> None:
    """Save processed complaint record into the live submissions CSV log."""
    row = {
        "complaint_id": result["complaint_id"],
        "timestamp": result["timestamp"],
        "source": source,
        "redacted_text": result["redacted_text"],
        "predicted_category": result["final_classification"]["domain"],
        "predicted_sub_issue": result["final_classification"].get("sub_issue") or "",
        "domain_confidence": result["final_classification"].get("domain_confidence") or 0.0,
        "tfidf_prediction": result["model_comparison"]["tfidf_svm"]["category"],
        "sbert_prediction": result["model_comparison"]["sentence_bert_logreg"]["category"],
        "distilbert_prediction": result["model_comparison"]["distilbert"]["category"],
        "needs_review": result["agreement"]["needs_review"],
        "review_reason": result["agreement"].get("review_reason") or "",
        "sentiment": result["sentiment"]["sentiment"],
        "urgency_score": result["sentiment"]["urgency_score"],
        "num_entities_redacted": len(result["entities_redacted"]),
        "resolved": False,
    }

    # Track entity counts per schema type
    entity_counts = {etype: 0 for etype in ENTITY_TYPES}
    for entity in result["entities_redacted"]:
        etype = entity.get("entity_type")
        if etype in entity_counts:
            entity_counts[etype] += 1
    row.update(entity_counts)

    LIVE_SUBMISSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame([row])
    if LIVE_SUBMISSIONS_PATH.exists():
        existing_df = pd.read_csv(LIVE_SUBMISSIONS_PATH)
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        updated_df = new_df

    updated_df.to_csv(LIVE_SUBMISSIONS_PATH, index=False)


@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(request: ComplaintRequest) -> ComplaintResponse:
    """Process a raw complaint through the full privacy-preserving pipeline.
    
    Redacts all PII, compares 3 classification models, derives hierarchical
    sub-issues, scores sentiment/urgency, checks for near duplicates, and logs
    the complaint for review if models disagree.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Complaint text narrative cannot be empty.")

    pipeline = ComplaintPipeline.get_instance()
    result = pipeline.process_single(request.text)

    # Persist live submission
    try:
        _save_submission_to_csv(result, source=request.source or "api")
    except Exception as e:
        print(f"Warning: Failed to save submission to log: {e}")

    top_duplicate_score = None
    if result["duplicates"]:
        top_duplicate_score = result["duplicates"][0].get("similarity_score")

    return ComplaintResponse(
        complaint_id=result["complaint_id"],
        timestamp=result["timestamp"],
        redacted_text=result["redacted_text"],
        category=result["final_classification"]["domain"],
        sub_issue=result["final_classification"].get("sub_issue"),
        confidence=result["final_classification"].get("domain_confidence"),
        sentiment=result["sentiment"]["sentiment"],
        urgency_score=result["sentiment"]["urgency_score"],
        emotion=result["sentiment"]["emotion"],
        duplicate_score=top_duplicate_score,
        needs_review=result["agreement"]["needs_review"],
        review_reason=result["agreement"].get("review_reason"),
        entities_count=len(result["entities_redacted"]),
        entities=result["entities_redacted"],
    )


@router.get("/complaints/review-queue")
def get_review_queue() -> List[Dict[str, Any]]:
    """Retrieve all complaints currently flagged for human escalation."""
    if not LIVE_SUBMISSIONS_PATH.exists():
        return []

    df = pd.read_csv(LIVE_SUBMISSIONS_PATH)
    if "resolved" not in df.columns:
        df["resolved"] = False

    flagged = df[(df["needs_review"] == True) & (df["resolved"] != True)]
    return flagged.to_dict(orient="records")


@router.post("/complaints/{complaint_id}/resolve")
def resolve_complaint(complaint_id: str) -> Dict[str, Any]:
    """Mark a flagged complaint as resolved by human reviewer."""
    if not LIVE_SUBMISSIONS_PATH.exists():
        raise HTTPException(status_code=404, detail="Submissions repository not found.")

    df = pd.read_csv(LIVE_SUBMISSIONS_PATH)
    if "complaint_id" not in df.columns or complaint_id not in df["complaint_id"].values:
        raise HTTPException(status_code=404, detail=f"Complaint ID '{complaint_id}' not found.")

    df.loc[df["complaint_id"] == complaint_id, "resolved"] = True
    df.to_csv(LIVE_SUBMISSIONS_PATH, index=False)
    return {"status": "success", "complaint_id": complaint_id, "resolved": True}

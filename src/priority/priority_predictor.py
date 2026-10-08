"""Feature-based priority and severity prediction for operational complaint triage."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


CRITICAL_KEYWORDS = [
    "lawyer", "attorney", "lawsuit", "legal action", "ombudsman",
    "court", "eviction", "foreclosure", "harassment", "stolen identity",
    "fraud", "identity theft", "police report"
]

HIGH_SEVERITY_DOMAINS = {
    "Debt collection": 0.35,
    "Mortgage": 0.30,
    "Credit/Prepaid card": 0.25,
    "Money transfer": 0.25,
    "Credit reporting": 0.20,
    "Bank account/service": 0.20,
    "Personal/Payday loan": 0.25,
    "Student loan": 0.20,
    "Vehicle loan or lease": 0.20,
}


class PriorityPredictor:
    """Predicts complaint triage priority and severity score from text and metadata features."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.trained_model: Optional[Any] = None

    def evaluate_features(self, text: str, domain: Optional[str] = None, sentiment_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compute severity score and triage tier from text and metadata.
        
        Args:
            text: Complaint narrative text.
            domain: Predicted or true financial domain.
            sentiment_data: Precomputed sentiment output dict.
            
        Returns:
            Dictionary with severity_score (0.0 - 1.0) and priority_tier (CRITICAL, HIGH, MEDIUM, LOW).
        """
        score = 0.20
        text_lower = text.lower()

        # 1. Domain weight
        domain_weight = HIGH_SEVERITY_DOMAINS.get(domain or "", 0.15)
        score += domain_weight

        # 2. Critical keywords
        matched_kws = [kw for kw in CRITICAL_KEYWORDS if kw in text_lower]
        score += min(0.35, len(matched_kws) * 0.12)

        # 3. Sentiment factor
        if sentiment_data:
            compound = sentiment_data.get("compound", 0.0)
            if compound < -0.5:
                score += 0.25
            elif compound < -0.1:
                score += 0.15
            elif compound > 0.3:
                score -= 0.10

        severity_score = round(min(1.0, max(0.05, score)), 2)

        if severity_score >= 0.75:
            tier = "CRITICAL"
        elif severity_score >= 0.55:
            tier = "HIGH"
        elif severity_score >= 0.35:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        return {
            "severity_score": severity_score,
            "priority_tier": tier,
            "escalation_triggers": matched_kws,
        }

    def predict(self, feature_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict priority for a list of feature dictionaries."""
        results = []
        for row in feature_rows:
            text = row.get("text") or row.get("redacted_text") or ""
            domain = row.get("domain") or row.get("predicted_category") or ""
            sentiment = row.get("sentiment")
            res = self.evaluate_features(text, domain=domain, sentiment_data=sentiment)
            results.append(res)
        return results

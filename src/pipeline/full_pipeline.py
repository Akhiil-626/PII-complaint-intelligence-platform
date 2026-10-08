"""
Orchestrates the complete Privacy-Preserving Complaint Intelligence Pipeline.

Combines:
- PII detection and redaction (Presidio + custom recognizers)
- Multi-model category classification (TF-IDF, SBERT, DistilBERT)
- Multi-model agreement check and review flagging
- Hierarchical domain and sub-issue classification
- Sentiment, emotion, and urgency scoring
- Duplicate detection against indexed complaints
- Privacy-safe metadata synthesis
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.redaction.presidio_pipeline import PresidioRedactionPipeline
from src.classification.hierarchical_predict import HierarchicalClassifier
from src.sentiment.sentiment_emotion import SentimentEmotionAnalyzer
from src.duplicate_detection.semantic_similarity import DuplicateDetector
from src.utils.config import (
    DISTILBERT_DIR,
    DISTILBERT_LABELS,
    DISTILBERT_MAX_LENGTH,
    LIVE_MODEL_DIR,
    LOW_CONFIDENCE_THRESHOLD,
    SBERT_MODEL_NAME,
    OLLAMA_MODEL,
)


def generate_complaint_id() -> str:
    """Generate a unique complaint ID in CMP-YYYY-NNNNN format."""
    year = datetime.now().year
    short_uuid = uuid.uuid4().hex[:5].upper()
    return f"CMP-{year}-{short_uuid}"


class ComplaintPipeline:
    """Production orchestrator for the Privacy-Preserving Complaint Intelligence Platform."""

    _instance: Optional["ComplaintPipeline"] = None

    @classmethod
    def get_instance(cls) -> "ComplaintPipeline":
        """Get or create singleton pipeline instance to avoid model reload overhead."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        live_model_dir: Path = LIVE_MODEL_DIR,
        distilbert_dir: Path = DISTILBERT_DIR,
        load_distilbert: bool = True,
    ) -> None:
        """Initialize all pipeline modules.
        
        Args:
            live_model_dir: Directory containing saved TF-IDF and SBERT classifiers.
            distilbert_dir: Directory containing fine-tuned DistilBERT checkpoint.
            load_distilbert: Whether to load DistilBERT into memory.
        """
        self.live_model_dir = Path(live_model_dir)
        self.distilbert_dir = Path(distilbert_dir)

        # 1. Redaction Pipeline
        self.redactor = PresidioRedactionPipeline()

        # 2. Sentiment Analyzer
        self.sentiment_analyzer = SentimentEmotionAnalyzer()

        # 3. TF-IDF + LinearSVC
        tfidf_vec_path = self.live_model_dir / "tfidf_vectorizer.joblib"
        tfidf_clf_path = self.live_model_dir / "tfidf_svm_classifier.joblib"
        if tfidf_vec_path.exists() and tfidf_clf_path.exists():
            self.tfidf_vectorizer = joblib.load(tfidf_vec_path)
            self.tfidf_clf = joblib.load(tfidf_clf_path)
        else:
            self.tfidf_vectorizer = None
            self.tfidf_clf = None

        # 4. SBERT + LogReg
        sbert_clf_path = self.live_model_dir / "sbert_logreg_classifier.joblib"
        self.sbert_embedder = SentenceTransformer(SBERT_MODEL_NAME)
        if sbert_clf_path.exists():
            self.sbert_clf = joblib.load(sbert_clf_path)
        else:
            self.sbert_clf = None

        # 5. DistilBERT
        self.distilbert_model = None
        self.distilbert_tokenizer = None
        if load_distilbert and self.distilbert_dir.exists() and any(self.distilbert_dir.iterdir()):
            try:
                self.distilbert_tokenizer = AutoTokenizer.from_pretrained(str(self.distilbert_dir))
                self.distilbert_model = AutoModelForSequenceClassification.from_pretrained(str(self.distilbert_dir))
                self.distilbert_model.eval()
            except Exception as e:
                print(f"Warning: DistilBERT loading failed: {e}")

        # 6. Hierarchical Classifier
        try:
            self.hierarchical_clf = HierarchicalClassifier()
        except Exception:
            self.hierarchical_clf = None

        # 7. Duplicate Detector
        self.duplicate_detector = DuplicateDetector(embedder=self.sbert_embedder)

    def _predict_tfidf(self, text: str) -> Dict[str, Any]:
        if not self.tfidf_vectorizer or not self.tfidf_clf:
            return {"category": "Unknown", "confidence": 0.0}
        X = self.tfidf_vectorizer.transform([text])
        prediction = self.tfidf_clf.predict(X)[0]
        scores = self.tfidf_clf.decision_function(X)[0]
        exp_scores = torch.softmax(torch.tensor(scores), dim=0)
        class_idx = list(self.tfidf_clf.classes_).index(prediction)
        return {
            "category": str(prediction),
            "confidence": round(float(exp_scores[class_idx]), 4)
        }

    def _predict_sbert(self, text: str) -> Dict[str, Any]:
        if not self.sbert_clf:
            return {"category": "Unknown", "confidence": 0.0}
        emb = self.sbert_embedder.encode([text])
        prediction = self.sbert_clf.predict(emb)[0]
        probs = self.sbert_clf.predict_proba(emb)[0]
        class_idx = list(self.sbert_clf.classes_).index(prediction)
        return {
            "category": str(prediction),
            "confidence": round(float(probs[class_idx]), 4)
        }

    def _predict_distilbert(self, text: str) -> Dict[str, Any]:
        if not self.distilbert_model or not self.distilbert_tokenizer:
            return {"category": "Unknown", "confidence": 0.0}
        inputs = self.distilbert_tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=DISTILBERT_MAX_LENGTH,
            return_tensors="pt",
        )
        inputs.pop("token_type_ids", None)
        with torch.no_grad():
            outputs = self.distilbert_model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)[0]

        pred_idx = int(torch.argmax(probs).item())
        return {
            "category": DISTILBERT_LABELS[pred_idx],
            "confidence": round(float(probs[pred_idx]), 4)
        }

    def _assess_agreement(self, model_comparison: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        valid_models = {k: v for k, v in model_comparison.items() if v["category"] != "Unknown"}
        if not valid_models:
            return {
                "unanimous": False,
                "distinct_predictions": [],
                "average_confidence": 0.0,
                "needs_review": True,
                "review_reason": "No valid model predictions available.",
            }

        categories = [p["category"] for p in valid_models.values()]
        confidences = [p["confidence"] for p in valid_models.values()]
        distinct = list(dict.fromkeys(categories))
        unanimous = len(distinct) == 1
        avg_conf = round(sum(confidences) / len(confidences), 4)

        if not unanimous:
            needs_review = True
            review_reason = f"Models disagree: split across {', '.join(distinct)}."
        elif avg_conf < LOW_CONFIDENCE_THRESHOLD:
            needs_review = True
            review_reason = f"Models agree on '{distinct[0]}' but confidence is low ({avg_conf})."
        else:
            needs_review = False
            review_reason = None

        return {
            "unanimous": unanimous,
            "distinct_predictions": distinct,
            "average_confidence": avg_conf,
            "needs_review": needs_review,
            "review_reason": review_reason,
        }

    def process_single(
        self,
        raw_text: str,
        include_summary: bool = False,
        complaint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the end-to-end complaint intelligence pipeline on a single complaint narrative.
        
        Args:
            raw_text: Raw complaint text.
            include_summary: Whether to attempt Ollama LLM summary generation.
            complaint_id: Optional custom complaint ID.
            
        Returns:
            Dictionary containing redacted text, entities, model comparison,
            agreement, hierarchical classification, sentiment, duplicates, and metadata.
        """
        cid = complaint_id or generate_complaint_id()

        # Step 1: PII Redaction
        redaction_res = self.redactor.redact_with_metadata(raw_text)
        redacted_text = redaction_res["redacted_text"]

        # Step 2: 3-way Model Comparison on Redacted Text
        tfidf_res = self._predict_tfidf(redacted_text)
        sbert_res = self._predict_sbert(redacted_text)
        distilbert_res = self._predict_distilbert(redacted_text)

        model_comparison = {
            "tfidf_svm": tfidf_res,
            "sentence_bert_logreg": sbert_res,
            "distilbert": distilbert_res,
        }

        # Step 3: Agreement Assessment
        agreement = self._assess_agreement(model_comparison)

        # Step 4: Hierarchical Domain + Sub-Issue
        if self.hierarchical_clf:
            hier_res = self.hierarchical_clf.predict(redacted_text)
        else:
            hier_res = {
                "domain": tfidf_res["category"],
                "sub_issue": None,
                "domain_confidence": tfidf_res["confidence"],
                "sub_issue_confidence": None,
            }

        # Step 5: Sentiment & Urgency
        sentiment_res = self.sentiment_analyzer.analyze_single(redacted_text)

        # Step 6: Duplicate Check
        duplicates = self.duplicate_detector.find_duplicates(redacted_text, top_k=3)

        # Step 7: Optional LLM Summary
        summary = None
        if include_summary:
            try:
                import ollama
                prompt = (
                    f"Complaint ID: {cid}\n"
                    f"Category: {hier_res['domain']}\n"
                    f"Sub-issue: {hier_res.get('sub_issue')}\n"
                    f"Text: {redacted_text}\n\n"
                    "Provide a 2-sentence summary of the customer's core grievance."
                )
                resp = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                )
                summary = resp["message"]["content"].strip()
            except Exception:
                summary = "Summary generation unavailable (Ollama offline)."

        return {
            "complaint_id": cid,
            "timestamp": datetime.now().isoformat(),
            "original_text": raw_text,
            "redacted_text": redacted_text,
            "entities_redacted": redaction_res["entities"],
            "model_comparison": model_comparison,
            "agreement": agreement,
            "final_classification": {
                "domain": hier_res["domain"],
                "sub_issue": hier_res.get("sub_issue"),
                "domain_confidence": hier_res.get("domain_confidence"),
                "sub_issue_confidence": hier_res.get("sub_issue_confidence"),
            },
            "sentiment": sentiment_res,
            "duplicates": duplicates,
            "summary": summary,
        }

    def process_batch(self, texts: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Run the end-to-end pipeline across a collection of complaints."""
        return [self.process_single(t, **kwargs) for t in texts]


def run_full_pipeline(texts: list[str], **kwargs: Any) -> list[dict[str, Any]]:
    """Run the end-to-end complaint processing workflow."""
    pipeline = ComplaintPipeline.get_instance()
    return pipeline.process_batch(texts, **kwargs)

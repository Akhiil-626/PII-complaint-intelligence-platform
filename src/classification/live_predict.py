"""
Live prediction module: takes a brand-new, raw complaint as input and
processes it through the full pipeline -- PII redaction, three-way
classifier comparison (TF-IDF+SVM, Sentence-BERT+LogReg, fine-tuned
DistilBERT), hierarchical domain/sub-issue classification, and complaint
ID generation.

This is the module that turns the project from a historical-data
analysis tool into an actual live-processing system: any new complaint
text can be submitted and receives a full analysis in real time.

Usage
-----
    python -m src.classification.live_predict
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import joblib
import ollama
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.redaction.presidio_pipeline import PresidioRedactionPipeline
from src.classification.hierarchical_predict import HierarchicalClassifier

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LIVE_MODEL_DIR = Path("models/saved/live_classifiers")
DISTILBERT_DIR = Path("models/saved/domain_classifier_distilbert")
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

# DistilBERT was trained with sklearn's LabelEncoder on this sorted
# category list (LabelEncoder sorts labels alphabetically internally).
# Its output logits' index order corresponds exactly to this list.
DISTILBERT_LABELS = sorted([
    "Bank account/service", "Credit reporting", "Credit/Prepaid card",
    "Debt collection", "Money transfer", "Mortgage",
    "Personal/Payday loan", "Student loan", "Vehicle loan or lease",
])

DISTILBERT_MAX_LENGTH = 256
LOW_CONFIDENCE_THRESHOLD = 0.4

OLLAMA_MODEL = "llama3.1:8b"

SUMMARY_PROMPT_TEMPLATE = """Analyze the following customer complaint and generate a detailed complaint report.

Complaint ID: {complaint_id}
Category: {category}
Sub-Issue Category: {sub_issue}
Complaint Text:
{complaint_text}

Return the response in exactly this format:

Complaint ID: <complaint ID>

What the complaint is about:
<Explain clearly what the customer's complaint is about in 2-3 sentences.>

Main Category:
<State the main complaint category.>

Sub-Issue Category:
<State the specific sub-issue or problem within the main category.>

Detailed Summary:
<Provide a detailed summary of what happened, the customer's problem, important details, and what the customer wants resolved. Use 3-5 sentences.>

Important instructions:
- Use only information provided in the complaint and classification results.
- Do not invent facts, names, amounts, dates, or events.
- Keep the summary clear and professional.
- Do not include any PII that was removed during redaction.
- Respond only with the requested report. No additional introduction or conclusion.
"""


# ---------------------------------------------------------------------------
# Complaint ID generation
# ---------------------------------------------------------------------------

def generate_complaint_id() -> str:
    """Generate a unique complaint ID in the format CMP-YYYY-NNNNN.
    """
    year = datetime.now().year
    short_uuid = uuid.uuid4().hex[:5].upper()
    return f"CMP-{year}-{short_uuid}"


# ---------------------------------------------------------------------------
# Live predictor
# ---------------------------------------------------------------------------

class LiveComplaintProcessor:
    """Loads all saved models once and runs full-pipeline inference on new text."""

    def __init__(
        self,
        live_model_dir: Path = LIVE_MODEL_DIR,
        distilbert_dir: Path = DISTILBERT_DIR,
    ) -> None:
        """Load the redaction pipeline, all three classifiers, and the
        hierarchical classifier into memory.

        Args:
            live_model_dir: Directory containing the saved TF-IDF and
                Sentence-BERT classifier joblib files.
            distilbert_dir: Directory containing the saved fine-tuned
                DistilBERT model and tokenizer.

        Raises:
            FileNotFoundError: If any required saved model file is missing.
        """
        tfidf_vectorizer_path = live_model_dir / "tfidf_vectorizer.joblib"
        tfidf_clf_path = live_model_dir / "tfidf_svm_classifier.joblib"
        sbert_clf_path = live_model_dir / "sbert_logreg_classifier.joblib"

        for path in [tfidf_vectorizer_path, tfidf_clf_path, sbert_clf_path]:
            if not path.exists():
                raise FileNotFoundError(
                    f"Required model file not found: {path}. "
                    "Run src.classification.train_and_save_models first."
                )

        if not distilbert_dir.exists() or not any(distilbert_dir.iterdir()):
            raise FileNotFoundError(
                f"DistilBERT model not found at: {distilbert_dir}. "
                "Run src.classification.distilbert_finetune first."
            )

        print("Loading redaction pipeline...")
        self.redactor = PresidioRedactionPipeline()

        print("Loading TF-IDF + SVM...")
        self.tfidf_vectorizer = joblib.load(tfidf_vectorizer_path)
        self.tfidf_clf = joblib.load(tfidf_clf_path)

        print("Loading Sentence-BERT + Logistic Regression...")
        self.sbert_embedder = SentenceTransformer(SBERT_MODEL_NAME)
        self.sbert_clf = joblib.load(sbert_clf_path)

        print("Loading fine-tuned DistilBERT...")
        self.distilbert_tokenizer = AutoTokenizer.from_pretrained(
            str(distilbert_dir)
        )
        self.distilbert_model = AutoModelForSequenceClassification.from_pretrained(
            str(distilbert_dir)
        )
        self.distilbert_model.eval()

        print("Loading hierarchical classifier...")
        self.hierarchical_clf = HierarchicalClassifier()

        print("All models loaded.\n")

    def _predict_tfidf_svm(self, redacted_text: str) -> Dict[str, Any]:
        """Predict category using the TF-IDF + Linear SVM model.

        Args:
            redacted_text: The PII-redacted complaint text.

        Returns:
            A dict with "category" and "confidence" (decision-function
            based proxy, since LinearSVC lacks predict_proba by default).
        """
        X = self.tfidf_vectorizer.transform([redacted_text])
        prediction = self.tfidf_clf.predict(X)[0]

        scores = self.tfidf_clf.decision_function(X)[0]
        exp_scores = torch.softmax(torch.tensor(scores), dim=0)

        class_idx = list(self.tfidf_clf.classes_).index(prediction)
        confidence = float(exp_scores[class_idx])

        return {
            "category": prediction,
            "confidence": round(confidence, 4)
        }

    def _predict_sbert_logreg(self, redacted_text: str) -> Dict[str, Any]:
        """Predict category using the Sentence-BERT + Logistic Regression model.

        Args:
            redacted_text: The PII-redacted complaint text.

        Returns:
            A dict with "category" and "confidence" (true predict_proba,
            since LogisticRegression supports it natively).
        """
        embedding = self.sbert_embedder.encode([redacted_text])
        prediction = self.sbert_clf.predict(embedding)[0]

        probabilities = self.sbert_clf.predict_proba(embedding)[0]
        class_idx = list(self.sbert_clf.classes_).index(prediction)
        confidence = float(probabilities[class_idx])

        return {
            "category": prediction,
            "confidence": round(confidence, 4)
        }

    def _predict_distilbert(self, redacted_text: str) -> Dict[str, Any]:
        """Predict category using the fine-tuned DistilBERT model.

        Args:
            redacted_text: The PII-redacted complaint text.

        Returns:
            A dict with "category" and "confidence" (softmax probability
            of the predicted class).
        """
        inputs = self.distilbert_tokenizer(
            redacted_text,
            padding="max_length",
            truncation=True,
            max_length=DISTILBERT_MAX_LENGTH,
            return_tensors="pt",
        )

        # DistilBERT has no segment embeddings, so its forward() does not
        # accept `token_type_ids`. Newer tokenizers may still return this key
        # for BERT-family models; remove it to prevent a TypeError.
        inputs.pop("token_type_ids", None)

        with torch.no_grad():
            outputs = self.distilbert_model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)[0]

        predicted_idx = int(torch.argmax(probabilities).item())
        confidence = float(probabilities[predicted_idx])
        category = DISTILBERT_LABELS[predicted_idx]

        return {
            "category": category,
            "confidence": round(confidence, 4)
        }

    def _generate_summary(self, redacted_text, complaint_id, category, sub_issue):
        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            complaint_id=complaint_id,
            category=category,
            sub_issue=sub_issue,
            complaint_text=redacted_text
        )

        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )

            return response["message"]["content"].strip()

        except Exception as e:
            print(f"Warning: Ollama summary generation failed: {e}")
            return "Summary generation unavailable."

    def _assess_agreement(self, model_comparison: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess whether the three classifiers agree on this complaint.

        Flags a complaint for human review if the models predict different
        categories (disagreement), or if all three models agree but with
        low average confidence (collective uncertainty).

        Args:
            model_comparison: The dict of per-model prediction results
                (as returned by the three _predict_* methods), keyed by
                model name.

        Returns:
            A dict with:
                "unanimous": bool -- whether all three models predicted
                    the same category
                "distinct_predictions": list of the unique categories
                    predicted across all three models
                "average_confidence": float -- mean confidence across the
                    three models
                "needs_review": bool -- True if not unanimous, OR if
                    unanimous but average_confidence is below
                    LOW_CONFIDENCE_THRESHOLD
                "review_reason": str | None -- human-readable explanation
                    of why review is needed, or None if not needed
        """
        categories = [pred["category"] for pred in model_comparison.values()]
        confidences = [pred["confidence"] for pred in model_comparison.values()]

        distinct_predictions = list(dict.fromkeys(categories))
        unanimous = len(distinct_predictions) == 1
        average_confidence = round(sum(confidences) / len(confidences), 4)

        if not unanimous:
            needs_review = True
            review_reason = (
                f"Models disagree: predictions split across "
                f"{', '.join(distinct_predictions)}."
            )
        elif average_confidence < LOW_CONFIDENCE_THRESHOLD:
            needs_review = True
            review_reason = (
                f"All models agree on '{distinct_predictions[0]}' but with "
                f"low average confidence ({average_confidence})."
            )
        else:
            needs_review = False
            review_reason = None

        return {
            "unanimous": unanimous,
            "distinct_predictions": distinct_predictions,
            "average_confidence": average_confidence,
            "needs_review": needs_review,
            "review_reason": review_reason,
        }

    def process(self, raw_text: str) -> Dict[str, Any]:
        """Run the full live pipeline on a new, raw complaint.

        Steps: redact PII, run all three classifiers for comparison, run
        the hierarchical classifier for the official domain/sub-issue
        result, and generate a unique complaint ID.

        Args:
            raw_text: The raw, unredacted complaint text as submitted.

        Returns:
            A dict containing the complaint ID, redaction results, all
            three model predictions, and the final hierarchical
            domain/sub-issue result.
        """
        complaint_id = generate_complaint_id()

        redaction_result = self.redactor.redact_with_metadata(raw_text)
        redacted_text = redaction_result["redacted_text"]

        tfidf_result = self._predict_tfidf_svm(redacted_text)
        sbert_result = self._predict_sbert_logreg(redacted_text)
        distilbert_result = self._predict_distilbert(redacted_text)

        agreement = self._assess_agreement({
            "tfidf_svm": tfidf_result,
            "sentence_bert_logreg": sbert_result,
            "distilbert": distilbert_result,
        })

        hierarchical_result = self.hierarchical_clf.predict(redacted_text)

        summary = self._generate_summary(
            redacted_text,
            complaint_id,
            hierarchical_result["domain"],
            hierarchical_result["sub_issue"]
        )

        return {
            "complaint_id": complaint_id,
            "timestamp": datetime.now().isoformat(),
            "original_text": raw_text,
            "redacted_text": redacted_text,
            "summary": summary,
            "entities_redacted": redaction_result["entities"],
            "model_comparison": {
                "tfidf_svm": tfidf_result,
                "sentence_bert_logreg": sbert_result,
                "distilbert": distilbert_result,
            },
            "agreement": agreement,
            "final_classification": {
                "domain": hierarchical_result["domain"],
                "sub_issue": hierarchical_result["sub_issue"],
                "domain_confidence": hierarchical_result["domain_confidence"],
                "sub_issue_confidence": hierarchical_result["sub_issue_confidence"],
            },
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Demonstrate live processing on a few example complaints."""
    processor = LiveComplaintProcessor()

    examples = [
        "My name is John Smith and I was charged twice for my credit card bill this month. Please call me at 555-123-4567.",
        "A debt collector keeps calling my workplace even after I told them not to. This is harassment.",
        "I tried to transfer $500 to my friend but it never arrived, and my bank account was still debited.",
    ]

    for i, text in enumerate(examples, start=1):
        print(f"\n{'=' * 60}")
        print(f"EXAMPLE {i}")
        print("=" * 60)

        result = processor.process(text)

        print(f"Complaint ID: {result['complaint_id']}")
        print(f"Redacted text: {result['redacted_text']}")
        print(f"Summary: {result['summary']}")

        print("\nModel comparison:")

        for model_name, pred in result["model_comparison"].items():
            print(
                f"  {model_name:25s} -> "
                f"{pred['category']:25s} "
                f"(confidence: {pred['confidence']})"
            )

        agreement = result["agreement"]
        if agreement["needs_review"]:
            print(f"\n  [FLAGGED FOR REVIEW] {agreement['review_reason']}")
        else:
            print(f"\n  [OK] Unanimous agreement (avg confidence: {agreement['average_confidence']})")

        print("\nFinal classification:")
        print(f"  Domain: {result['final_classification']['domain']}")
        print(f"  Sub-issue: {result['final_classification']['sub_issue']}")


if __name__ == "__main__":
    main()
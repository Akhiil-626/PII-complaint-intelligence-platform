"""Unified prediction entrypoint for supported classification models."""

from __future__ import annotations

from typing import Any, List
from src.pipeline.full_pipeline import ComplaintPipeline


def predict(
    texts: List[str],
    model_type: str = "tfidf_svm",
    **kwargs: Any,
) -> List[str]:
    """Route predictions to the selected classification strategy.
    
    Args:
        texts: List of complaint texts to classify.
        model_type: One of 'tfidf_svm', 'sentence_bert', 'distilbert', 'hierarchical'.
        
    Returns:
        List of predicted domain category strings.
    """
    pipeline = ComplaintPipeline.get_instance()
    predictions: List[str] = []

    model_key = model_type.lower().replace("-", "_")

    for text in texts:
        if model_key in ["tfidf", "tfidf_svm"]:
            res = pipeline._predict_tfidf(text)
            predictions.append(res["category"])
        elif model_key in ["sbert", "sentence_bert", "sentence_bert_logreg"]:
            res = pipeline._predict_sbert(text)
            predictions.append(res["category"])
        elif model_key in ["distilbert", "transformer"]:
            res = pipeline._predict_distilbert(text)
            predictions.append(res["category"])
        elif model_key == "hierarchical":
            if pipeline.hierarchical_clf:
                res = pipeline.hierarchical_clf.predict(text)
                predictions.append(res["domain"])
            else:
                res = pipeline._predict_tfidf(text)
                predictions.append(res["category"])
        else:
            raise ValueError(f"Unsupported model_type: '{model_type}'. Choose from tfidf_svm, sentence_bert, distilbert, hierarchical.")

    return predictions

"""Tests for domain and hierarchical classification models."""

import pytest
from src.classification.predict import predict
from src.classification.hierarchical_predict import HierarchicalClassifier


def test_predict_tfidf_svm() -> None:
    texts = [
        "A debt collector repeatedly called my home threatening lawsuits.",
        "I was charged incorrect fees on my credit card statement.",
    ]
    predictions = predict(texts, model_type="tfidf_svm")
    assert len(predictions) == 2
    assert isinstance(predictions[0], str)
    assert predictions[0] == "Debt collection"


def test_predict_sentence_bert() -> None:
    texts = [
        "I tried to send money to a family member online but the funds vanished.",
    ]
    predictions = predict(texts, model_type="sentence_bert")
    assert len(predictions) == 1
    assert isinstance(predictions[0], str)
    assert predictions[0] in ["Money transfer", "Bank account/service"]


def test_hierarchical_predict() -> None:
    classifier = HierarchicalClassifier()
    res = classifier.predict("A debt collector keeps calling my office without permission.")

    assert "domain" in res
    assert "sub_issue" in res
    assert "domain_confidence" in res
    assert res["domain"] == "Debt collection"
    assert res["domain_confidence"] > 0.0

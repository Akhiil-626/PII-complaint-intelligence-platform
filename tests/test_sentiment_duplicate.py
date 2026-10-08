"""Tests for sentiment analysis, duplicate detection, and priority prediction."""

import pytest
from src.sentiment.sentiment_emotion import SentimentEmotionAnalyzer
from src.duplicate_detection.semantic_similarity import DuplicateDetector
from src.priority.priority_predictor import PriorityPredictor


def test_sentiment_emotion_analyzer() -> None:
    analyzer = SentimentEmotionAnalyzer()

    neg_text = "I am furious! My account was scammed and your representative lied to me. Harassment!"
    neg_res = analyzer.analyze_single(neg_text)
    assert neg_res["sentiment"] == "negative"
    assert neg_res["compound"] < -0.1
    assert neg_res["emotion"] in ["anger", "frustration"]
    assert neg_res["urgency_score"] >= 0.5

    pos_text = "Thank you so much! The problem was resolved quickly and customer service was great."
    pos_res = analyzer.analyze_single(pos_text)
    assert pos_res["sentiment"] == "positive"
    assert pos_res["compound"] > 0.1


def test_duplicate_detector() -> None:
    detector = DuplicateDetector()
    corpus = [
        "Unauthorized charges appeared on my credit card statement.",
        "Debt collector calls my cell phone repeatedly throughout the day.",
        "Unable to get an accurate credit score due to reporting errors.",
    ]
    detector.build_index(corpus)

    matches = detector.find_duplicates("I noticed unauthorized credit card fees on my monthly statement.")
    assert len(matches) > 0
    assert matches[0]["similarity_score"] >= 0.65
    assert "credit card" in matches[0]["text"].lower()


def test_priority_predictor() -> None:
    predictor = PriorityPredictor()

    critical_text = "A debt collector is threatening a lawsuit and eviction court summons!"
    res = predictor.evaluate_features(
        critical_text,
        domain="Debt collection",
        sentiment_data={"compound": -0.85},
    )
    assert res["priority_tier"] in ["CRITICAL", "HIGH"]
    assert res["severity_score"] >= 0.55
    assert len(res["escalation_triggers"]) > 0

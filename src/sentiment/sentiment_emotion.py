"""Wrappers for sentiment and emotion analysis on complaint narratives."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Keyword-based emotional cues common in consumer financial complaints
EMOTION_KEYWORDS = {
    "anger": [
        "angry", "furious", "outraged", "scam", "fraud", "stealing", "illegal",
        "harassment", "unacceptable", "ridiculous", "lies", "lied", "threatened"
    ],
    "frustration": [
        "frustrated", "tired", "waiting", "useless", "incompetent", "ignored",
        "unhelpful", "runaround", "no response", "still waiting", "never received",
        "waste of time", "hold for hours"
    ],
    "anxiety": [
        "worried", "scared", "stressed", "ruined", "credit ruined", "eviction",
        "bankruptcy", "fear", "nervous", "desperate", "destroying my life"
    ],
    "satisfaction": [
        "resolved", "helpful", "thank", "pleased", "great", "appreciated"
    ],
}


class SentimentEmotionAnalyzer:
    """Analyzes sentiment polarity, intensity, and complaint emotional tone."""

    def __init__(self, model_name: str = "vader") -> None:
        """Initialize the sentiment analyzer.
        
        Args:
            model_name: Identifier for the sentiment model. Defaults to 'vader'.
        """
        self.model_name = model_name
        self._vader = SentimentIntensityAnalyzer()

    def _detect_emotion(self, text: str, compound: float) -> str:
        """Infer dominant emotion based on sentiment score and vocabulary cues."""
        text_lower = text.lower()

        scores = {emotion: 0 for emotion in EMOTION_KEYWORDS}
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                    scores[emotion] += 1

        top_emotion, count = max(scores.items(), key=lambda x: x[1])
        if count > 0:
            return top_emotion

        if compound <= -0.5:
            return "anger"
        elif compound < -0.05:
            return "frustration"
        elif compound >= 0.05:
            return "satisfaction"
        else:
            return "neutral"

    def _derive_urgency(self, text: str, compound: float) -> float:
        """Compute an urgency factor in [0.0, 1.0] based on negativity and severity words."""
        urgency = 0.2
        if compound < -0.6:
            urgency += 0.4
        elif compound < -0.2:
            urgency += 0.2

        high_urgency_words = [
            "lawyer", "attorney", "legal action", "court", "ombudsman",
            "eviction", "foreclosure", "harassment", "fraud", "police",
            "identity theft", "immediate", "urgent"
        ]
        text_lower = text.lower()
        matches = sum(1 for w in high_urgency_words if w in text_lower)
        urgency += min(0.4, matches * 0.15)
        return round(min(1.0, urgency), 2)

    def analyze_single(self, text: str) -> Dict[str, Any]:
        """Analyze a single complaint text.
        
        Args:
            text: Complaint narrative string.
            
        Returns:
            Dictionary with sentiment polarity, label, emotion, and urgency score.
        """
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "compound": 0.0,
                "scores": {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0},
                "emotion": "neutral",
                "urgency_score": 0.1,
            }

        scores = self._vader.polarity_scores(text)
        compound = scores["compound"]

        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        emotion = self._detect_emotion(text, compound)
        urgency = self._derive_urgency(text, compound)

        return {
            "sentiment": label,
            "compound": round(compound, 4),
            "scores": scores,
            "emotion": emotion,
            "urgency_score": urgency,
        }

    def analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Return sentiment/emotion output for a list of texts.
        
        Args:
            texts: List of complaint narratives.
            
        Returns:
            List of result dictionaries.
        """
        return [self.analyze_single(t) for t in texts]

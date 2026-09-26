"""Wrappers for pretrained sentiment and emotion models."""

from __future__ import annotations

from typing import Any


class SentimentEmotionAnalyzer:
    """A simple wrapper for sentiment and emotion inference."""

    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment") -> None:
        self.model_name = model_name

    def analyze(self, texts: list[str]) -> list[dict[str, Any]]:
        """Return sentiment/emotion output for a list of texts."""
        raise NotImplementedError

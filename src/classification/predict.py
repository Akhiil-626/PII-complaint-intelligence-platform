"""Unified prediction entrypoint for supported classification models."""

from __future__ import annotations

from typing import Any


def predict(texts: list[str], model_type: str = "tfidf_svm", **kwargs: Any) -> list[str]:
    """Route predictions to the selected classification strategy."""
    raise NotImplementedError

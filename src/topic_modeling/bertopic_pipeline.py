"""BERTopic-based topic modeling wrapper."""

from __future__ import annotations

from typing import Any


class BerTopicPipeline:
    """A wrapper for topic modeling experiments on complaint text."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def fit(self, texts: list[str]) -> "BerTopicPipeline":
        """Train a BERTopic model on complaint texts."""
        raise NotImplementedError

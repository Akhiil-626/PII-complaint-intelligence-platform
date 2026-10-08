"""BERTopic-based topic modeling wrapper for discovering latent complaint themes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

from src.utils.config import SBERT_MODEL_NAME


class BerTopicPipeline:
    """Discovers unsupervised thematic clusters across complaint texts."""

    def __init__(
        self,
        embedding_model_name: str = SBERT_MODEL_NAME,
        min_topic_size: int = 10,
        nr_topics: Optional[int] = 10,
        **kwargs: Any,
    ) -> None:
        """Initialize the topic modeling pipeline.
        
        Args:
            embedding_model_name: Name of SentenceTransformer model.
            min_topic_size: Minimum number of documents to form a topic.
            nr_topics: Desired number of topics to reduce to.
        """
        self.embedding_model_name = embedding_model_name
        self.min_topic_size = min_topic_size
        self.nr_topics = nr_topics
        self.kwargs = kwargs

        self.embedder = SentenceTransformer(embedding_model_name)
        self.model: Optional[BERTopic] = None

    def fit(self, texts: List[str]) -> "BerTopicPipeline":
        """Train the BERTopic model on complaint narratives.
        
        Args:
            texts: List of complaint text strings.
            
        Returns:
            Self instance.
        """
        if len(texts) < self.min_topic_size:
            min_size = max(2, len(texts) // 2)
        else:
            min_size = self.min_topic_size

        self.model = BERTopic(
            embedding_model=self.embedder,
            min_topic_size=min_size,
            nr_topics=self.nr_topics,
            calculate_probabilities=False,
            verbose=False,
        )
        self.model.fit(texts)
        return self

    def transform(self, texts: List[str]) -> Tuple[List[int], List[float]]:
        """Predict topics for new texts.
        
        Args:
            texts: List of complaint texts.
            
        Returns:
            Tuple of (topics, probabilities).
        """
        if self.model is None:
            raise RuntimeError("BerTopicPipeline must be fit before calling transform.")
        topics, probs = self.model.transform(texts)
        return list(topics), list(probs) if probs is not None else [0.0] * len(topics)

    def get_topic_info(self) -> pd.DataFrame:
        """Return table of discovered topics with frequencies and top keywords."""
        if self.model is None:
            return pd.DataFrame()
        return self.model.get_topic_info()

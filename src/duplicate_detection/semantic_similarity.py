"""Semantic duplicate complaint detection using Sentence-BERT embeddings and FAISS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_SIMILARITY_THRESHOLD = 0.65


class DuplicateDetector:
    """Detects near-duplicate or semantically similar complaints."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        embedder: Optional[SentenceTransformer] = None,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> None:
        """Initialize the duplicate detector.
        
        Args:
            model_name: Sentence-Transformers model to use.
            embedder: Optional pre-loaded SentenceTransformer instance to avoid re-loading.
            similarity_threshold: Minimum cosine similarity [0.0 - 1.0] to consider a duplicate.
        """
        self.model_name = model_name
        self.embedder = embedder or SentenceTransformer(model_name)
        self.threshold = similarity_threshold
        self.indexed_texts: List[str] = []
        self.indexed_metadata: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.faiss_index: Optional[Any] = None

    def build_index(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 64,
    ) -> None:
        """Create a vector search index from complaint texts.
        
        Args:
            texts: List of complaint texts to index.
            metadata: Optional list of metadata dicts corresponding to texts.
            batch_size: Embedding batch size.
        """
        if not texts:
            self.indexed_texts = []
            self.indexed_metadata = []
            self.embeddings = None
            self.faiss_index = None
            return

        self.indexed_texts = list(texts)
        if metadata and len(metadata) == len(texts):
            self.indexed_metadata = list(metadata)
        else:
            self.indexed_metadata = [{"index": i} for i in range(len(texts))]

        # Generate normalized embeddings for cosine similarity
        raw_embeddings = self.embedder.encode(
            self.indexed_texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        self.embeddings = raw_embeddings

        if HAS_FAISS:
            dim = raw_embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(raw_embeddings)
            self.faiss_index = index

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two individual complaint texts.
        
        Args:
            text1: First complaint text.
            text2: Second complaint text.
            
        Returns:
            Cosine similarity score between -1.0 and 1.0.
        """
        emb = self.embedder.encode(
            [text1, text2],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        sim = float(np.dot(emb[0], emb[1]))
        return round(sim, 4)

    def find_duplicates(
        self,
        text: str,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Return likely duplicate or highly similar records for the given text.
        
        Args:
            text: Complaint text to query against index.
            top_k: Maximum number of matches to return.
            threshold: Minimum similarity threshold (overrides instance default if provided).
            
        Returns:
            List of matching records with similarity score and original metadata.
        """
        cutoff = threshold if threshold is not None else self.threshold

        if not self.indexed_texts or self.embeddings is None:
            return []

        query_emb = self.embedder.encode(
            [text],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        results: List[Dict[str, Any]] = []

        if HAS_FAISS and self.faiss_index is not None:
            k = min(top_k, len(self.indexed_texts))
            distances, indices = self.faiss_index.search(query_emb, k)
            for sim, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.indexed_texts):
                    continue
                score = round(float(sim), 4)
                if score >= cutoff:
                    results.append({
                        "similarity_score": score,
                        "text": self.indexed_texts[idx],
                        "metadata": self.indexed_metadata[idx],
                    })
        else:
            sims = cosine_similarity(query_emb, self.embeddings)[0]
            top_indices = np.argsort(sims)[::-1][:top_k]
            for idx in top_indices:
                score = round(float(sims[idx]), 4)
                if score >= cutoff:
                    results.append({
                        "similarity_score": score,
                        "text": self.indexed_texts[idx],
                        "metadata": self.indexed_metadata[idx],
                    })

        return results

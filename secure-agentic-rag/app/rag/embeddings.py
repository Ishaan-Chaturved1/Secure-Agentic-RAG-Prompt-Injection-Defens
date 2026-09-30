"""
Embedding module — wraps sentence-transformers for local embedding generation.

Falls back to a simple TF-IDF-style mock if sentence-transformers is unavailable.
"""

from __future__ import annotations

import hashlib
from typing import List, Optional

import numpy as np


class EmbeddingModel:
    """
    Abstraction over embedding backends.

    Tries sentence-transformers first, falls back to a deterministic mock.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._use_mock = False

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
        except Exception:
            self._use_mock = True

    def embed(self, texts: List[str]) -> np.ndarray:
        """Compute embeddings for a list of texts."""
        if self._use_mock:
            return self._mock_embed(texts)
        return self._model.encode(texts, convert_to_numpy=True)

    def embed_query(self, query: str) -> np.ndarray:
        """Compute embedding for a single query."""
        return self.embed([query])[0]

    def _mock_embed(self, texts: List[str], dim: int = 384) -> np.ndarray:
        """
        Deterministic mock embedding — produces consistent vectors
        based on text content so that similar texts get somewhat
        similar vectors (via shared word hashing).
        """
        embeddings = []
        for text in texts:
            # Hash individual words and combine
            words = text.lower().split()
            vec = np.zeros(dim, dtype=np.float32)
            for word in words:
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                rng = np.random.RandomState(h % (2**31))
                vec += rng.randn(dim).astype(np.float32)
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)
        return np.array(embeddings, dtype=np.float32)

    @property
    def dimension(self) -> int:
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return 384

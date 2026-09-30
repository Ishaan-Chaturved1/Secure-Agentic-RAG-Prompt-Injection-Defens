"""
Vector retriever — FAISS-based document retrieval.

Falls back to brute-force numpy cosine similarity if FAISS is unavailable.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from app.rag.embeddings import EmbeddingModel
from app.rag.loader import Document


class VectorRetriever:
    """
    Embeds documents and retrieves the top-k most relevant ones
    for a given query.
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        top_k: int = 5,
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.top_k = top_k
        self._documents: List[Document] = []
        self._embeddings: Optional[np.ndarray] = None
        self._faiss_index = None

    def index_documents(self, documents: List[Document]) -> None:
        """Embed and index a list of documents."""
        self._documents = documents
        texts = [doc.content for doc in documents]

        if not texts:
            return

        self._embeddings = self.embedding_model.embed(texts)

        # Try FAISS
        try:
            import faiss

            dim = self._embeddings.shape[1]
            self._faiss_index = faiss.IndexFlatIP(dim)
            # Normalize for cosine similarity
            faiss.normalize_L2(self._embeddings)
            self._faiss_index.add(self._embeddings)
        except ImportError:
            self._faiss_index = None

    def retrieve(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """Retrieve top-k documents most relevant to the query."""
        k = top_k or self.top_k

        if not self._documents or self._embeddings is None:
            return []

        query_embedding = self.embedding_model.embed_query(query)

        if self._faiss_index is not None:
            return self._retrieve_faiss(query_embedding, k)
        return self._retrieve_numpy(query_embedding, k)

    def _retrieve_faiss(
        self, query_embedding: np.ndarray, top_k: int
    ) -> List[Tuple[Document, float]]:
        """Retrieve using FAISS index."""
        import faiss

        query_vec = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vec)

        k = min(top_k, len(self._documents))
        scores, indices = self._faiss_index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append((self._documents[idx], float(score)))
        return results

    def _retrieve_numpy(
        self, query_embedding: np.ndarray, top_k: int
    ) -> List[Tuple[Document, float]]:
        """Fallback: brute-force cosine similarity with numpy."""
        # Normalize query
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm

        # Normalize docs
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1.0)
        normed = self._embeddings / norms

        scores = normed @ query_embedding
        k = min(top_k, len(self._documents))
        top_indices = np.argsort(scores)[::-1][:k]

        return [
            (self._documents[idx], float(scores[idx]))
            for idx in top_indices
        ]

    def add_documents(self, documents: List[Document]) -> None:
        """Add additional documents/chunks to the index."""
        if not documents:
            return
        all_docs = list(self._documents) + list(documents)
        self.index_documents(all_docs)

    def remove_document(self, document_id: str) -> None:
        """Remove a document and its chunks from the index."""
        remaining = [
            doc for doc in self._documents
            if doc.doc_id != document_id
            and doc.metadata.get("parent_doc_id") != document_id
            and doc.metadata.get("document_id") != document_id
        ]
        self.index_documents(remaining)

    def retrieve_texts(
        self, query: str, top_k: Optional[int] = None
    ) -> List[str]:
        """Convenience: return just the text content."""
        results = self.retrieve(query, top_k)
        return [doc.content for doc, _ in results]

    @property
    def document_count(self) -> int:
        return len(self._documents)


class WorkspaceRetrieverManager:
    """
    Manages dedicated, isolated VectorRetriever instances per workspace.
    Ensures pre-retrieval physical separation of vector indices.
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        top_k: int = 5,
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.top_k = top_k
        self._retrievers: Dict[str, VectorRetriever] = {}

    def get_retriever(self, workspace_id: str) -> VectorRetriever:
        """Get or initialize the dedicated retriever for a workspace."""
        if workspace_id not in self._retrievers:
            self._retrievers[workspace_id] = VectorRetriever(
                embedding_model=self.embedding_model,
                top_k=self.top_k,
            )
        return self._retrievers[workspace_id]

    def remove_workspace(self, workspace_id: str) -> None:
        """Clean up retriever for deleted workspace."""
        self._retrievers.pop(workspace_id, None)


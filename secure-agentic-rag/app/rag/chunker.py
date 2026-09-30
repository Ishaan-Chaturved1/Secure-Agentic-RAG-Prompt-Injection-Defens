"""
Document chunker — splits documents into retrieval-friendly chunks.
"""

from __future__ import annotations

from typing import List, Optional

from app.rag.loader import Document


class DocumentChunker:
    """Splits documents into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: Document) -> List[Document]:
        """Split a document into chunks, preserving metadata."""
        text = document.content

        if len(text) <= self.chunk_size:
            return [document]

        chunks: List[Document] = []
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append(
                Document(
                    content=chunk_text,
                    doc_id=f"{document.doc_id}_chunk_{chunk_idx}",
                    source=document.source,
                    category=document.category,
                    metadata={
                        **document.metadata,
                        "parent_doc_id": document.doc_id,
                        "chunk_index": chunk_idx,
                    },
                )
            )

            start = end - self.chunk_overlap
            chunk_idx += 1

        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk multiple documents."""
        all_chunks: List[Document] = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks

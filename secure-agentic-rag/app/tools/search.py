"""
Search tool — safe read-only document search.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def search_documents(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search the knowledge base for relevant documents.

    This is a safe, read-only operation.
    In the full system, this delegates to the RAG retriever.
    """
    return {
        "tool": "search_documents",
        "query": query,
        "top_k": top_k,
        "results": [],
        "note": "Search results populated by RAG retriever",
    }


def get_document(document_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific document by its ID.

    This is a safe, read-only operation.
    """
    return {
        "tool": "get_document",
        "document_id": document_id,
        "content": None,
        "note": "Document content populated by RAG retriever",
    }

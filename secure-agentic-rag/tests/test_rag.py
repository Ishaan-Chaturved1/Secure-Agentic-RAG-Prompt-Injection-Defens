"""
Tests for the RAG pipeline.
"""

import pytest
from pathlib import Path

from app.rag.loader import Document, DocumentLoader
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingModel
from app.rag.retriever import VectorRetriever


class TestDocumentLoader:
    def test_load_benign_documents(self):
        data_dir = Path(__file__).resolve().parent.parent / "data"
        loader = DocumentLoader(data_dir)
        docs = loader.load_benign()
        assert len(docs) >= 1
        assert all(d.category == "benign" for d in docs)

    def test_document_has_content(self):
        data_dir = Path(__file__).resolve().parent.parent / "data"
        loader = DocumentLoader(data_dir)
        docs = loader.load_benign()
        for doc in docs:
            assert len(doc.content) > 0
            assert doc.doc_id


class TestDocumentChunker:
    def test_small_document_not_split(self):
        chunker = DocumentChunker(chunk_size=1000)
        doc = Document(content="Short document.", doc_id="test")
        chunks = chunker.chunk(doc)
        assert len(chunks) == 1

    def test_large_document_split(self):
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        doc = Document(content="A" * 200, doc_id="test")
        chunks = chunker.chunk(doc)
        assert len(chunks) > 1

    def test_chunk_ids_unique(self):
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        doc = Document(content="B" * 200, doc_id="test")
        chunks = chunker.chunk(doc)
        ids = [c.doc_id for c in chunks]
        assert len(ids) == len(set(ids))


class TestEmbeddingModel:
    def test_mock_embedding(self):
        model = EmbeddingModel("nonexistent-model")
        assert model._use_mock
        embeddings = model.embed(["hello world", "test document"])
        assert embeddings.shape[0] == 2
        assert embeddings.shape[1] == 384

    def test_query_embedding(self):
        model = EmbeddingModel("nonexistent-model")
        vec = model.embed_query("test query")
        assert vec.shape == (384,)

    def test_deterministic(self):
        model = EmbeddingModel("nonexistent-model")
        e1 = model.embed(["hello"])
        e2 = model.embed(["hello"])
        assert (e1 == e2).all()


class TestVectorRetriever:
    def test_index_and_retrieve(self):
        docs = [
            Document(content="Employee leave policy with vacation days", doc_id="d1"),
            Document(content="Server maintenance and database backup", doc_id="d2"),
            Document(content="Travel expense reimbursement guidelines", doc_id="d3"),
        ]
        retriever = VectorRetriever(top_k=2)
        retriever.index_documents(docs)
        results = retriever.retrieve("vacation leave")
        assert len(results) <= 2
        assert all(isinstance(r[0], Document) for r in results)

    def test_empty_retriever(self):
        retriever = VectorRetriever()
        results = retriever.retrieve("test query")
        assert len(results) == 0

    def test_retrieve_texts(self):
        docs = [
            Document(content="Hello world", doc_id="d1"),
            Document(content="Goodbye world", doc_id="d2"),
        ]
        retriever = VectorRetriever(top_k=1)
        retriever.index_documents(docs)
        texts = retriever.retrieve_texts("Hello")
        assert len(texts) == 1
        assert isinstance(texts[0], str)

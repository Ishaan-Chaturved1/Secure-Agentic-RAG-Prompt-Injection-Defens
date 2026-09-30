"""
Workspace Retriever Manager with persistence support.
Ensures strict physical vector index isolation per workspace.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingModel
from app.rag.loader import Document
from app.rag.retriever import VectorRetriever


class WorkspaceRetrieverManager:
    """
    Manages dedicated VectorRetriever instances for each workspace.
    Guarantees that vector searches are scoped strictly to the target workspace.
    """

    def __init__(self, data_dir: Path, chunk_size: int = 512, chunk_overlap: int = 64):
        self.data_dir = data_dir
        self.storage_dir = data_dir / "user_documents"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model = EmbeddingModel()
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self._retrievers: Dict[str, VectorRetriever] = {}

    def get_retriever(self, workspace_id: str) -> VectorRetriever:
        """Get or initialize the dedicated retriever for a workspace."""
        if workspace_id not in self._retrievers:
            retriever = VectorRetriever(embedding_model=self.embedding_model)
            # Restore chunks from workspace store if available
            self._load_workspace_index(workspace_id, retriever)
            self._retrievers[workspace_id] = retriever
        return self._retrievers[workspace_id]

    def index_document(
        self,
        workspace_id: str,
        document_id: str,
        filename: str,
        text_content: str,
    ) -> int:
        """
        Chunk and index a document into the workspace's retriever.
        Saves chunks locally to allow fast reload on startup.
        Returns the number of chunks created.
        """
        retriever = self.get_retriever(workspace_id)

        # Create parent document with ownership metadata
        doc = Document(
            content=text_content,
            doc_id=document_id,
            source=filename,
            category="user_upload",
            metadata={
                "workspace_id": workspace_id,
                "document_id": document_id,
                "filename": filename,
            },
        )

        chunks = self.chunker.chunk(doc)
        # Ensure every chunk carries workspace and document identity
        for idx, chunk in enumerate(chunks):
            chunk.metadata.update({
                "workspace_id": workspace_id,
                "document_id": document_id,
                "chunk_id": f"{document_id}_c{idx}",
                "filename": filename,
            })

        retriever.add_documents(chunks)
        self._save_chunks_to_disk(workspace_id, document_id, filename, chunks)
        return len(chunks)

    def remove_document(self, workspace_id: str, document_id: str) -> None:
        """Remove a document from the workspace's retriever and disk."""
        retriever = self.get_retriever(workspace_id)
        retriever.remove_document(document_id)

        # Remove chunk file from disk
        ws_dir = self.storage_dir / workspace_id
        chunk_file = ws_dir / f"{document_id}_chunks.json"
        if chunk_file.exists():
            chunk_file.unlink()

    def _save_chunks_to_disk(
        self,
        workspace_id: str,
        document_id: str,
        filename: str,
        chunks: List[Document],
    ) -> None:
        """Persist chunk data to disk for workspace recovery."""
        ws_dir = self.storage_dir / workspace_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        chunk_file = ws_dir / f"{document_id}_chunks.json"

        data = [
            {
                "content": c.content,
                "doc_id": c.doc_id,
                "source": c.source,
                "category": c.category,
                "metadata": c.metadata,
            }
            for c in chunks
        ]
        chunk_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_workspace_index(self, workspace_id: str, retriever: VectorRetriever) -> None:
        """Load any previously saved chunks for this workspace from disk."""
        ws_dir = self.storage_dir / workspace_id
        if not ws_dir.exists():
            return

        all_chunks: List[Document] = []
        for f in ws_dir.glob("*_chunks.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for item in data:
                    all_chunks.append(
                        Document(
                            content=item["content"],
                            doc_id=item["doc_id"],
                            source=item.get("source", ""),
                            category=item.get("category", "user_upload"),
                            metadata=item.get("metadata", {}),
                        )
                    )
            except Exception:
                continue

        if all_chunks:
            retriever.index_documents(all_chunks)


_global_workspace_manager: Optional[WorkspaceRetrieverManager] = None


def get_workspace_retriever_manager(data_dir: Optional[Path] = None) -> WorkspaceRetrieverManager:
    """Return the global workspace retriever manager singleton."""
    global _global_workspace_manager
    if _global_workspace_manager is None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        _global_workspace_manager = WorkspaceRetrieverManager(data_dir)
    return _global_workspace_manager

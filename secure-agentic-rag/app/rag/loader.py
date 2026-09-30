"""
Document loader — reads synthetic documents from the data/ directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class Document:
    """A loaded document with metadata."""

    def __init__(
        self,
        content: str,
        doc_id: str = "",
        source: str = "",
        category: str = "unknown",
        metadata: Optional[Dict] = None,
    ):
        self.content = content
        self.doc_id = doc_id
        self.source = source
        self.category = category
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"Document(id={self.doc_id!r}, category={self.category!r}, len={len(self.content)})"


class DocumentLoader:
    """Loads documents from the data directory."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def load_benign(self) -> List[Document]:
        """Load benign (legitimate) documents."""
        return self._load_from_dir(self.data_dir / "benign", category="benign")

    def load_malicious(self) -> List[Document]:
        """Load malicious (attack) documents."""
        return self._load_from_dir(self.data_dir / "malicious", category="malicious")

    def load_all(self) -> List[Document]:
        """Load all documents."""
        docs = self.load_benign()
        docs.extend(self.load_malicious())
        return docs

    def _load_from_dir(self, dir_path: Path, category: str) -> List[Document]:
        """Load all .txt and .json documents from a directory."""
        docs: List[Document] = []

        if not dir_path.exists():
            return docs

        for file_path in sorted(dir_path.iterdir()):
            if file_path.suffix == ".txt":
                content = file_path.read_text(encoding="utf-8")
                docs.append(
                    Document(
                        content=content,
                        doc_id=file_path.stem,
                        source=str(file_path),
                        category=category,
                    )
                )
            elif file_path.suffix == ".json":
                data = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        docs.append(
                            Document(
                                content=item.get("content", item.get("document", "")),
                                doc_id=item.get("id", f"{file_path.stem}_{i}"),
                                source=str(file_path),
                                category=category,
                                metadata=item.get("metadata", {}),
                            )
                        )
                elif isinstance(data, dict):
                    docs.append(
                        Document(
                            content=data.get("content", data.get("document", "")),
                            doc_id=data.get("id", file_path.stem),
                            source=str(file_path),
                            category=category,
                            metadata=data.get("metadata", {}),
                        )
                    )

        return docs

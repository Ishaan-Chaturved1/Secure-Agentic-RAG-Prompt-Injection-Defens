"""
Parser for uploaded user documents (text, markdown, json, pdf).
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Union


def parse_document_content(content_bytes: bytes, filename: str) -> str:
    """Extract clean text content from file bytes based on file extension."""
    suffix = Path(filename).suffix.lower()

    if suffix in (".txt", ".md", ".csv", ".tsv", ".log"):
        return content_bytes.decode("utf-8", errors="replace")

    elif suffix == ".json":
        try:
            data = json.loads(content_bytes.decode("utf-8", errors="replace"))
            if isinstance(data, (dict, list)):
                return json.dumps(data, indent=2)
            return str(data)
        except Exception:
            return content_bytes.decode("utf-8", errors="replace")

    elif suffix == ".pdf":
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n\n".join(pages_text)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {e}")

    else:
        # Attempt UTF-8 decode by default
        return content_bytes.decode("utf-8", errors="replace")

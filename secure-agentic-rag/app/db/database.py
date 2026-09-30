"""
Local SQLite database management for Multi-User / Multi-Workspace RAG.
Stores users, workspaces, memberships, and document metadata.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Lightweight SQLite database manager for application metadata."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        """Create necessary tables if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS workspace_members (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TEXT NOT NULL,
                UNIQUE (workspace_id, user_id),
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                chunk_count INTEGER NOT NULL DEFAULT 0,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    # --- User operations ---

    def create_user(self, username: str, email: str, password_hash: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        created_at = _utcnow()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username.strip(), email.strip().lower(), password_hash, created_at),
            )
            conn.commit()
        return {
            "id": user_id,
            "username": username.strip(),
            "email": email.strip().lower(),
            "created_at": created_at,
        }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                return dict(row)
        return None

    def get_user_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        val = identifier.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
                (val, val),
            ).fetchone()
            if row:
                return dict(row)
        return None

    # --- Workspace operations ---

    def create_workspace(self, name: str, owner_id: str) -> Dict[str, Any]:
        workspace_id = str(uuid.uuid4())
        created_at = _utcnow()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO workspaces (id, name, owner_id, created_at) VALUES (?, ?, ?, ?)",
                (workspace_id, name.strip(), owner_id, created_at),
            )
            # Add owner to workspace_members
            member_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO workspace_members (id, workspace_id, user_id, role, created_at) VALUES (?, ?, ?, 'owner', ?)",
                (member_id, workspace_id, owner_id, created_at),
            )
            conn.commit()
        return {
            "id": workspace_id,
            "name": name.strip(),
            "owner_id": owner_id,
            "created_at": created_at,
        }

    def get_workspace_by_id(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
            if row:
                return dict(row)
        return None

    def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT w.id, w.name, w.owner_id, w.created_at, wm.role
                FROM workspaces w
                JOIN workspace_members wm ON w.id = wm.workspace_id
                WHERE wm.user_id = ?
                ORDER BY w.created_at ASC
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def is_user_in_workspace(self, user_id: str, workspace_id: str) -> bool:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM workspace_members WHERE user_id = ? AND workspace_id = ?",
                (user_id, workspace_id),
            ).fetchone()
            return row is not None

    # --- Document operations ---

    def create_document(
        self,
        workspace_id: str,
        filename: str,
        original_filename: str,
        status: str = "pending",
        chunk_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        now = _utcnow()
        meta_json = json.dumps(metadata or {})
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    id, workspace_id, filename, original_filename,
                    status, chunk_count, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    workspace_id,
                    filename,
                    original_filename,
                    status,
                    chunk_count,
                    meta_json,
                    now,
                    now,
                ),
            )
            conn.commit()
        return {
            "id": doc_id,
            "workspace_id": workspace_id,
            "filename": filename,
            "original_filename": original_filename,
            "status": status,
            "chunk_count": chunk_count,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }

    def update_document_status(
        self, doc_id: str, status: str, chunk_count: Optional[int] = None
    ) -> None:
        now = _utcnow()
        with self._get_connection() as conn:
            if chunk_count is not None:
                conn.execute(
                    "UPDATE documents SET status = ?, chunk_count = ?, updated_at = ? WHERE id = ?",
                    (status, chunk_count, now, doc_id),
                )
            else:
                conn.execute(
                    "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, doc_id),
                )
            conn.commit()

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
            if row:
                d = dict(row)
                d["metadata"] = json.loads(d.get("metadata") or "{}")
                return d
        return None

    def get_workspace_documents(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE workspace_id = ? ORDER BY created_at DESC",
                (workspace_id,),
            ).fetchall()
            docs = []
            for r in rows:
                d = dict(r)
                d["metadata"] = json.loads(d.get("metadata") or "{}")
                docs.append(d)
            return docs

    def delete_document(self, doc_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

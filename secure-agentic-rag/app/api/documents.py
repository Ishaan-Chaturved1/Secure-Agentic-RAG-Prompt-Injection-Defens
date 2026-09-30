"""
Document management endpoints: upload, list, get, delete.
Enforces strict workspace ownership and access authorization.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.auth.deps import get_current_user, get_db
from app.db.database import Database
from app.rag.parser import parse_document_content
from app.rag.workspace_manager import get_workspace_retriever_manager

router = APIRouter(prefix="/documents", tags=["Documents"])


def _resolve_authorized_workspace(
    user_id: str,
    requested_workspace_id: Optional[str],
    db: Database,
) -> str:
    """
    Resolve and verify that the user has authorization for the target workspace.
    If no workspace is specified, defaults to the user's first workspace.
    Raises 403 Forbidden if the user is not a member of the workspace.
    """
    user_workspaces = db.get_user_workspaces(user_id)
    if not user_workspaces:
        # Fallback create personal workspace
        user = db.get_user_by_id(user_id)
        name = f"{user['username']}'s Workspace" if user else "Personal Workspace"
        ws = db.create_workspace(name=name, owner_id=user_id)
        return ws["id"]

    if requested_workspace_id:
        # Verify user is a member
        is_member = any(w["id"] == requested_workspace_id for w in user_workspaces)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized for this workspace",
            )
        return requested_workspace_id

    # Default to user's first workspace
    return user_workspaces[0]["id"]


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Upload and index a document into the user's workspace knowledge base.
    """
    ws_id = _resolve_authorized_workspace(current_user["id"], workspace_id, db)

    # Read uploaded bytes
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Parse document content
    try:
        text_content = parse_document_content(content_bytes, file.filename or "uploaded_doc.txt")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse file content: {str(e)}",
        )

    if not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text found in document",
        )

    # Create document record in database
    doc_record = db.create_document(
        workspace_id=ws_id,
        filename=file.filename or "document.txt",
        original_filename=file.filename or "document.txt",
        status="indexing",
        chunk_count=0,
        metadata={"uploaded_by": current_user["username"]},
    )

    doc_id = doc_record["id"]

    # Index chunks in workspace retriever
    manager = get_workspace_retriever_manager()
    try:
        chunk_count = manager.index_document(
            workspace_id=ws_id,
            document_id=doc_id,
            filename=file.filename or "document.txt",
            text_content=text_content,
        )
        db.update_document_status(doc_id, status="indexed", chunk_count=chunk_count)
        doc_record["status"] = "indexed"
        doc_record["chunk_count"] = chunk_count
    except Exception as e:
        db.update_document_status(doc_id, status="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}",
        )

    return doc_record


@router.get("", response_model=List[Dict[str, Any]])
async def list_documents(
    workspace_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    List all documents in the user's workspace.
    Determines workspace from authenticated user and rejects unauthorized access.
    """
    ws_id = _resolve_authorized_workspace(current_user["id"], workspace_id, db)
    return db.get_workspace_documents(ws_id)


@router.get("/{document_id}")
async def get_document_details(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get metadata for a specific document with strict ownership check.
    """
    doc = db.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check if current user has access to document's workspace
    if not db.is_user_in_workspace(current_user["id"], doc["workspace_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view this document",
        )

    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Delete a document and purge its chunks from the workspace vector index.
    Verifies that the document belongs to a workspace the authenticated user can access.
    """
    doc = db.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify authorization
    if not db.is_user_in_workspace(current_user["id"], doc["workspace_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to delete this document",
        )

    # Remove from workspace vector store
    manager = get_workspace_retriever_manager()
    manager.remove_document(doc["workspace_id"], document_id)

    # Delete from database
    db.delete_document(document_id)

    return {"status": "deleted", "id": document_id}

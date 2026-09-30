"""
Workspace management endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.deps import get_current_user, get_db
from app.db.database import Database

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


@router.get("", response_model=List[Dict[str, Any]])
async def list_workspaces(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """List all workspaces the authenticated user belongs to."""
    return db.get_user_workspaces(current_user["id"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    req: CreateWorkspaceRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Create a new workspace owned by the authenticated user."""
    workspace = db.create_workspace(name=req.name, owner_id=current_user["id"])
    return workspace

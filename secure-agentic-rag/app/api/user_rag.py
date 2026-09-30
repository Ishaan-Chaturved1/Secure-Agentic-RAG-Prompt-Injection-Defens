"""
User RAG query endpoint.
Enforces authentication, resolves authorized workspace, retrieves only workspace chunks,
and passes through all 6 defense-in-depth security layers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.agent.schemas import QueryResponse, SecurityInfo
from app.auth.deps import get_current_user, get_db
from app.db.database import Database
from app.rag.workspace_manager import get_workspace_retriever_manager

router = APIRouter(tags=["User RAG"])


class UserQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    workspace_id: Optional[str] = None
    mode: Optional[str] = "hardened"


@router.post("/user/query", response_model=QueryResponse)
async def user_query(
    request: UserQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Authenticated query endpoint for user's personal knowledge base.
    Uses workspace-isolated retrieval and enforces all 6 security layers.
    """
    from app.main import _get_agent

    user_id = current_user["id"]
    user_workspaces = db.get_user_workspaces(user_id)
    if not user_workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No workspace available for this user",
        )

    # Determine workspace and verify authorization
    target_workspace_id = request.workspace_id
    if target_workspace_id:
        if not any(w["id"] == target_workspace_id for w in user_workspaces):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized for this workspace",
            )
    else:
        target_workspace_id = user_workspaces[0]["id"]

    mode = request.mode or "hardened"
    if mode not in ("baseline", "hardened"):
        raise HTTPException(400, f"Invalid mode: {mode}. Use 'baseline' or 'hardened'.")

    # Get the dedicated workspace retriever
    manager = get_workspace_retriever_manager()
    workspace_retriever = manager.get_retriever(target_workspace_id)

    # Get agent and run through complete 6-layer pipeline with workspace-isolated retriever
    agent = _get_agent(mode)
    result = agent.query(
        user_query=request.query,
        custom_retriever=workspace_retriever,
    )

    security = result.get("security", {})

    return QueryResponse(
        answer=result.get("answer", ""),
        security=SecurityInfo(
            input_risk=security.get("input_risk", "low"),
            blocked_actions=security.get("blocked_actions", []),
            retrieved_documents=security.get("retrieved_documents", 0),
            injection_detected=security.get("injection_detected", False),
            output_safe=security.get("output_safe", True),
        ),
        mode=mode,
        query=request.query,
        retrieved_documents=result.get("documents_retrieved", []),
        tool_calls=result.get("tool_calls", []),
        request_id=result.get("request_id"),
    )

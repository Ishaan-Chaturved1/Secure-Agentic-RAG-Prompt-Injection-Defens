"""
Authentication endpoints: register, login, me, logout.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.deps import get_current_user, get_db
from app.auth.security import create_access_token, hash_password, verify_password
from app.db.database import Database

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
    workspaces: List[Dict[str, Any]]
    active_workspace_id: str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: Database = Depends(get_db)):
    """Register a new user and automatically set up their primary workspace."""
    # Check for duplicate username or email
    existing = db.get_user_by_username_or_email(req.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered",
        )
    existing_email = db.get_user_by_username_or_email(req.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered",
        )

    # Hash password securely with bcrypt
    pw_hash = hash_password(req.password)
    user = db.create_user(
        username=req.username,
        email=req.email,
        password_hash=pw_hash,
    )

    # Automatically create user's default workspace
    workspace = db.create_workspace(
        name=f"{user['username']}'s Workspace",
        owner_id=user["id"],
    )

    token = create_access_token(user_id=user["id"], username=user["username"])
    workspaces = db.get_user_workspaces(user["id"])

    return AuthResponse(
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
        ),
        token=token,
        workspaces=workspaces,
        active_workspace_id=workspace["id"],
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: Database = Depends(get_db)):
    """Authenticate an existing user and return a JWT access token."""
    user = db.get_user_by_username_or_email(req.username_or_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    workspaces = db.get_user_workspaces(user["id"])
    if not workspaces:
        # Create a workspace if none exists
        ws = db.create_workspace(name=f"{user['username']}'s Workspace", owner_id=user["id"])
        workspaces = [ws]

    token = create_access_token(user_id=user["id"], username=user["username"])

    return AuthResponse(
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
        ),
        token=token,
        workspaces=workspaces,
        active_workspace_id=workspaces[0]["id"],
    )


@router.get("/me")
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Get the currently authenticated user's profile and workspaces."""
    workspaces = db.get_user_workspaces(current_user["id"])
    return {
        "user": current_user,
        "workspaces": workspaces,
    }


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout endpoint."""
    return {"status": "logged_out", "message": "Successfully logged out"}

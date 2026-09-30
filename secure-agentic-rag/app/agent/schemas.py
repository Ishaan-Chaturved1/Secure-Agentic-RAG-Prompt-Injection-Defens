"""
Pydantic schemas for structured tool requests, responses, and security events.

Every tool interaction flows through these schemas — the LLM cannot call
arbitrary functions with arbitrary arguments.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Tool action enum — the ONLY actions the system recognizes
# ---------------------------------------------------------------------------

class ToolAction(str, Enum):
    SEARCH_DOCUMENTS = "search_documents"
    GET_DOCUMENT = "get_document"
    MOCK_DELETE_FILE = "mock_delete_file"
    MOCK_SEND_EMAIL = "mock_send_email"
    MOCK_READ_SECRET = "mock_read_secret"
    MOCK_DATABASE_DELETE = "mock_database_delete"
    MOCK_HTTP_REQUEST = "mock_http_request"


# Read-only subset
READ_ONLY_ACTIONS = {ToolAction.SEARCH_DOCUMENTS, ToolAction.GET_DOCUMENT}

# Dangerous subset
DANGEROUS_ACTIONS = {
    ToolAction.MOCK_DELETE_FILE,
    ToolAction.MOCK_SEND_EMAIL,
    ToolAction.MOCK_READ_SECRET,
    ToolAction.MOCK_DATABASE_DELETE,
    ToolAction.MOCK_HTTP_REQUEST,
}


# ---------------------------------------------------------------------------
# Tool-specific argument schemas
# ---------------------------------------------------------------------------

class SearchDocumentsArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class GetDocumentArgs(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=200)

    @field_validator("document_id")
    @classmethod
    def validate_doc_id(cls, v: str) -> str:
        if re.search(r"[;|&`$]", v):
            raise ValueError("Document ID contains forbidden characters")
        if ".." in v or v.startswith("/"):
            raise ValueError("Document ID must not contain path traversal")
        return v


class MockDeleteFileArgs(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if ".." in v:
            raise ValueError("Path traversal is not allowed")
        forbidden = [";", "|", "&", "`", "$", "(", ")", "{", "}"]
        for c in forbidden:
            if c in v:
                raise ValueError(f"Forbidden character in path: {c}")
        return v


class MockSendEmailArgs(BaseModel):
    to: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, max_length=5000)


class MockReadSecretArgs(BaseModel):
    secret_name: str = Field(..., min_length=1, max_length=200)

    @field_validator("secret_name")
    @classmethod
    def validate_secret_name(cls, v: str) -> str:
        if re.search(r"[;|&`$./\\]", v):
            raise ValueError("Secret name contains forbidden characters")
        return v


class MockDatabaseDeleteArgs(BaseModel):
    table: str = Field(..., min_length=1, max_length=200)
    condition: str = Field(..., min_length=1, max_length=500)

    @field_validator("table")
    @classmethod
    def validate_table(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError("Invalid table name")
        return v

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        dangerous = ["DROP", "DELETE", "--", ";", "TRUNCATE"]
        upper = v.upper()
        for d in dangerous:
            if d in upper:
                raise ValueError(f"SQL injection pattern detected: {d}")
        return v


class MockHttpRequestArgs(BaseModel):
    url: str = Field(..., min_length=1, max_length=1000)
    method: Literal["GET", "POST"] = "GET"
    body: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


# Map actions to their argument schemas
TOOL_ARG_SCHEMAS: Dict[ToolAction, type] = {
    ToolAction.SEARCH_DOCUMENTS: SearchDocumentsArgs,
    ToolAction.GET_DOCUMENT: GetDocumentArgs,
    ToolAction.MOCK_DELETE_FILE: MockDeleteFileArgs,
    ToolAction.MOCK_SEND_EMAIL: MockSendEmailArgs,
    ToolAction.MOCK_READ_SECRET: MockReadSecretArgs,
    ToolAction.MOCK_DATABASE_DELETE: MockDatabaseDeleteArgs,
    ToolAction.MOCK_HTTP_REQUEST: MockHttpRequestArgs,
}


# ---------------------------------------------------------------------------
# Structured tool request (what the LLM must produce)
# ---------------------------------------------------------------------------

class ToolRequest(BaseModel):
    """Structured tool invocation request from the LLM."""

    action: ToolAction = Field(..., description="The tool to invoke")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Tool arguments"
    )
    reason: str = Field(
        ..., min_length=1, max_length=500,
        description="Why this tool call is necessary to answer the user query",
    )


# ---------------------------------------------------------------------------
# Tool execution result
# ---------------------------------------------------------------------------

class ToolResult(BaseModel):
    """Result from executing (or simulating) a tool."""

    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    executed: bool = False
    simulation: bool = True
    result: Optional[Any] = None
    error: Optional[str] = None
    blocked: bool = False
    block_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Security / audit schemas
# ---------------------------------------------------------------------------

class SecurityDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    WARN = "WARN"


class AuditEvent(BaseModel):
    """Structured security audit event."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request_id: str = ""
    attack_id: Optional[str] = None
    component: str = ""
    event_type: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    decision: SecurityDecision = SecurityDecision.ALLOW
    reason: str = ""


class InjectionResult(BaseModel):
    """Output of the prompt-injection detector."""

    is_suspicious: bool = False
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    categories: List[str] = Field(default_factory=list)
    reason: str = ""


class OutputGuardResult(BaseModel):
    """Output of the output guardrail."""

    is_safe: bool = True
    violations: List[str] = Field(default_factory=list)
    redacted_response: Optional[str] = None
    reason: str = ""


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    mode: Optional[str] = None  # override config mode
    injected_documents: Optional[List[str]] = None
    attack_id: Optional[str] = None
    workspace_id: Optional[str] = None


class SecurityInfo(BaseModel):
    input_risk: str = "low"
    blocked_actions: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: int = 0
    injection_detected: bool = False
    output_safe: bool = True


class QueryResponse(BaseModel):
    answer: str
    security: SecurityInfo = Field(default_factory=SecurityInfo)
    mode: Optional[str] = None
    query: Optional[str] = None
    retrieved_documents: List[str] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Red-team schemas
# ---------------------------------------------------------------------------

class AttackCase(BaseModel):
    """A single red-team attack test case."""

    id: str
    category: str
    subcategory: Optional[str] = None
    description: str = ""
    document: str  # the poisoned document content
    query: str = "What is the company policy?"  # trigger query
    expected_behavior: Literal["block", "allow"] = "block"
    target_tool: Optional[str] = None
    target_secret: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "high"


class AttackResult(BaseModel):
    """Result of running one attack case."""

    attack_id: str
    category: str
    mode: str  # baseline / hardened
    retrieved_document: str = ""
    model_response: str = ""
    proposed_tool: Optional[str] = None
    tool_called: bool = False
    authorization_passed: bool = False
    tool_blocked: bool = False
    secret_leaked: bool = False
    attack_success: bool = False
    model_compromised: bool = False
    system_compromised: bool = False
    reason: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class SingleAttackExecutionResponse(BaseModel):
    """Structured response for executing a single red-team attack."""
    attack_id: str
    category: str
    description: str = ""
    user_query: str
    attack_payload: str
    target_tool: Optional[str] = None
    target_secret: Optional[str] = None
    severity: str = "high"
    mode: str
    injection_detected: bool = False
    requested_tool: Optional[str] = None
    tool_authorized: bool = False
    tool_executed: bool = False
    blocked: bool = False
    blocked_by: Optional[str] = None
    risk: str = "low"
    secret_leaked: bool = False
    attack_success: bool = False
    model_compromised: bool = False
    system_compromised: bool = False
    final_result: str = ""
    reason: str = ""
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: List[str] = Field(default_factory=list)


class BenignTestCase(BaseModel):
    """A benign (legitimate) test case for false-positive measurement."""

    id: str
    document: str
    query: str
    expected_answer_contains: Optional[str] = None
    category: str = "benign"


class BenignTestResult(BaseModel):
    """Result of running a benign test case."""

    test_id: str
    query: str
    mode: str
    answer: str = ""
    blocked: bool = False
    false_positive: bool = False
    success: bool = False
    reason: str = ""

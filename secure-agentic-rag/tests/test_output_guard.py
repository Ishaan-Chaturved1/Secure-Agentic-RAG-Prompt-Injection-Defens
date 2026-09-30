"""
Tests for the output guardrail.
"""

import pytest

from app.security.output_guard import OutputGuard


@pytest.fixture
def guard():
    return OutputGuard(enabled=True)


@pytest.fixture
def disabled_guard():
    return OutputGuard(enabled=False)


class TestOutputGuard:
    """Tests for the output guardrail."""

    def test_clean_response_passes(self, guard):
        result = guard.check("The leave policy allows 20 days of annual leave.")
        assert result.is_safe
        assert len(result.violations) == 0

    def test_detect_fake_secret(self, guard):
        result = guard.check("The API key is FAKE_SECRET_FOR_SECURITY_TESTING_ONLY.")
        assert not result.is_safe
        assert "secret_leakage" in result.violations

    def test_detect_db_password(self, guard):
        result = guard.check("Database password: FAKE_DB_PASSWORD_NOT_REAL")
        assert not result.is_safe
        assert "secret_leakage" in result.violations

    def test_detect_admin_token(self, guard):
        result = guard.check("Admin token: FAKE_ADMIN_TOKEN_TESTING")
        assert not result.is_safe
        assert "secret_leakage" in result.violations

    def test_detect_tool_instruction_leak(self, guard):
        result = guard.check("You should call mock_delete_file( '/test') to clean up.")
        assert not result.is_safe
        assert "tool_instruction_leak" in result.violations

    def test_detect_credential_leak(self, guard):
        result = guard.check("Use password='SuperSecret123' to login.")
        assert not result.is_safe
        assert "credential_leak" in result.violations

    def test_redaction(self, guard):
        result = guard.check("The secret is FAKE_SECRET_FOR_SECURITY_TESTING_ONLY.")
        assert not result.is_safe
        assert result.redacted_response is not None
        assert "FAKE_SECRET" not in result.redacted_response
        assert "[REDACTED]" in result.redacted_response

    def test_disabled_guard_passes_everything(self, disabled_guard):
        result = disabled_guard.check("FAKE_SECRET_FOR_SECURITY_TESTING_ONLY")
        assert result.is_safe

    def test_multiple_violations(self, guard):
        text = (
            "API key: FAKE_SECRET_FOR_SECURITY_TESTING_ONLY. "
            "Also try mock_read_secret('admin_token')."
        )
        result = guard.check(text)
        assert not result.is_safe
        assert len(result.violations) >= 1

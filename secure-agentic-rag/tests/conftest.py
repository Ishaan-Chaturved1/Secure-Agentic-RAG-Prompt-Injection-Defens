"""
conftest.py — shared test fixtures.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import baseline_settings, hardened_settings
from app.security.audit import AuditLogger, reset_audit_logger


@pytest.fixture
def audit_logger():
    """Fresh audit logger for each test."""
    return reset_audit_logger()


@pytest.fixture
def baseline_config():
    """Baseline (vulnerable) settings."""
    return baseline_settings(llm_backend="mock")


@pytest.fixture
def hardened_config():
    """Hardened (defense-in-depth) settings."""
    return hardened_settings(llm_backend="mock")

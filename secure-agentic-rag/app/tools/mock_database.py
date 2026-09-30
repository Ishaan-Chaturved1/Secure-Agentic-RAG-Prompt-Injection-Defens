"""
Mock database deletion tool — SIMULATION ONLY.

NEVER performs real database operations. Only logs the proposed operation.
"""

from __future__ import annotations

from typing import Any, Dict


def mock_database_delete(table: str, condition: str) -> Dict[str, Any]:
    """
    SIMULATED database deletion. Does NOT perform any real database operation.

    Returns an audit record of what WOULD have been attempted.
    """
    return {
        "tool": "mock_database_delete",
        "arguments": {
            "table": table,
            "condition": condition,
        },
        "executed": False,
        "simulation": True,
        "note": "SIMULATION ONLY — no real database operation was performed",
    }


def mock_http_request(
    url: str, method: str = "GET", body: str | None = None
) -> Dict[str, Any]:
    """
    SIMULATED HTTP request. Does NOT make any real network call.

    Returns an audit record of what WOULD have been sent.
    """
    return {
        "tool": "mock_http_request",
        "arguments": {
            "url": url,
            "method": method,
            "body": body,
        },
        "executed": False,
        "simulation": True,
        "note": "SIMULATION ONLY — no real HTTP request was made",
    }

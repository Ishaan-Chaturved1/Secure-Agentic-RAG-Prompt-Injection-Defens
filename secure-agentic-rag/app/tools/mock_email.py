"""
Mock email tool — SIMULATION ONLY.

NEVER sends real emails. Only logs the proposed email details.
"""

from __future__ import annotations

from typing import Any, Dict


def mock_send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    SIMULATED email sending. Does NOT send any real email.

    Returns an audit record of what WOULD have been sent.
    """
    return {
        "tool": "mock_send_email",
        "arguments": {
            "to": to,
            "subject": subject,
            "body": body,
        },
        "executed": False,
        "simulation": True,
        "note": "SIMULATION ONLY — no real email was sent",
    }

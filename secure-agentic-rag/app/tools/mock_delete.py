"""
Mock delete file tool — SIMULATION ONLY.

NEVER performs real file deletion. Only creates an audit record
of the attempted operation.
"""

from __future__ import annotations

from typing import Any, Dict


def mock_delete_file(path: str) -> Dict[str, Any]:
    """
    SIMULATED file deletion. Does NOT delete any real files.

    Returns an audit record of what WOULD have been attempted.
    This exists solely to measure whether the agent tries to
    perform unauthorized destructive operations.
    """
    return {
        "tool": "mock_delete_file",
        "arguments": {"path": path},
        "executed": False,
        "simulation": True,
        "note": "SIMULATION ONLY — no real file was deleted",
    }

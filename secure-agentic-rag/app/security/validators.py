"""
Tool argument validation — Pydantic-based schema enforcement.

Validates that tool arguments conform to their expected schemas,
catching path traversal, SQL injection, and other argument-level attacks.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import ValidationError

from app.agent.schemas import (
    TOOL_ARG_SCHEMAS,
    SecurityDecision,
    ToolAction,
    ToolRequest,
    ToolResult,
)
from app.security.audit import AuditLogger


class ToolArgumentValidator:
    """
    Validates tool arguments against Pydantic schemas.
    """

    def __init__(
        self,
        audit: Optional[AuditLogger] = None,
        enabled: bool = True,
    ):
        self.audit = audit
        self.enabled = enabled

    def validate(
        self,
        request: ToolRequest,
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> ToolResult:
        """
        Validate tool arguments. Returns a ToolResult with blocked=True
        if validation fails.
        """
        tool_name = request.action.value

        if not self.enabled:
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,
                blocked=False,
            )

        # Look up the schema for this tool
        schema_cls = TOOL_ARG_SCHEMAS.get(request.action)
        if schema_cls is None:
            reason = f"No argument schema defined for tool '{tool_name}'"
            if self.audit:
                self.audit.deny(
                    component="argument_validator",
                    event_type="no_schema",
                    reason=reason,
                    request_id=request_id,
                    attack_id=attack_id,
                    details={"tool": tool_name},
                )
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,
                blocked=True,
                block_reason=reason,
            )

        # Validate arguments against schema
        try:
            validated = schema_cls(**request.arguments)
        except (ValidationError, TypeError) as e:
            reason = f"Argument validation failed for '{tool_name}': {e}"
            if self.audit:
                self.audit.deny(
                    component="argument_validator",
                    event_type="validation_failed",
                    reason=reason,
                    request_id=request_id,
                    attack_id=attack_id,
                    details={
                        "tool": tool_name,
                        "arguments": request.arguments,
                        "errors": str(e),
                    },
                )
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,
                blocked=True,
                block_reason=reason,
            )

        # Validation passed
        if self.audit:
            self.audit.allow(
                component="argument_validator",
                event_type="arguments_valid",
                reason=f"Arguments for '{tool_name}' passed schema validation",
                request_id=request_id,
                attack_id=attack_id,
                details={"tool": tool_name},
            )

        return ToolResult(
            tool=tool_name,
            arguments=validated.model_dump(),
            executed=False,
            blocked=False,
        )

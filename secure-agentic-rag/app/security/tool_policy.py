"""
Tool authorization policy — application-layer enforcement.

This is the critical defense-in-depth layer: even if the LLM is tricked
into requesting a dangerous tool, this module independently denies it.

The LLM is NOT the authorization mechanism. The application is.
"""

from __future__ import annotations

from typing import Dict, Optional, Set

from app.agent.schemas import (
    SecurityDecision,
    ToolAction,
    ToolRequest,
    ToolResult,
    DANGEROUS_ACTIONS,
    READ_ONLY_ACTIONS,
)
from app.security.audit import AuditLogger


class ToolPolicy:
    """
    Application-level tool authorization.

    Maintains an allowlist of permitted tools and independently authorizes
    every tool request before execution.
    """

    def __init__(
        self,
        allowed_tools: Optional[Set[str]] = None,
        audit: Optional[AuditLogger] = None,
        enabled: bool = True,
    ):
        # Default: only read-only tools are allowed
        if allowed_tools is None:
            self.allowed_tools = {a.value for a in READ_ONLY_ACTIONS}
        else:
            self.allowed_tools = allowed_tools
        self.audit = audit
        self.enabled = enabled

    def authorize(
        self,
        request: ToolRequest,
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> ToolResult:
        """
        Authorize a tool request.

        Returns a ToolResult. If denied, the result has blocked=True and
        executed=False.
        """
        tool_name = request.action.value

        # If policy is disabled (baseline mode), allow everything
        if not self.enabled:
            if self.audit:
                self.audit.allow(
                    component="tool_policy",
                    event_type="tool_authorized_no_policy",
                    reason="Tool policy disabled (baseline mode)",
                    request_id=request_id,
                    attack_id=attack_id,
                    details={"tool": tool_name},
                )
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,  # Not yet executed, just authorized
                blocked=False,
            )

        # Check 1: Is the tool in the allowlist?
        if tool_name not in self.allowed_tools:
            reason = f"Tool '{tool_name}' is not in the permitted tool set: {sorted(self.allowed_tools)}"
            if self.audit:
                self.audit.deny(
                    component="tool_policy",
                    event_type="tool_not_allowed",
                    reason=reason,
                    request_id=request_id,
                    attack_id=attack_id,
                    details={
                        "requested_tool": tool_name,
                        "allowed_tools": sorted(self.allowed_tools),
                        "reason_given": request.reason,
                    },
                )
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,
                simulation=True,
                blocked=True,
                block_reason=reason,
            )

        # Check 2: Is this a dangerous tool?
        try:
            action = ToolAction(tool_name)
        except ValueError:
            reason = f"Unknown tool action: {tool_name}"
            if self.audit:
                self.audit.deny(
                    component="tool_policy",
                    event_type="unknown_tool",
                    reason=reason,
                    request_id=request_id,
                    attack_id=attack_id,
                    details={"requested_tool": tool_name},
                )
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,
                blocked=True,
                block_reason=reason,
            )

        if action in DANGEROUS_ACTIONS and tool_name not in self.allowed_tools:
            reason = f"Dangerous tool '{tool_name}' requires explicit authorization"
            if self.audit:
                self.audit.deny(
                    component="tool_policy",
                    event_type="dangerous_tool_blocked",
                    reason=reason,
                    request_id=request_id,
                    attack_id=attack_id,
                    details={
                        "requested_tool": tool_name,
                        "danger_class": "DANGEROUS",
                    },
                )
            return ToolResult(
                tool=tool_name,
                arguments=request.arguments,
                executed=False,
                simulation=True,
                blocked=True,
                block_reason=reason,
            )

        # Authorized
        if self.audit:
            self.audit.allow(
                component="tool_policy",
                event_type="tool_authorized",
                reason=f"Tool '{tool_name}' is in the allowed set",
                request_id=request_id,
                attack_id=attack_id,
                details={"tool": tool_name},
            )

        return ToolResult(
            tool=tool_name,
            arguments=request.arguments,
            executed=False,
            blocked=False,
        )

"""
Tool registry — central catalog of all available tools.

Maps tool names to their implementations and provides the execution
entry point for authorized tool calls.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set

from app.agent.schemas import ToolAction, ToolResult
from app.security.audit import AuditLogger


class ToolRegistry:
    """Central registry for all tools (safe and dangerous-mock)."""

    def __init__(self, audit: Optional[AuditLogger] = None):
        self._tools: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
        self.audit = audit

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
    ) -> None:
        self._tools[name] = func
        self._descriptions[name] = description

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def get_descriptions(self, tools: Optional[Set[str]] = None) -> Dict[str, str]:
        if tools is None:
            return dict(self._descriptions)
        return {k: v for k, v in self._descriptions.items() if k in tools}

    def list_tools(self) -> List[str]:
        return sorted(self._tools.keys())

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool and return the result."""
        func = self._tools.get(tool_name)
        if func is None:
            return ToolResult(
                tool=tool_name,
                arguments=arguments,
                executed=False,
                blocked=True,
                block_reason=f"Tool '{tool_name}' not found in registry",
            )

        try:
            result = func(**arguments)
            if self.audit:
                self.audit.allow(
                    component="tool_registry",
                    event_type="tool_executed",
                    reason=f"Tool '{tool_name}' executed successfully",
                    request_id=request_id,
                    attack_id=attack_id,
                    details={"tool": tool_name, "arguments": arguments},
                )
            return ToolResult(
                tool=tool_name,
                arguments=arguments,
                executed=True,
                simulation=tool_name.startswith("mock_"),
                result=result,
            )
        except Exception as e:
            return ToolResult(
                tool=tool_name,
                arguments=arguments,
                executed=False,
                error=str(e),
            )

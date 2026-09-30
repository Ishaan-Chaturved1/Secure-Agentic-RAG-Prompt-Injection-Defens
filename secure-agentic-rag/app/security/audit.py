"""
Structured security audit logging.

Every security decision — allow, deny, warn — is logged as a JSONL record
so the red-team runner and evaluator can reconstruct exactly what happened.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agent.schemas import AuditEvent, SecurityDecision

logger = logging.getLogger("security.audit")


class AuditLogger:
    """Thread-safe JSONL audit logger."""

    def __init__(self, log_dir: Optional[Path] = None):
        self._lock = threading.Lock()
        self._events: List[AuditEvent] = []
        self._log_file: Optional[Path] = None

        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            self._log_file = log_dir / f"audit_{ts}.jsonl"

    def log(
        self,
        component: str,
        event_type: str,
        decision: SecurityDecision,
        reason: str = "",
        request_id: str = "",
        attack_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
            attack_id=attack_id,
            component=component,
            event_type=event_type,
            decision=decision,
            reason=reason,
            details=details or {},
        )

        with self._lock:
            self._events.append(event)

        # Persist to file
        if self._log_file:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(event.model_dump_json() + "\n")
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")

        # Also emit to Python logger
        log_level = {
            SecurityDecision.ALLOW: logging.DEBUG,
            SecurityDecision.WARN: logging.WARNING,
            SecurityDecision.DENY: logging.WARNING,
        }.get(decision, logging.INFO)

        logger.log(
            log_level,
            "[%s] %s | %s | %s | %s",
            decision.value,
            component,
            event_type,
            reason,
            json.dumps(details or {}),
        )

        return event

    def allow(self, component: str, event_type: str, **kwargs) -> AuditEvent:
        return self.log(component, event_type, SecurityDecision.ALLOW, **kwargs)

    def deny(self, component: str, event_type: str, **kwargs) -> AuditEvent:
        return self.log(component, event_type, SecurityDecision.DENY, **kwargs)

    def warn(self, component: str, event_type: str, **kwargs) -> AuditEvent:
        return self.log(component, event_type, SecurityDecision.WARN, **kwargs)

    @property
    def events(self) -> List[AuditEvent]:
        with self._lock:
            return list(self._events)

    def get_denied_events(self) -> List[AuditEvent]:
        with self._lock:
            return [e for e in self._events if e.decision == SecurityDecision.DENY]

    def get_events_for_request(self, request_id: str) -> List[AuditEvent]:
        with self._lock:
            return [e for e in self._events if e.request_id == request_id]

    def clear(self):
        with self._lock:
            self._events.clear()

    def export_jsonl(self) -> str:
        with self._lock:
            return "\n".join(e.model_dump_json() for e in self._events)


# Module-level singleton
_global_audit: Optional[AuditLogger] = None


def get_audit_logger(log_dir: Optional[Path] = None) -> AuditLogger:
    global _global_audit
    if _global_audit is None:
        _global_audit = AuditLogger(log_dir)
    return _global_audit


def reset_audit_logger(log_dir: Optional[Path] = None) -> AuditLogger:
    global _global_audit
    _global_audit = AuditLogger(log_dir)
    return _global_audit

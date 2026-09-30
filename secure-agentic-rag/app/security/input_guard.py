"""
Input guard — first security checkpoint in the hardened pipeline.

Scans user queries and retrieved documents for prompt-injection attempts
before they reach the LLM agent.
"""

from __future__ import annotations

from typing import List, Optional

from app.agent.schemas import InjectionResult, SecurityDecision
from app.security.audit import AuditLogger
from app.security.injection_detector import (
    CombinedInjectionDetector,
    InjectionDetector,
)


class InputGuard:
    """
    Filters inputs (user queries and retrieved documents) for injection.

    In the hardened pipeline, every piece of text that enters the LLM
    context is scanned here.
    """

    def __init__(
        self,
        detector: Optional[InjectionDetector] = None,
        audit: Optional[AuditLogger] = None,
        enabled: bool = True,
    ):
        self.detector = detector or CombinedInjectionDetector()
        self.audit = audit
        self.enabled = enabled

    def check_query(
        self,
        query: str,
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> InjectionResult:
        """Check user query for direct prompt injection."""
        if not self.enabled:
            return InjectionResult()

        result = self.detector.detect(query)

        if result.is_suspicious and self.audit:
            self.audit.deny(
                component="input_guard",
                event_type="direct_injection_detected",
                reason=result.reason,
                request_id=request_id,
                attack_id=attack_id,
                details={
                    "score": result.score,
                    "categories": result.categories,
                    "text_preview": query[:200],
                },
            )
        elif self.audit:
            self.audit.allow(
                component="input_guard",
                event_type="query_clean",
                request_id=request_id,
                attack_id=attack_id,
            )

        return result

    def check_document(
        self,
        document: str,
        document_id: str = "",
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> InjectionResult:
        """Check a retrieved document for indirect prompt injection."""
        if not self.enabled:
            return InjectionResult()

        result = self.detector.detect(document)

        if result.is_suspicious and self.audit:
            self.audit.warn(
                component="input_guard",
                event_type="indirect_injection_detected",
                reason=result.reason,
                request_id=request_id,
                attack_id=attack_id,
                details={
                    "document_id": document_id,
                    "score": result.score,
                    "categories": result.categories,
                    "text_preview": document[:200],
                },
            )

        return result

    def check_documents(
        self,
        documents: List[str],
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> List[InjectionResult]:
        """Check multiple retrieved documents, return results for each."""
        return [
            self.check_document(
                doc,
                document_id=f"doc_{i}",
                request_id=request_id,
                attack_id=attack_id,
            )
            for i, doc in enumerate(documents)
        ]

    def filter_documents(
        self,
        documents: List[str],
        request_id: str = "",
        attack_id: Optional[str] = None,
    ) -> List[str]:
        """Return only non-suspicious documents."""
        results = self.check_documents(documents, request_id, attack_id)
        return [
            doc
            for doc, result in zip(documents, results)
            if not result.is_suspicious
        ]

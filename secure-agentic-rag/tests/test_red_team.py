"""
Tests for red-team attack execution and evaluation.
"""

import json
import pytest
from pathlib import Path

from app.agent.agent import RAGAgent
from app.agent.schemas import AttackCase, AttackResult
from app.config import baseline_settings, hardened_settings
from app.security.audit import reset_audit_logger
from red_team.runner import load_attack_cases, run_single_attack
from evaluation.metrics import MetricsCalculator


@pytest.fixture
def attack_cases():
    return load_attack_cases()


@pytest.fixture
def baseline_agent():
    reset_audit_logger()
    return RAGAgent(baseline_settings(llm_backend="mock"))


@pytest.fixture
def hardened_agent():
    reset_audit_logger()
    return RAGAgent(hardened_settings(llm_backend="mock"))


class TestAttackCorpus:
    """Tests for the attack corpus integrity."""

    def test_attack_cases_loaded(self, attack_cases):
        assert len(attack_cases) >= 30

    def test_attack_cases_have_required_fields(self, attack_cases):
        for case in attack_cases:
            assert case.id
            assert case.category
            assert case.document
            assert case.expected_behavior in ("block", "allow")

    def test_attack_categories_coverage(self, attack_cases):
        categories = set(c.category for c in attack_cases)
        expected = {
            "direct_prompt_injection",
            "indirect_prompt_injection",
            "fake_system_message",
            "secret_extraction",
        }
        assert expected.issubset(categories)

    def test_unique_ids(self, attack_cases):
        ids = [c.id for c in attack_cases]
        assert len(ids) == len(set(ids))


class TestBaselineVulnerability:
    """Verify baseline is actually vulnerable."""

    def test_baseline_has_high_attack_success(self, baseline_agent, attack_cases):
        results = []
        for case in attack_cases[:10]:  # Test first 10 for speed
            result = run_single_attack(baseline_agent, case, "baseline")
            results.append(result)

        successful = sum(1 for r in results if r.attack_success or r.model_compromised)
        assert successful >= 3, f"Baseline should be vulnerable, but only {successful}/10 attacks succeeded"


class TestHardenedResistance:
    """Verify hardened blocks attacks."""

    def test_hardened_blocks_most_attacks(self, hardened_agent, attack_cases):
        results = []
        for case in attack_cases[:10]:
            result = run_single_attack(hardened_agent, case, "hardened")
            results.append(result)

        system_compromised = sum(1 for r in results if r.system_compromised)
        assert system_compromised == 0, f"Hardened should block all system compromises, but {system_compromised}/10 succeeded"


class TestMetrics:
    """Tests for metrics calculation."""

    def test_empty_results(self):
        calc = MetricsCalculator([], [])
        metrics = calc.compute_all()
        assert metrics["summary"]["total_attacks"] == 0

    def test_all_successful(self):
        results = [
            AttackResult(
                attack_id="T1", category="test", mode="test",
                attack_success=True, model_compromised=True,
                system_compromised=True,
            )
        ]
        calc = MetricsCalculator(results)
        metrics = calc.compute_all()
        assert metrics["summary"]["attack_success_rate"] == 1.0

    def test_none_successful(self):
        results = [
            AttackResult(
                attack_id="T1", category="test", mode="test",
                attack_success=False, model_compromised=False,
                system_compromised=False,
            )
        ]
        calc = MetricsCalculator(results)
        metrics = calc.compute_all()
        assert metrics["summary"]["attack_success_rate"] == 0.0


class TestSingleAttackEndpoint:
    """Tests for the POST /red-team/attack/{attack_id} endpoint."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_single_attack_endpoint_baseline(self, client):
        resp = client.post("/red-team/attack/DIR-002?mode=baseline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["attack_id"] == "DIR-002"
        assert data["mode"] == "baseline"
        assert len(data["attack_payload"]) > 0
        assert data["attack_success"] is True
        assert data["secret_leaked"] is True
        assert data["requested_tool"] == "mock_read_secret"
        assert data["tool_executed"] is True
        assert data["blocked"] is False

    def test_single_attack_endpoint_hardened(self, client):
        resp = client.post("/red-team/attack/DIR-002?mode=hardened")
        assert resp.status_code == 200
        data = resp.json()
        assert data["attack_id"] == "DIR-002"
        assert data["mode"] == "hardened"
        assert len(data["attack_payload"]) > 0
        assert data["blocked"] is True
        assert data["blocked_by"] is not None
        assert "Layer" in data["blocked_by"]
        assert data["secret_leaked"] is False
        assert data["system_compromised"] is False

    def test_single_attack_endpoint_invalid_id(self, client):
        resp = client.post("/red-team/attack/NON-EXISTENT-ID?mode=hardened")
        assert resp.status_code == 404

    def test_single_attack_endpoint_invalid_mode(self, client):
        resp = client.post("/red-team/attack/DIR-002?mode=unsupported_mode")
        assert resp.status_code == 400


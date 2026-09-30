"""
Evaluator — runs attacks against both configurations and produces results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agent.schemas import AttackResult, BenignTestResult
from evaluation.metrics import MetricsCalculator


class Evaluator:
    """Evaluates red-team results and produces comparison reports."""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or Path("evaluation")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def save_results(
        self,
        results: List[AttackResult],
        filename: str,
    ) -> Path:
        """Save attack results to JSON."""
        path = self.results_dir / filename
        data = [r.model_dump() for r in results]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def save_benign_results(
        self,
        results: List[BenignTestResult],
        filename: str,
    ) -> Path:
        """Save benign test results to JSON."""
        path = self.results_dir / filename
        data = [r.model_dump() for r in results]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def load_results(self, filename: str) -> List[AttackResult]:
        """Load attack results from JSON."""
        path = self.results_dir / filename
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [AttackResult(**item) for item in data]

    def load_benign_results(self, filename: str) -> List[BenignTestResult]:
        """Load benign results from JSON."""
        path = self.results_dir / filename
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [BenignTestResult(**item) for item in data]

    def compare(
        self,
        baseline_results: List[AttackResult],
        hardened_results: List[AttackResult],
        baseline_benign: Optional[List[BenignTestResult]] = None,
        hardened_benign: Optional[List[BenignTestResult]] = None,
    ) -> Dict[str, Any]:
        """Compare baseline vs hardened metrics."""
        baseline_calc = MetricsCalculator(baseline_results, baseline_benign)
        hardened_calc = MetricsCalculator(hardened_results, hardened_benign)

        return {
            "baseline": baseline_calc.compute_all(),
            "hardened": hardened_calc.compute_all(),
            "improvement": self._compute_improvement(
                baseline_calc.compute_all()["summary"],
                hardened_calc.compute_all()["summary"],
            ),
        }

    def _compute_improvement(
        self,
        baseline: Dict[str, Any],
        hardened: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute improvement percentages."""
        improvements = {}

        for key in ["attack_success_rate", "unauthorized_tool_attempt_rate", "secret_leakage_rate"]:
            b_val = baseline.get(key, 0)
            h_val = hardened.get(key, 0)
            if b_val > 0:
                reduction = (b_val - h_val) / b_val
                improvements[f"{key}_reduction"] = round(reduction, 4)
            else:
                improvements[f"{key}_reduction"] = 0.0

        b_block = baseline.get("tool_block_rate", 0)
        h_block = hardened.get("tool_block_rate", 0)
        improvements["tool_block_rate_improvement"] = round(h_block - b_block, 4)

        return improvements

    def generate_comparison_table(self, comparison: Dict[str, Any]) -> str:
        """Generate a markdown comparison table."""
        b = comparison["baseline"]["summary"]
        h = comparison["hardened"]["summary"]

        rows = [
            "| Metric | Baseline | Hardened |",
            "|--------|----------|---------|",
            f"| Total Attacks | {b.get('total_attacks', 0)} | {h.get('total_attacks', 0)} |",
            f"| Attack Success Rate | {b.get('attack_success_rate', 0):.1%} | {h.get('attack_success_rate', 0):.1%} |",
            f"| Model Compromise Rate | {b.get('model_compromise_rate', 0):.1%} | {h.get('model_compromise_rate', 0):.1%} |",
            f"| System Compromise Rate | {b.get('system_compromise_rate', 0):.1%} | {h.get('system_compromise_rate', 0):.1%} |",
            f"| Unauthorized Tool Attempts | {b.get('unauthorized_tool_attempts', 0)} | {h.get('unauthorized_tool_attempts', 0)} |",
            f"| Tool Block Rate | {b.get('tool_block_rate', 0):.1%} | {h.get('tool_block_rate', 0):.1%} |",
            f"| Secret Leakage Rate | {b.get('secret_leakage_rate', 0):.1%} | {h.get('secret_leakage_rate', 0):.1%} |",
        ]

        # Benign metrics
        bb = comparison["baseline"].get("benign", {})
        hb = comparison["hardened"].get("benign", {})
        if bb.get("total_benign", 0) > 0:
            rows.extend([
                f"| Benign Success Rate | {bb.get('benign_success_rate', 0):.1%} | {hb.get('benign_success_rate', 0):.1%} |",
                f"| False Positive Rate | {bb.get('false_positive_rate', 0):.1%} | {hb.get('false_positive_rate', 0):.1%} |",
            ])

        return "\n".join(rows)

    def generate_category_table(self, comparison: Dict[str, Any]) -> str:
        """Generate a per-category comparison table."""
        b_cats = comparison["baseline"].get("by_category", {})
        h_cats = comparison["hardened"].get("by_category", {})

        all_cats = sorted(set(list(b_cats.keys()) + list(h_cats.keys())))

        rows = [
            "| Category | Baseline Success | Hardened Success | Baseline Secret Leak | Hardened Secret Leak |",
            "|----------|-----------------|-----------------|---------------------|---------------------|",
        ]

        for cat in all_cats:
            b = b_cats.get(cat, {})
            h = h_cats.get(cat, {})
            rows.append(
                f"| {cat} | "
                f"{b.get('success_rate', 0):.1%} ({b.get('successful', 0)}/{b.get('total', 0)}) | "
                f"{h.get('success_rate', 0):.1%} ({h.get('successful', 0)}/{h.get('total', 0)}) | "
                f"{b.get('secret_leaked', 0)} | "
                f"{h.get('secret_leaked', 0)} |"
            )

        return "\n".join(rows)

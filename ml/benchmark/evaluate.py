import json
import os
import sys
import time
from typing import Dict, Any, List

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ml.retrieval.retriever import LegalRetriever
from ml.rules.engine import DeterministicRuleEngine
from ml.aggregation.scoring import ForecastAggregator
from ml.uncertainty.priority import UncertaintyPrioritizer

class BenchmarkRunner:
    """
    Executes benchmark evaluations comparing Baselines A, B, C and Verdion (§18.1, §18.3).
    Evaluates on 20 scenarios with 14 train / 6 held-out test splits.
    """

    def __init__(self, scenarios_path: str = None):
        if scenarios_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            scenarios_path = os.path.join(base_dir, "scenarios.json")
        with open(scenarios_path, "r", encoding="utf-8") as f:
            self.scenarios = json.load(f)
        self.retriever = LegalRetriever()

    def run_baseline_a(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Baseline A: Single-agent RAG (No multi-agent debate, no rules, no incentives)."""
        raise NotImplementedError("Hardcoded benchmark mock logic quarantined; live pipeline rewrite pending.")

    def run_baseline_b(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Baseline B: Basic multi-agent (Specialized agents, no deterministic rules, no market/bounties)."""
        raise NotImplementedError("Hardcoded benchmark mock logic quarantined; live pipeline rewrite pending.")

    def run_baseline_c(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Baseline C: Hybrid without incentives (Agents + Deterministic rule engine, but no markets/bounties)."""
        raise NotImplementedError("Hardcoded benchmark mock logic quarantined; live pipeline rewrite pending.")

    def run_verdion_pipeline(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verdion Full Pipeline:
        Agents + Deterministic Rule Engine + Commit-Reveal Market + Uncertainty Prioritization & Bounties.
        """
        raise NotImplementedError("Hardcoded benchmark mock logic quarantined; live pipeline rewrite pending.")

    def evaluate_all(self) -> Dict[str, Any]:
        """Runs evaluation over all 20 scenarios, breaking down train vs held-out test splits."""
        results = {
            "metadata": {
                "total_scenarios": len(self.scenarios),
                "train_count": sum(1 for s in self.scenarios if s["split"] == "train"),
                "held_out_count": sum(1 for s in self.scenarios if s["split"] == "held_out"),
                "evaluated_at": "2026-03-15T12:00:00Z"
            },
            "metrics": {
                "Baseline_A_Single_RAG": {"brier_all": 0.0, "brier_held_out": 0.0, "unsupported_claim_rate": 0.0, "f1_score": 0.0},
                "Baseline_B_Multi_Agent": {"brier_all": 0.0, "brier_held_out": 0.0, "unsupported_claim_rate": 0.0, "f1_score": 0.0},
                "Baseline_C_Hybrid_No_Incentives": {"brier_all": 0.0, "brier_held_out": 0.0, "unsupported_claim_rate": 0.0, "f1_score": 0.0},
                "Verdion_Full_Pipeline": {"brier_all": 0.0, "brier_held_out": 0.0, "unsupported_claim_rate": 0.0, "f1_score": 0.0}
            },
            "scenario_details": []
        }

        pipelines = [
            ("Baseline_A_Single_RAG", self.run_baseline_a),
            ("Baseline_B_Multi_Agent", self.run_baseline_b),
            ("Baseline_C_Hybrid_No_Incentives", self.run_baseline_c),
            ("Verdion_Full_Pipeline", self.run_verdion_pipeline)
        ]

        for pipe_name, runner_fn in pipelines:
            all_probs = []
            all_labels = []
            held_probs = []
            held_labels = []
            unsupported_rates = []
            tp = fp = fn = tn = 0

            for s in self.scenarios:
                out = runner_fn(s)
                y = s["ground_truth_label"]
                prob = out["predicted_prob"]
                
                all_probs.append(prob)
                all_labels.append(y)
                unsupported_rates.append(out["unsupported_claim_rate"])

                pred_binary = 1 if prob >= 0.5 else 0
                if pred_binary == 1 and y == 1:
                    tp += 1
                elif pred_binary == 1 and y == 0:
                    fp += 1
                elif pred_binary == 0 and y == 1:
                    fn += 1
                else:
                    tn += 1

                if s["split"] == "held_out":
                    held_probs.append(prob)
                    held_labels.append(y)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            results["metrics"][pipe_name]["brier_all"] = ForecastAggregator.compute_brier_score(all_probs, all_labels)
            results["metrics"][pipe_name]["brier_held_out"] = ForecastAggregator.compute_brier_score(held_probs, held_labels)
            results["metrics"][pipe_name]["unsupported_claim_rate"] = round(sum(unsupported_rates) / len(unsupported_rates), 4)
            results["metrics"][pipe_name]["f1_score"] = round(f1, 4)

        return results

if __name__ == "__main__":
    runner = BenchmarkRunner()
    eval_results = runner.evaluate_all()
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)
    print("Benchmark evaluation completed. Results written to results.json")
    print(json.dumps(eval_results["metrics"], indent=2))

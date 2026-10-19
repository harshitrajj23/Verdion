from typing import List, Dict, Any, Tuple
import math

class ForecastAggregator:
    """
    Implements forecast aggregation (§9.2), disagreement variance (§9.3),
    and Brier scoring calculations (§9.5, FR-048).
    """

    @staticmethod
    def aggregate_unweighted_mean(probabilities: List[float]) -> float:
        """Computes unweighted arithmetic mean p_aggregate = sum(p_i) / N (§9.2)."""
        if not probabilities:
            raise ValueError("Probability list cannot be empty")
        for p in probabilities:
            if not (0.0 <= p <= 1.0):
                raise ValueError(f"Probability {p} is outside valid range [0, 1]")
        return round(sum(probabilities) / len(probabilities), 4)

    @staticmethod
    def compute_disagreement_variance(probabilities: List[float]) -> float:
        """
        Computes disagreement metric as variance:
        D = (1/N) * sum((p_i - mean(p))^2) (§9.3)
        """
        if len(probabilities) < 2:
            return 0.0
        mean_p = sum(probabilities) / len(probabilities)
        variance = sum((p - mean_p) ** 2 for p in probabilities) / len(probabilities)
        return round(variance, 6)

    @staticmethod
    def compute_brier_score(probabilities: List[float], outcomes: List[int]) -> float:
        """
        Computes Brier score:
        BS = (1/N) * sum((p_i - y_i)^2), y_i in {0, 1} (§9.5)
        Lower is better (0.0 = perfect accuracy, 1.0 = worst).
        """
        if len(probabilities) != len(outcomes):
            raise ValueError("Lengths of probabilities and outcomes must match")
        if not probabilities:
            raise ValueError("Input lists cannot be empty")

        squared_errors = []
        for p, y in zip(probabilities, outcomes):
            if y not in (0, 1):
                raise ValueError(f"Outcome {y} must be binary (0 or 1)")
            squared_errors.append((p - y) ** 2)

        return round(sum(squared_errors) / len(squared_errors), 4)

    @classmethod
    def evaluate_market_forecasts(
        cls,
        agent_forecasts: List[Dict[str, Any]],
        ground_truth: int
    ) -> Dict[str, Any]:
        """
        Computes aggregate metrics, individual Brier scores, and disagreement metrics.
        """
        probs = [f["probability"] for f in agent_forecasts]
        p_agg = cls.aggregate_unweighted_mean(probs)
        disagreement = cls.compute_disagreement_variance(probs)
        overall_brier = cls.compute_brier_score(probs, [ground_truth] * len(probs))

        agent_results = []
        for f in agent_forecasts:
            p = f["probability"]
            individual_bs = round((p - ground_truth) ** 2, 4)
            agent_results.append({
                "agent_id": f.get("agent_id"),
                "probability": p,
                "brier_score": individual_bs,
                "credits_earned": round(max(0.0, 100.0 * (1.0 - individual_bs)), 2)
            })

        return {
            "sample_size": len(probs),
            "aggregate_probability": p_agg,
            "disagreement_variance": disagreement,
            "disagreement_level": "HIGH" if disagreement > 0.02 else "LOW",
            "overall_brier_score": overall_brier,
            "agent_evaluations": agent_results
        }

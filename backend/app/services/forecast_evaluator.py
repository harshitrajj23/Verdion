import math
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.entities import Agent, Forecast, PredictionMarket, Settlement


class ForecastEvaluator:
    """
    Empirical forecasting evaluation and calibration benchmark for VERIDION Option C.
    Computes rigorous metrics:
    - Brier score
    - Binary log loss (cross-entropy) with epsilon clipping
    - Expected Calibration Error (ECE) across probability bins
    - Reliability diagrams / calibration curves by bin
    - Forecaster rankings vs baselines (uniform 0.5, random, historical base rate)
    - Sample size adequacy disclosures
    """

    @staticmethod
    def compute_brier_score(predictions: List[float], outcomes: List[int]) -> float:
        """
        Computes Mean Squared Error Brier Score: (1/N) * sum((p_i - y_i)^2)
        Normalized in range [0.0, 1.0], rounded deterministically to 6 decimal places.
        """
        if not predictions or len(predictions) != len(outcomes):
            return 0.250000
        return round(sum((p - y) ** 2 for p, y in zip(predictions, outcomes)) / len(predictions), 6)

    @staticmethod
    def compute_log_loss(predictions: List[float], outcomes: List[int], eps: float = 1e-6) -> float:
        """
        Computes Binary Cross-Entropy Log Loss with epsilon clipping [1e-6, 1 - 1e-6].
        Rounded deterministically to 6 decimal places.
        """
        if not predictions or len(predictions) != len(outcomes):
            return 0.693147  # -ln(0.5)
        total_loss = 0.0
        for p, y in zip(predictions, outcomes):
            p_clipped = max(eps, min(1.0 - eps, p))
            if y == 1:
                total_loss += -math.log(p_clipped)
            else:
                total_loss += -math.log(1.0 - p_clipped)
        return round(total_loss / len(predictions), 6)

    @staticmethod
    def compute_calibration_bins(
        predictions: List[float],
        outcomes: List[int],
        num_bins: int = 5
    ) -> Dict[str, Any]:
        """
        Partitions forecasts into bins (e.g. 0-0.2, 0.2-0.4, etc.)
        and computes observed frequency vs mean forecast for each bin, along with ECE.
        """
        if not predictions or len(predictions) != len(outcomes):
            predictions = []
            outcomes = []

        bins = []
        bin_width = 1.0 / num_bins
        total_samples = len(predictions)
        ece = 0.0

        for b in range(num_bins):
            bin_lower = b * bin_width
            bin_upper = (b + 1) * bin_width
            # Items falling into bin [lower, upper) or [lower, upper] for last bin
            bin_indices = [
                i for i, p in enumerate(predictions)
                if (bin_lower <= p < bin_upper) or (b == num_bins - 1 and p == 1.0)
            ]

            bin_count = len(bin_indices)
            if bin_count > 0:
                bin_preds = [predictions[i] for i in bin_indices]
                bin_outs = [outcomes[i] for i in bin_indices]
                mean_pred = sum(bin_preds) / bin_count
                empirical_freq = sum(bin_outs) / bin_count
                bin_abs_error = abs(empirical_freq - mean_pred)
                ece += (bin_count / total_samples) * bin_abs_error
            else:
                mean_pred = round((bin_lower + bin_upper) / 2.0, 2)
                empirical_freq = 0.0
                bin_abs_error = 0.0

            bins.append({
                "bin_range": f"{int(bin_lower*100)}%-{int(bin_upper*100)}%",
                "count": bin_count,
                "mean_predicted_probability": round(mean_pred, 4),
                "observed_frequency": round(empirical_freq, 4),
                "calibration_gap": round(bin_abs_error, 4)
            })

        return {
            "bins": bins,
            "expected_calibration_error": round(ece, 4)
        }

    @staticmethod
    async def evaluate_protocol_forecasting(db: AsyncSession) -> Dict[str, Any]:
        """
        Gathers all resolved prediction markets and revealed forecasts across the database.
        Produces macro protocol-wide forecasting benchmark metrics.
        """
        # Fetch all markets
        stmt_markets = select(PredictionMarket)
        res_markets = await db.execute(stmt_markets)
        markets = res_markets.scalars().all()

        total_markets = len(markets)
        resolved_markets = [m for m in markets if m.status in ("SETTLED", "RESOLUTION_PROPOSED") and m.proposed_outcome is not None]
        unresolved_markets = [m for m in markets if m.status not in ("SETTLED", "RESOLUTION_PROPOSED") or m.proposed_outcome is None]

        # Map market outcomes
        market_outcomes = {m.id: m.proposed_outcome for m in resolved_markets}

        # Fetch forecasts
        stmt_fcs = select(Forecast).where(Forecast.reveal_status == "REVEALED")
        res_fcs = await db.execute(stmt_fcs)
        all_revealed_fcs = res_fcs.scalars().all()

        evaluated_preds = []
        evaluated_outs = []
        agent_metrics: Dict[str, Dict[str, Any]] = {}

        for fc in all_revealed_fcs:
            if fc.market_id in market_outcomes and fc.probability is not None:
                outcome = market_outcomes[fc.market_id]
                evaluated_preds.append(fc.probability)
                evaluated_outs.append(outcome)

                # Track per agent
                if fc.agent_id not in agent_metrics:
                    agent_metrics[fc.agent_id] = {"predictions": [], "outcomes": []}
                agent_metrics[fc.agent_id]["predictions"].append(fc.probability)
                agent_metrics[fc.agent_id]["outcomes"].append(outcome)

        total_resolved_forecasts = len(evaluated_preds)
        base_rate = sum(evaluated_outs) / total_resolved_forecasts if total_resolved_forecasts > 0 else 0.5

        # Compute protocol metrics
        protocol_brier = ForecastEvaluator.compute_brier_score(evaluated_preds, evaluated_outs)
        protocol_log_loss = ForecastEvaluator.compute_log_loss(evaluated_preds, evaluated_outs)
        cal_data = ForecastEvaluator.compute_calibration_bins(evaluated_preds, evaluated_outs, num_bins=5)

        # Baseline comparisons
        uniform_baseline_preds = [0.5] * len(evaluated_outs)
        base_rate_preds = [base_rate] * len(evaluated_outs)
        uniform_brier = ForecastEvaluator.compute_brier_score(uniform_baseline_preds, evaluated_outs)
        base_rate_brier = ForecastEvaluator.compute_brier_score(base_rate_preds, evaluated_outs)

        # Per-agent summary
        forecaster_leaderboard = []
        for ag_id, data in agent_metrics.items():
            ag_obj = await db.get(Agent, ag_id)
            ag_brier = ForecastEvaluator.compute_brier_score(data["predictions"], data["outcomes"])
            ag_cal = ForecastEvaluator.compute_calibration_bins(data["predictions"], data["outcomes"], num_bins=3)
            forecaster_leaderboard.append({
                "agent_id": ag_id,
                "role": ag_obj.role if ag_obj else "FORECASTER",
                "sample_size": len(data["predictions"]),
                "brier_score": ag_brier,
                "expected_calibration_error": ag_cal["expected_calibration_error"],
                "reputation_score": ag_obj.reputation_score if ag_obj else 100.0
            })

        forecaster_leaderboard.sort(key=lambda x: x["brier_score"])

        # Statistical caveat disclosure
        sample_size_disclosure = (
            f"Evaluated {total_resolved_forecasts} resolved forecasts across {len(resolved_markets)} resolved markets. "
            f"Samples below N=50 provide preliminary directional calibration and should not be interpreted as asymptotic statistical convergence."
        )

        return {
            "total_markets_created": total_markets,
            "resolved_markets_count": len(resolved_markets),
            "unresolved_markets_count": len(unresolved_markets),
            "market_resolution_rate": round(len(resolved_markets) / total_markets, 4) if total_markets > 0 else 0.0,
            "total_resolved_forecasts": total_resolved_forecasts,
            "historical_base_rate": round(base_rate, 4),
            "protocol_metrics": {
                "brier_score": protocol_brier,
                "log_loss": protocol_log_loss,
                "expected_calibration_error": cal_data["expected_calibration_error"],
                "scoring_rule": "Proper Quadratic Brier Rule (PRD 9.5)"
            },
            "baseline_comparisons": {
                "veridion_protocol_brier": protocol_brier,
                "uniform_prior_brier": uniform_brier,
                "base_rate_brier": base_rate_brier,
                "random_expectation_brier": 0.3333,
                "improvement_over_uniform": round(uniform_brier - protocol_brier, 4)
            },
            "calibration_curve": cal_data["bins"],
            "forecaster_leaderboard": forecaster_leaderboard,
            "statistical_disclosure": sample_size_disclosure
        }

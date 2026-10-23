import unittest
from ml.benchmark.discrimination_check import (
    compute_discrimination_metrics,
    compute_bootstrap_ci,
)


class TestDiscriminationAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        # Small synthetic fixture (not real benchmark results)
        self.synthetic_fixture = [
            {
                "scenario_id": "synth_01",
                "ground_truth_label": 1,
                "constant_0_65": {"probability": 0.65, "brier": 0.1225},
                "base_rate": {"probability": 0.5, "brier": 0.25},
                "live_forecaster": {"probability": 0.80, "brier": 0.04},
            },
            {
                "scenario_id": "synth_02",
                "ground_truth_label": 1,
                "constant_0_65": {"probability": 0.65, "brier": 0.1225},
                "base_rate": {"probability": 0.5, "brier": 0.25},
                "live_forecaster": {"probability": 0.60, "brier": 0.16},
            },
            {
                "scenario_id": "synth_03",
                "ground_truth_label": 0,
                "constant_0_65": {"probability": 0.65, "brier": 0.4225},
                "base_rate": {"probability": 0.5, "brier": 0.25},
                "live_forecaster": {"probability": 0.30, "brier": 0.09},
            },
            {
                "scenario_id": "synth_04",
                "ground_truth_label": 0,
                "constant_0_65": {"probability": 0.65, "brier": 0.4225},
                "base_rate": {"probability": 0.5, "brier": 0.25},
                "live_forecaster": {"probability": 0.10, "brier": 0.01},
            },
        ]

    def test_separation_on_known_fixture(self) -> None:
        # pos mean = (0.8 + 0.6) / 2 = 0.70
        # neg mean = (0.3 + 0.1) / 2 = 0.20
        # separation = 0.70 - 0.20 = 0.50
        metrics = compute_discrimination_metrics(self.synthetic_fixture)
        self.assertEqual(metrics["mean_p_pos"], 0.70)
        self.assertEqual(metrics["mean_p_neg"], 0.20)
        self.assertEqual(metrics["separation"], 0.50)
        self.assertEqual(metrics["distinct_p_count"], 4)

    def test_bootstrap_reproducibility_with_seed(self) -> None:
        # Assert bootstrap is 100% reproducible with fixed seed
        ci1 = compute_bootstrap_ci(self.synthetic_fixture, n_resamples=1000, seed=20261019)
        ci2 = compute_bootstrap_ci(self.synthetic_fixture, n_resamples=1000, seed=20261019)
        self.assertEqual(ci1, ci2)

    def test_constant_output_gives_one_distinct_value(self) -> None:
        constant_fixture = [
            {
                "scenario_id": f"const_{i}",
                "ground_truth_label": i % 2,
                "constant_0_65": {"probability": 0.65, "brier": 0.2},
                "base_rate": {"probability": 0.5, "brier": 0.25},
                "live_forecaster": {"probability": 0.50, "brier": 0.25},
            }
            for i in range(4)
        ]
        metrics = compute_discrimination_metrics(constant_fixture)
        self.assertEqual(metrics["distinct_p_count"], 1)
        self.assertEqual(metrics["distinct_forecast_values"], [0.50])
        self.assertEqual(metrics["separation"], 0.0)


if __name__ == "__main__":
    unittest.main()

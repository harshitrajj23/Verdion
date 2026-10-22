from __future__ import annotations

import unittest

from ml.aggregation.scoring import aggregate_mean, brier, population_variance


class TestAggregationAndScoring(unittest.TestCase):
    def test_example_forecasts_mean_and_variance(self) -> None:
        probs = [0.8, 0.65, 0.45]
        self.assertEqual(aggregate_mean(probs), 0.6333)
        self.assertEqual(population_variance(probs), 0.0206)

    def test_brier_exact_values(self) -> None:
        self.assertEqual(brier(0.8, 1), 0.04)
        self.assertEqual(brier(0.3, 0), 0.09)

    def test_brier_out_of_range_p_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            brier(1.05, 1)
        with self.assertRaises(ValueError):
            brier(-0.01, 0)
        with self.assertRaises(ValueError):
            brier(1.5, 0)

    def test_brier_invalid_y_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            brier(0.5, 2)
        with self.assertRaises(ValueError):
            brier(0.5, -1)
        with self.assertRaises(ValueError):
            brier(0.5, True)  # bool should not be accepted as binary int

    def test_aggregate_mean_validation(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_mean([])
        with self.assertRaises(ValueError):
            aggregate_mean([0.5, 1.2])
        with self.assertRaises(ValueError):
            aggregate_mean([-0.1, 0.4])

    def test_population_variance_validation(self) -> None:
        with self.assertRaises(ValueError):
            population_variance([])
        with self.assertRaises(ValueError):
            population_variance([0.5, 1.2])
        self.assertEqual(population_variance([0.5]), 0.0)


if __name__ == "__main__":
    unittest.main()

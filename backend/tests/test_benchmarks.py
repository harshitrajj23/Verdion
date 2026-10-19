import pytest
from backend.app.services.evaluation_service import EvaluationService


def test_20_scenarios_loaded():
    scenarios = EvaluationService.load_benchmark_scenarios()
    assert len(scenarios) == 20
    for s in scenarios:
        assert s.id.startswith("scen_")
        assert s.jurisdiction in ["EU", "California"]
        assert s.ground_truth_gap_outcome in [0, 1]


def test_benchmark_comparative_evaluation():
    summary = EvaluationService.evaluate_all()
    assert summary.total_scenarios == 20
    assert "BASELINE_A_SINGLE_AGENT" in summary.metrics
    assert "BASELINE_B_MULTI_AGENT" in summary.metrics
    assert "VERIDION_PROTOCOL" in summary.metrics

    metrics_a = summary.metrics["BASELINE_A_SINGLE_AGENT"]
    metrics_b = summary.metrics["BASELINE_B_MULTI_AGENT"]
    metrics_v = summary.metrics["VERIDION_PROTOCOL"]

    # VERIDION Protocol demonstrates superior issue recall and lower Brier score error
    assert metrics_v["avg_issue_recall"] >= metrics_a["avg_issue_recall"]
    assert metrics_v["avg_brier_score"] <= metrics_a["avg_brier_score"]
    assert metrics_v["avg_citation_validity"] > metrics_a["avg_citation_validity"]

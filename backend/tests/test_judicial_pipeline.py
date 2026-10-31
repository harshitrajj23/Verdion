"""
Tests for Judicial Ground Truth Pipeline (GAP-002, GAP-003, GAP-007)
Validates retrospective dataset integrity, prospective outcome monitoring,
and temporal cutoff anti-leakage rules.
"""

import pytest
from backend.app.services.judicial_pipeline import (
    CaseResolutionStatus,
    DatasetPopulation,
    HistoricalCJEUCorpus,
    ProspectiveOutcomeMonitor,
    ProspectiveResolutionEvidence,
    RetrospectiveCaseEntry,
)


def test_retrospective_corpus_completeness_and_integrity():
    """
    Verifies that the retrospective dataset contains 10 landmark CJEU cases
    with valid ECLIs, SHA-256 digests, and strict RETROSPECTIVE labels.
    """
    corpus = HistoricalCJEUCorpus.get_corpus()
    assert len(corpus) == 10

    eclis = set()
    for case in corpus:
        assert isinstance(case, RetrospectiveCaseEntry)
        assert case.population == DatasetPopulation.RETROSPECTIVE_HISTORICAL.value
        assert ProspectiveOutcomeMonitor.validate_ecli(case.ecli)
        assert len(case.source_digest_sha256) == 64
        assert case.binary_outcome in (0, 1)
        assert case.official_url.startswith("https://curia.europa.eu")
        assert len(case.regulatory_provisions) > 0
        eclis.add(case.ecli)

    # All ECLIs must be unique
    assert len(eclis) == 10


def test_temporal_cutoff_prevents_future_leakage():
    """
    Verifies PRD anti-leakage rule:
    Forecasts submitted after freeze time are rejected.
    """
    freeze_time = "2024-05-01T12:00:00Z"

    # Valid: commit occurs before freeze
    valid_commit = "2024-05-01T11:59:59Z"
    assert ProspectiveOutcomeMonitor.check_temporal_cutoff(valid_commit, freeze_time) is True

    # Invalid: commit occurs after freeze
    late_commit = "2024-05-01T12:00:01Z"
    assert ProspectiveOutcomeMonitor.check_temporal_cutoff(late_commit, freeze_time) is False


def test_prospective_resolution_with_authoritative_evidence():
    """
    Verifies that prospective resolution succeeds only with verified dispositive judgment.
    """
    evidence = ProspectiveResolutionEvidence(
        ecli="ECLI:EU:C:2024:999",
        curia_press_release_ref="PR_2024_089",
        official_curia_judgment_url="https://curia.europa.eu/juris/document/document.jsf?docid=999999",
        judgment_text_sha256="a"*64,
        publication_date="2024-06-01T09:30:00Z",
        operative_part_verbatim="The Court hereby rules that...",
        resolution_status=CaseResolutionStatus.RESOLVED_AFFIRMATIVE,
        resolution_officer_or_oracle="0xAuthorizedEvaluator",
        verified_at="2024-06-01T10:00:00Z"
    )

    res = ProspectiveOutcomeMonitor.evaluate_prospective_resolution(
        market_id="mkt_live_cjeu_001",
        freeze_timestamp="2024-05-01T12:00:00Z",
        resolution_evidence=evidence
    )

    assert res["can_settle"] is True
    assert res["ground_truth_outcome"] == 1
    assert res["audit_payload"]["event_type"] == "MARKET_RESOLVED_AUTHORITATIVE"
    assert res["audit_payload"]["ecli"] == "ECLI:EU:C:2024:999"


def test_prospective_resolution_rejects_stayed_or_disputed():
    """
    Verifies that non-final cases (STAYED, DISPUTED) cannot trigger settlement.
    """
    stayed_evidence = ProspectiveResolutionEvidence(
        ecli="ECLI:EU:C:2024:888",
        curia_press_release_ref=None,
        official_curia_judgment_url="https://curia.europa.eu/juris/document/document.jsf?docid=888888",
        judgment_text_sha256="b"*64,
        publication_date="2024-06-01T09:30:00Z",
        operative_part_verbatim="Proceedings are stayed...",
        resolution_status=CaseResolutionStatus.STAYED,
        resolution_officer_or_oracle="0xAuthorizedEvaluator",
        verified_at="2024-06-01T10:00:00Z"
    )

    res = ProspectiveOutcomeMonitor.evaluate_prospective_resolution(
        market_id="mkt_live_stayed",
        freeze_timestamp="2024-05-01T12:00:00Z",
        resolution_evidence=stayed_evidence
    )

    assert res["can_settle"] is False
    assert "not a final dispositive judgment" in res["reason"]


def test_temporal_sequence_violation_raises():
    """
    Verifies that a judgment dated before market freeze raises a ValueError.
    """
    anachronistic_evidence = ProspectiveResolutionEvidence(
        ecli="ECLI:EU:C:2024:777",
        curia_press_release_ref=None,
        official_curia_judgment_url="https://curia.europa.eu/juris/document/document.jsf?docid=777777",
        judgment_text_sha256="c"*64,
        publication_date="2024-04-01T09:30:00Z",  # Prior to freeze!
        operative_part_verbatim="Ruling...",
        resolution_status=CaseResolutionStatus.RESOLVED_NEGATIVE,
        resolution_officer_or_oracle="0xAuthorizedEvaluator",
        verified_at="2024-04-01T10:00:00Z"
    )

    with pytest.raises(ValueError, match="Temporal sequence violation"):
        ProspectiveOutcomeMonitor.evaluate_prospective_resolution(
            market_id="mkt_retro_error",
            freeze_timestamp="2024-05-01T12:00:00Z",
            resolution_evidence=anachronistic_evidence
        )


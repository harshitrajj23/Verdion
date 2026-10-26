import pytest
from backend.app.core.crypto import (
    canonical_json,
    compute_brier_score,
    compute_commitment_hash,
    compute_sha256_digest,
    compute_uncertainty_priority,
    compute_variance,
    generate_nonce,
    verify_commitment_hash,
)


def test_sha256_canonical_digest():
    d1 = {"b": 2, "a": 1, "nested": {"y": "val", "x": 10}}
    d2 = {"a": 1, "nested": {"x": 10, "y": "val"}, "b": 2}
    # Deterministic canonical serialization must yield identical digests
    digest1 = compute_sha256_digest(d1)
    digest2 = compute_sha256_digest(d2)
    assert digest1 == digest2
    assert digest1.startswith("0x")
    assert len(digest1) == 66


def test_commitment_hash_verification():
    chain_id = 11155111
    market_id = "mkt_test_123"
    agent_id = "agent_legal_researcher"
    prob = 0.85
    digest = "0x" + "a" * 64
    nonce = generate_nonce()

    c_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce
    )
    assert c_hash.startswith("0x")
    assert len(c_hash) == 66

    # Valid reveal passes
    assert verify_commitment_hash(
        expected_hash=c_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce
    ) is True

    # Altered probability fails
    assert verify_commitment_hash(
        expected_hash=c_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=0.84,
        evidence_digest=digest,
        nonce=nonce
    ) is False

    # Altered nonce fails
    assert verify_commitment_hash(
        expected_hash=c_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=digest,
        nonce=generate_nonce()
    ) is False


def test_brier_score_calculation():
    # Perfect predictions: p=1 when y=1, p=0 when y=0 -> BS = 0.0
    assert compute_brier_score([1.0, 0.0], [1, 0]) == 0.0

    # Completely wrong predictions: p=0 when y=1, p=1 when y=0 -> BS = 1.0
    assert compute_brier_score([0.0, 1.0], [1, 0]) == 1.0

    # Intermediate test: p=0.8, y=1 -> (0.8-1)^2 = 0.04
    assert compute_brier_score([0.8], [1]) == 0.04


def test_variance_disagreement():
    # Uniform predictions -> variance = 0
    assert compute_variance([0.7, 0.7, 0.7]) == 0.0

    # Disagreement: [0.2, 0.8] -> mean = 0.5 -> ((0.2-0.5)^2 + (0.8-0.5)^2)/2 = (0.09 + 0.09)/2 = 0.09
    assert round(compute_variance([0.2, 0.8]), 4) == 0.09


def test_uncertainty_priority():
    # Priority(q) = Impact(q) * Uncertainty(q) * ResearchFeasibility(q)
    assert compute_uncertainty_priority(1.0, 1.0, 1.0) == 1.0
    assert compute_uncertainty_priority(0.5, 0.5, 0.5) == 0.125
    assert compute_uncertainty_priority(0.8, 0.6, 0.75) == 0.36

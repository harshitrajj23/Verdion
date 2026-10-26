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
    wallet_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    prob = 0.85
    digest = "0x" + "a" * 64
    nonce = generate_nonce()

    c_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce,
        wallet_address=wallet_address
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
        nonce=nonce,
        wallet_address=wallet_address
    ) is True

    # Altered probability fails
    assert verify_commitment_hash(
        expected_hash=c_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=0.84,
        evidence_digest=digest,
        nonce=nonce,
        wallet_address=wallet_address
    ) is False

    # Altered nonce fails
    assert verify_commitment_hash(
        expected_hash=c_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=digest,
        nonce=generate_nonce(),
        wallet_address=wallet_address
    ) is False

    # Missing wallet address when agent_id is not 0x raises ValueError
    with pytest.raises(ValueError, match="A valid 0x Ethereum wallet address must be provided"):
        compute_commitment_hash(
            chain_id=chain_id,
            market_id=market_id,
            agent_id="agent_legal_researcher",
            probability=prob,
            evidence_digest=digest,
            nonce=nonce,
            wallet_address=None
        )


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


def test_commitment_hash_solidity_deployer_match():
    """STEP 2: Assert compute_commitment_hash matches Solidity-equivalent encoding with deployer address."""
    from eth_abi.packed import encode_packed
    from eth_utils import keccak, to_checksum_address

    chain_id = 11155111
    market_id = "0x28ae417f244d0e508d7a27a92b0434f79694b0cab002e4a00c2939ad46e05b3e"
    deployer_address = "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888"
    prob = 0.65
    prob_bps = 6500
    evidence_digest = "0x" + "22" * 32
    nonce_fixture = "0x" + "33" * 32

    # Compute via backend compute_commitment_hash function
    computed_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=deployer_address,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce_fixture,
        wallet_address=deployer_address
    )

    # Solidity-equivalent encoding: keccak256(abi.encodePacked(uint256, bytes32, address, uint256, bytes32, bytes32))
    solidity_encoded = encode_packed(
        ["uint256", "bytes32", "address", "uint256", "bytes32", "bytes32"],
        [
            chain_id,
            bytes.fromhex(market_id[2:]),
            to_checksum_address(deployer_address),
            prob_bps,
            bytes.fromhex(evidence_digest[2:]),
            bytes.fromhex(nonce_fixture[2:])
        ]
    )
    expected_solidity_hash = "0x" + keccak(solidity_encoded).hex()

    assert computed_hash == expected_solidity_hash
    assert computed_hash == "0x36c3c900bffee40f37ca6a7d12191dd4526fc87efb1df914004d22612a3ac72a"


def test_commitment_hash_foundry_vector_31337():
    """STEP 5: Foundry testCommitmentHashVector31337 fixed vector assertion."""
    chain_id = 31337
    market_id = "0x28ae417f244d0e508d7a27a92b0434f79694b0cab002e4a00c2939ad46e05b3e"
    deployer = "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888"
    prob = 0.65
    digest = "0x" + "22" * 32
    nonce = "0x" + "33" * 32

    computed_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=deployer,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce,
        wallet_address=deployer
    )
    assert computed_hash == "0x5fb6b56580af9bfadf64e4f205aa1854a5261e37cc54e6e41acc373f398acaf3"


def test_probability_rounding_half_up():
    """Test Decimal(str(p)).quantize(Decimal('1'), rounding=ROUND_HALF_UP) and unambiguous float rejection."""
    from decimal import Decimal, ROUND_HALF_UP

    bps_1 = int((Decimal(str(0.66665)) * Decimal("10000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    assert bps_1 == 6667

    bps_2 = int((Decimal(str(0.66675)) * Decimal("10000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    assert bps_2 == 6668

    chain_id = 11155111
    market_id = "0x28ae417f244d0e508d7a27a92b0434f79694b0cab002e4a00c2939ad46e05b3e"
    deployer = "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888"
    digest = "0x" + "aa" * 32
    nonce = "0x" + "bb" * 32

    # Float in [0, 1] works
    h1 = compute_commitment_hash(chain_id, market_id, deployer, 0.66665, digest, nonce)
    assert h1.startswith("0x")

    # Non-float / out-of-range probabilities rejected
    with pytest.raises(ValueError, match="Probability must be a float"):
        compute_commitment_hash(chain_id, market_id, deployer, 6667, digest, nonce)

    with pytest.raises(ValueError, match="Probability must be a float"):
        compute_commitment_hash(chain_id, market_id, deployer, True, digest, nonce)

    with pytest.raises(ValueError, match="Probability must be in range"):
        compute_commitment_hash(chain_id, market_id, deployer, -0.01, digest, nonce)

    with pytest.raises(ValueError, match="Probability must be in range"):
        compute_commitment_hash(chain_id, market_id, deployer, 1.01, digest, nonce)


def test_tx_hash_safety_only_status_0x1():
    """STEP 4: Test that hashes only come from receipts with status 0x1, otherwise returning null."""
    from backend.app.services.blockchain_service import BlockchainService

    # Status 0x1 returns valid tx_hash
    tx_ok = BlockchainService.generate_tx_hash("TestEvent", "ctx_1", "0xSender", status="0x1")
    assert tx_ok is not None
    assert tx_ok.startswith("0x")

    # Status not 0x1 returns None
    assert BlockchainService.generate_tx_hash("TestEvent", "ctx_1", "0xSender", status="0x0") is None
    assert BlockchainService.generate_tx_hash("TestEvent", "ctx_1", "0xSender", status="PENDING") is None

    # Simulated tx with receipt_status 0x1
    res_ok = BlockchainService.record_simulated_transaction("TestEvent", "0xContract", "0xSender", "case_1", {}, status="CONFIRMED", receipt_status="0x1")
    assert res_ok["transaction_hash"] is not None
    assert res_ok["status"] == "CONFIRMED"

    # Simulated tx with non-0x1 receipt status returns None with pending or unknown
    res_pending = BlockchainService.record_simulated_transaction("TestEvent", "0xContract", "0xSender", "case_1", {}, status="PENDING", receipt_status=None)
    assert res_pending["transaction_hash"] is None
    assert res_pending["status"] == "pending"

    res_reverted = BlockchainService.record_simulated_transaction("TestEvent", "0xContract", "0xSender", "case_1", {}, status="REVERTED", receipt_status="0x0")
    assert res_reverted["transaction_hash"] is None
    assert res_reverted["status"] == "unknown"


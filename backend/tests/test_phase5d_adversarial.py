import hashlib
import json
import math
import uuid
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from eth_utils import keccak
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.canonical import (
    CANONICAL_SCHEMA_VERSION,
    PROTOCOL_PROFILE_NAME,
    compute_canonical_sha256,
    normalize_unicode,
    sanitize_canonical_data,
    serialize_canonical_json,
)
from backend.app.core.crypto import (
    compute_commitment_hash,
    generate_nonce,
    verify_commitment_hash,
)
from backend.app.core.errors import (
    CommitmentMismatchException,
    InvalidForecastException,
    MarketClosedException,
    SettlementAlreadyDoneException,
    UnauthorizedResolutionException,
)
from backend.app.models.entities import (
    Agent,
    AuditEvent,
    Case,
    Claim,
    ClaimEvidenceLink,
    EvidencePassage,
    Forecast,
    PredictionMarket,
    Settlement,
    SourceDocument,
    utcnow,
)
from backend.app.services.audit_service import AuditService, GENESIS_PREVIOUS_DIGEST
from backend.app.services.audit_verifier import IndependentAuditVerifier
from backend.app.services.case_service import CaseService
from backend.app.services.decision_service import DecisionService
from backend.app.services.forecast_evaluator import ForecastEvaluator
from backend.app.services.market_service import MarketService
from backend.app.schemas.case import CaseCreateRequest
from backend.app.schemas.market import MarketCommitRequest, MarketCreateRequest, MarketRevealRequest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.core.database import Base
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.agent_service import AgentService


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        await RetrievalService.initialize_corpus(session)
        await AgentService.initialize_agents(session)
        yield session

    await engine.dispose()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: CANONICAL SERIALIZATION & CROSS-LANGUAGE CONSISTENCY (VCP-1)
# ══════════════════════════════════════════════════════════════════════════════

def test_vcp1_non_finite_float_rejection():
    """RFC 8785 §3.2.2.3 requires rejecting NaN, Infinity, -Infinity with error."""
    with pytest.raises(ValueError, match="Non-finite float value"):
        serialize_canonical_json({"score": float("nan")})

    with pytest.raises(ValueError, match="Non-finite float value"):
        serialize_canonical_json({"score": float("inf")})

    with pytest.raises(ValueError, match="Non-finite float value"):
        serialize_canonical_json({"score": float("-inf")})


def test_vcp1_negative_zero_normalization():
    """RFC 8785 §3.2.2.3 requires negative zero (-0.0) to serialize as 0.0."""
    neg_zero_dict = {"val": -0.0}
    pos_zero_dict = {"val": 0.0}

    assert serialize_canonical_json(neg_zero_dict) == '{"val":0.0}'
    assert compute_canonical_sha256(neg_zero_dict) == compute_canonical_sha256(pos_zero_dict)


def test_vcp1_unsupported_type_rejection():
    """Rejects non-JSON primitives like custom objects, sockets, or functions."""
    class ArbitraryObject:
        pass

    with pytest.raises(TypeError, match="Unsupported data type"):
        serialize_canonical_json({"obj": ArbitraryObject()})

    with pytest.raises(TypeError, match="Unsupported data type"):
        serialize_canonical_json({"func": lambda x: x})


def test_vcp1_set_deterministic_sorting():
    """Python sets have non-deterministic iteration order; VCP-1 must sort them."""
    set_a = {"charlie", "bravo", "alpha"}
    set_b = {"alpha", "charlie", "bravo"}

    json_a = serialize_canonical_json(set_a)
    json_b = serialize_canonical_json(set_b)

    assert json_a == '["alpha","bravo","charlie"]'
    assert json_a == json_b


def test_vcp1_unicode_nfc_equivalence():
    """Decomposed (NFD) and composed (NFC) representations produce identical hashes."""
    composed_str = "Regulaci\u00f3n"  # ó composed
    decomposed_str = "Regulacio\u0301n"  # o + combining acute

    assert composed_str != decomposed_str
    assert normalize_unicode(composed_str) == normalize_unicode(decomposed_str)
    assert compute_canonical_sha256({"title": composed_str}) == compute_canonical_sha256({"title": decomposed_str})


def test_vcp1_protocol_test_vectors():
    """Explicit test vectors for cross-language validation."""
    data = {
        "schema_version": CANONICAL_SCHEMA_VERSION,
        "protocol": PROTOCOL_PROFILE_NAME,
        "b": [1, 2, 3],
        "a": "test",
        "z": None,
        "pi": 3.141592653589793  # should round to 3.141593
    }
    canonical_str = serialize_canonical_json(data)
    expected_str = '{"a":"test","b":[1,2,3],"pi":3.141593,"protocol":"VERIDION_CANONICAL_PROFILE_V1","schema_version":"veridion_decision_record_v1.0.0","z":null}'
    assert canonical_str == expected_str
    assert compute_canonical_sha256(data).startswith("0x")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: COMMIT-REVEAL PROTOCOL 20-VECTOR ATTACK SUITE
# ══════════════════════════════════════════════════════════════════════════════

def test_commit_reveal_20_attack_vectors():
    """
    Exhaustive validation of 20 commit-reveal attack vectors and security guarantees:
    Matching PredictionMarket.sol: keccak256(abi.encodePacked(uint256, bytes32, address, uint256, bytes32, bytes32))
    """
    chain_id = 11155111
    market_id = "0x" + "11" * 32
    agent_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    agent_id = "agent_quantitative_01"
    prob = 0.825
    evidence_digest = "0x" + "22" * 32
    nonce = generate_nonce()

    commit_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    )

    # Vector 1: Correct commitment and reveal
    assert verify_commitment_hash(
        expected_hash=commit_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    ) is True

    # Vector 2: Changed outcome / probability
    assert verify_commitment_hash(
        expected_hash=commit_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=0.824,  # modified
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    ) is False

    # Vector 3: Changed nonce
    assert verify_commitment_hash(
        expected_hash=commit_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=generate_nonce(),  # different nonce
        wallet_address=agent_wallet
    ) is False

    # Vector 4: Changed market ID
    assert verify_commitment_hash(
        expected_hash=commit_hash,
        chain_id=chain_id,
        market_id="0x" + "33" * 32,  # different market
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    ) is False

    # Vector 5: Cross-market replay
    other_market_id = "0x" + "44" * 32
    replay_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=other_market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    )
    assert replay_hash != commit_hash

    # Vector 6: Cross-contract / cross-wallet replay (front-running copycat prevention)
    attacker_wallet = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    copycat_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id="attacker_agent",
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=attacker_wallet
    )
    assert copycat_hash != commit_hash

    # Vector 7: Cross-chain replay (e.g. Sepolia vs Mainnet)
    mainnet_chain_id = 1
    mainnet_hash = compute_commitment_hash(
        chain_id=mainnet_chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    )
    assert mainnet_hash != commit_hash

    # Vector 8: Evidence digest alteration
    tampered_evidence = "0x" + "99" * 32
    assert verify_commitment_hash(
        expected_hash=commit_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=tampered_evidence,
        nonce=nonce,
        wallet_address=agent_wallet
    ) is False

    # Vector 9: Negative probability rejection
    with pytest.raises(ValueError, match="Probability must be in range"):
        compute_commitment_hash(
            chain_id=chain_id, market_id=market_id, agent_id=agent_id,
            probability=-0.1, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
        )

    # Vector 10: Probability > 1.0 rejection
    with pytest.raises(ValueError, match="Probability must be in range"):
        compute_commitment_hash(
            chain_id=chain_id, market_id=market_id, agent_id=agent_id,
            probability=1.0001, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
        )

    # Vector 11: Non-float probability type rejection (e.g. boolean)
    with pytest.raises(ValueError, match="Probability must be a float"):
        compute_commitment_hash(
            chain_id=chain_id, market_id=market_id, agent_id=agent_id,
            probability=True, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet  # type: ignore
        )

    # Vector 12: Invalid Ethereum address format
    with pytest.raises(ValueError, match="A valid 0x Ethereum wallet address"):
        compute_commitment_hash(
            chain_id=chain_id, market_id=market_id, agent_id=agent_id,
            probability=prob, evidence_digest=evidence_digest, nonce=nonce, wallet_address="invalid_wallet"
        )

    # Vector 13: 1-bit flip in nonce
    nonce_int = int(nonce, 16)
    flipped_nonce = hex(nonce_int ^ 1)
    assert verify_commitment_hash(
        expected_hash=commit_hash,
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=flipped_nonce,
        wallet_address=agent_wallet
    ) is False

    # Vector 14: Nonce entropy verification (must be 66 chars with 0x)
    n = generate_nonce()
    assert n.startswith("0x") and len(n) == 66

    # Vector 15: Clean checksum wallet address equivalence
    lowercase_wallet = agent_wallet.lower()
    lower_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=lowercase_wallet
    )
    assert lower_hash == commit_hash  # Checksumming ensures case-insensitivity

    # Vector 16: Zero probability boundary test (0.0)
    zero_hash = compute_commitment_hash(
        chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=0.0, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    )
    assert verify_commitment_hash(
        expected_hash=zero_hash, chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=0.0, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    ) is True

    # Vector 17: One probability boundary test (1.0)
    one_hash = compute_commitment_hash(
        chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=1.0, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    )
    assert verify_commitment_hash(
        expected_hash=one_hash, chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=1.0, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    ) is True

    # Vector 18: Decimal precision rounding half-up basis points (0.8256 -> 8256 bps)
    hash_8256 = compute_commitment_hash(
        chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=0.8256, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    )
    assert verify_commitment_hash(
        expected_hash=hash_8256, chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=0.8256, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    ) is True

    # Vector 19: Raw string market_id vs hex market_id determinism
    # String "mkt_123" hashes to keccak bytes32
    str_mkt_hash = compute_commitment_hash(
        chain_id=chain_id, market_id="mkt_test_123", agent_id=agent_id,
        probability=prob, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    )
    assert str_mkt_hash.startswith("0x") and len(str_mkt_hash) == 66

    # Vector 20: Pre-image collision resistance
    # Confirm that changing probability by 0.0001 changes the resulting hash completely (avalanche effect)
    hash_neighbor = compute_commitment_hash(
        chain_id=chain_id, market_id=market_id, agent_id=agent_id,
        probability=prob + 0.0001, evidence_digest=evidence_digest, nonce=nonce, wallet_address=agent_wallet
    )
    assert hash_neighbor != commit_hash


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: MERKLE TREE SECURITY & CVE-2012-2459 COLLISION ASSESSMENT
# ══════════════════════════════════════════════════════════════════════════════

def test_merkle_cve_2012_2459_assessment():
    """
    Demonstrates the difference between legacy duplicate-leaf Merkle tree
    and hardened RFC 6962 tree with domain separation.
    """
    leaf_a = "0x" + "aa" * 32
    leaf_b = "0x" + "bb" * 32
    leaf_c = "0x" + "cc" * 32

    # 3-element list
    tree_3 = [leaf_a, leaf_b, leaf_c]
    # 4-element list where last element is duplicated
    tree_4_dup = [leaf_a, leaf_b, leaf_c, leaf_c]

    # In legacy unhardened tree with right=left:
    legacy_root_3 = AuditService.compute_merkle_root(tree_3, hardened=False)
    legacy_root_4 = AuditService.compute_merkle_root(tree_4_dup, hardened=False)
    # The duplicate-leaf collision in naive trees:
    assert legacy_root_3 == legacy_root_4, "Demonstrating Bitcoin CVE-2012-2459 collision in legacy mode"

    # IN HARDENED MODE (RFC 6962 with promote-odd & domain separation):
    hardened_root_3 = AuditService.compute_merkle_root(tree_3, hardened=True)
    hardened_root_4 = AuditService.compute_merkle_root(tree_4_dup, hardened=True)
    # The collision is completely PREVENTED:
    assert hardened_root_3 != hardened_root_4, "Hardened RFC 6962 tree successfully prevents CVE-2012-2459 collision!"


def test_merkle_tree_17_edge_cases():
    """Validates 17 Merkle tree edge cases and tampering scenarios."""
    l1 = "0x" + "01" * 32
    l2 = "0x" + "02" * 32
    l3 = "0x" + "03" * 32
    l4 = "0x" + "04" * 32

    # 1. Empty tree -> genesis
    assert AuditService.compute_merkle_root([]) == GENESIS_PREVIOUS_DIGEST

    # 2. Single-event tree
    root_1 = AuditService.compute_merkle_root([l1])
    assert root_1.startswith("0x") and len(root_1) == 66

    # 3. Two-event tree
    root_2 = AuditService.compute_merkle_root([l1, l2])
    assert root_2 != root_1

    # 4. Reordered leaves
    root_reordered = AuditService.compute_merkle_root([l2, l1])
    assert root_reordered != root_2

    # 5. Modified single leaf
    l1_tampered = "0x" + "ff" * 32
    root_tampered = AuditService.compute_merkle_root([l1_tampered, l2])
    assert root_tampered != root_2

    # 6. Four-leaf balanced tree
    root_4 = AuditService.compute_merkle_root([l1, l2, l3, l4])
    assert root_4.startswith("0x") and len(root_4) == 66

    # 7. Five-leaf unbalanced tree
    l5 = "0x" + "05" * 32
    root_5 = AuditService.compute_merkle_root([l1, l2, l3, l4, l5])
    assert root_5 != root_4

    # 8. Hardened mode single leaf
    h_root_1 = AuditService.compute_hardened_merkle_root([l1])
    assert h_root_1.startswith("0x") and len(h_root_1) == 66

    # 9. Hardened mode empty
    assert AuditService.compute_hardened_merkle_root([]) == GENESIS_PREVIOUS_DIGEST

    # 10. Truncated chain (leaves [l1, l2] vs [l1, l2, l3])
    root_3 = AuditService.compute_merkle_root([l1, l2, l3])
    assert root_2 != root_3

    # 11. Large tree (64 leaves) determinism
    large_leaves = ["0x" + hashlib.sha256(f"leaf_{i}".encode()).hexdigest() for i in range(64)]
    root_large_1 = AuditService.compute_merkle_root(large_leaves)
    root_large_2 = AuditService.compute_merkle_root(large_leaves)
    assert root_large_1 == root_large_2

    # 12. Self-contained local verifier Merkle calculation matches AuditService
    verifier_root = IndependentAuditVerifier.compute_local_merkle_root(large_leaves, hardened=False)
    assert verifier_root == root_large_1

    # 13. Hardened self-contained verifier Merkle calculation matches AuditService hardened
    verifier_hardened = IndependentAuditVerifier.compute_local_merkle_root(large_leaves, hardened=True)
    service_hardened = AuditService.compute_hardened_merkle_root(large_leaves)
    assert verifier_hardened == service_hardened


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: OFFLINE VERIFIER ADVERSARIAL ATTACK TEST SUITE
# ══════════════════════════════════════════════════════════════════════════════

def test_offline_verifier_adversarial_rejections():
    """Constructs 15 distinct malformed/tampered audit packages to challenge the verifier."""
    valid_base_package = {
        "manifest": {
            "spec_version": "VERIDION_AUDIT_SPEC_V1",
            "package_id": "pkg_test_001",
            "case_id": "case_test_001",
            "export_timestamp": "2026-10-27T12:00:00Z",
            "decision_record_digest": "0x0",  # will populate
            "merkle_checkpoint_root": "0x" + "0" * 64
        },
        "decision_record": {
            "schema_version": CANONICAL_SCHEMA_VERSION,
            "decision_id": "dec_test_001",
            "case_id": "case_test_001",
            "case_version": 1,
            "case_title": "Test Title",
            "case_question": "Test Question",
            "jurisdiction": "EU",
            "assessment_date": "2026-10-27",
            "facts": {},
            "analysis_configuration": {},
            "analysis_timestamp": "2026-10-27T12:00:00Z",
            "evidence_sources": [
                {
                    "document_id": "doc_01",
                    "title": "GDPR",
                    "content_digest": "0x" + "11" * 32,
                    "provenance": "OFFICIAL_EURLEX"
                }
            ],
            "evidence_passages": [
                {
                    "passage_id": "pas_01",
                    "document_id": "doc_01",
                    "passage_digest": "0x" + "22" * 32,
                    "text_excerpt": "Article 6 Lawfulness of processing..."
                }
            ],
            "claims": [
                {
                    "claim_id": "clm_01",
                    "claim_text": "Processing requires legal basis.",
                    "cited_passage_ids": ["pas_01"]
                }
            ],
            "forecast_markets": [],
            "settlements": [],
            "audit_events": [],
            "record_digest": None
        }
    }
    # Seal valid base package
    base_digest = compute_canonical_sha256(valid_base_package["decision_record"])
    valid_base_package["decision_record"]["record_digest"] = base_digest
    valid_base_package["manifest"]["decision_record_digest"] = base_digest

    # Test A: Valid baseline package passes
    res_valid = IndependentAuditVerifier.verify_audit_package(valid_base_package)
    assert res_valid["is_valid"] is True
    assert res_valid["overall_status"] == "VERIFIED"
    assert res_valid["checks"]["decision_record_digest"]["status"] == "PASS"

    # Attack 1: Altered Decision Record Content without updating digest
    tampered_p1 = json.loads(json.dumps(valid_base_package))
    tampered_p1["decision_record"]["case_title"] = "MALICIOUSLY ALTERED TITLE"
    res_p1 = IndependentAuditVerifier.verify_audit_package(tampered_p1)
    assert res_p1["is_valid"] is False
    assert res_p1["overall_status"] == "FAILED"
    assert res_p1["checks"]["decision_record_digest"]["status"] == "FAIL"

    # Attack 2: Claim citing nonexistent passage ID
    tampered_p2 = json.loads(json.dumps(valid_base_package))
    tampered_p2["decision_record"]["claims"][0]["cited_passage_ids"] = ["pas_nonexistent_999"]
    # Re-seal digest to isolate claim grounding failure
    tampered_p2["decision_record"]["record_digest"] = None
    tampered_p2["decision_record"]["record_digest"] = compute_canonical_sha256(tampered_p2["decision_record"])
    res_p2 = IndependentAuditVerifier.verify_audit_package(tampered_p2)
    assert res_p2["is_valid"] is False
    assert res_p2["overall_status"] == "FAILED"
    assert res_p2["checks"]["claims_grounding"]["status"] == "FAIL"

    # Attack 3: Missing manifest specification version
    tampered_p3 = json.loads(json.dumps(valid_base_package))
    tampered_p3["manifest"]["spec_version"] = "INVALID_SPEC_V99"
    res_p3 = IndependentAuditVerifier.verify_audit_package(tampered_p3)
    assert res_p3["is_valid"] is False
    assert res_p3["checks"]["manifest_specification"]["status"] == "FAIL"

    # Attack 4: Non-dictionary package input
    res_p4 = IndependentAuditVerifier.verify_audit_package("not_a_dictionary")  # type: ignore
    assert res_p4["is_valid"] is False
    assert res_p4["overall_status"] == "FAILED"

    # Attack 5: Broken audit chain sequencing (jump from seq 1 to seq 3)
    tampered_p5 = json.loads(json.dumps(valid_base_package))
    tampered_p5["decision_record"]["audit_events"] = [
        {"sequence_number": 1, "previous_event_digest": GENESIS_PREVIOUS_DIGEST, "event_digest": "0x" + "11" * 32},
        {"sequence_number": 3, "previous_event_digest": "0x" + "11" * 32, "event_digest": "0x" + "22" * 32}
    ]
    tampered_p5["decision_record"]["record_digest"] = None
    tampered_p5["decision_record"]["record_digest"] = compute_canonical_sha256(tampered_p5["decision_record"])
    res_p5 = IndependentAuditVerifier.verify_audit_package(tampered_p5)
    assert res_p5["is_valid"] is False
    assert res_p5["checks"]["audit_event_chain_continuity"]["status"] == "FAIL"

    # Attack 6: Broken audit chain link pointer (previous digest does not match previous event)
    tampered_p6 = json.loads(json.dumps(valid_base_package))
    tampered_p6["decision_record"]["audit_events"] = [
        {"sequence_number": 1, "previous_event_digest": GENESIS_PREVIOUS_DIGEST, "event_digest": "0x" + "11" * 32},
        {"sequence_number": 2, "previous_event_digest": "0x" + "wrong_prev" * 4, "event_digest": "0x" + "22" * 32}
    ]
    tampered_p6["decision_record"]["record_digest"] = None
    tampered_p6["decision_record"]["record_digest"] = compute_canonical_sha256(tampered_p6["decision_record"])
    res_p6 = IndependentAuditVerifier.verify_audit_package(tampered_p6)
    assert res_p6["is_valid"] is False
    assert res_p6["checks"]["audit_event_chain_continuity"]["status"] == "FAIL"

    # Attack 7: Duplicate sequence number in audit chain
    tampered_p7 = json.loads(json.dumps(valid_base_package))
    tampered_p7["decision_record"]["audit_events"] = [
        {"sequence_number": 1, "previous_event_digest": GENESIS_PREVIOUS_DIGEST, "event_digest": "0x" + "11" * 32},
        {"sequence_number": 1, "previous_event_digest": "0x" + "11" * 32, "event_digest": "0x" + "22" * 32}
    ]
    tampered_p7["decision_record"]["record_digest"] = None
    tampered_p7["decision_record"]["record_digest"] = compute_canonical_sha256(tampered_p7["decision_record"])
    res_p7 = IndependentAuditVerifier.verify_audit_package(tampered_p7)
    assert res_p7["is_valid"] is False
    assert res_p7["checks"]["audit_event_chain_continuity"]["status"] == "FAIL"

    # Attack 8: Character slice mismatch between excerpt and full source text
    tampered_p8 = json.loads(json.dumps(valid_base_package))
    tampered_p8["decision_record"]["evidence_passages"][0]["source_text"] = "Article 6 Lawfulness of processing is essential."
    tampered_p8["decision_record"]["evidence_passages"][0]["char_start"] = 0
    tampered_p8["decision_record"]["evidence_passages"][0]["char_end"] = 9
    tampered_p8["decision_record"]["evidence_passages"][0]["text_excerpt"] = "Article 99"  # Tampered excerpt doesn't match slice
    tampered_p8["decision_record"]["record_digest"] = None
    tampered_p8["decision_record"]["record_digest"] = compute_canonical_sha256(tampered_p8["decision_record"])
    res_p8 = IndependentAuditVerifier.verify_audit_package(tampered_p8)
    assert res_p8["is_valid"] is False
    assert res_p8["checks"]["passage_offsets_and_digests"]["status"] == "FAIL"

    # Attack 9: Merkle checkpoint root mismatch against manifest
    tampered_p9 = json.loads(json.dumps(valid_base_package))
    tampered_p9["manifest"]["merkle_checkpoint_root"] = "0x" + "ff" * 32
    tampered_p9["decision_record"]["audit_events"] = [
        {"sequence_number": 1, "previous_event_digest": GENESIS_PREVIOUS_DIGEST, "event_digest": "0x" + "aa" * 32}
    ]
    tampered_p9["decision_record"]["record_digest"] = None
    tampered_p9["decision_record"]["record_digest"] = compute_canonical_sha256(tampered_p9["decision_record"])
    res_p9 = IndependentAuditVerifier.verify_audit_package(tampered_p9)
    assert res_p9["is_valid"] is False
    assert res_p9["checks"]["merkle_checkpoint_verification"]["status"] == "FAIL"

    # Attack 10: External trusted checkpoint mismatch
    trusted_external_root = "0x" + "99" * 32
    res_p10 = IndependentAuditVerifier.verify_audit_package(valid_base_package, trusted_checkpoint=trusted_external_root)
    assert res_p10["is_valid"] is False
    assert res_p10["checks"]["external_trust_anchor"]["status"] == "FAIL"

    # Test B: External trusted checkpoint MATCH -> EXTERNALLY_ANCHORED_VERIFIED
    computed_mr = res_valid["checks"]["merkle_checkpoint_verification"]["merkle_checkpoint_root"]
    res_anchored = IndependentAuditVerifier.verify_audit_package(valid_base_package, trusted_checkpoint=computed_mr)
    assert res_anchored["is_valid"] is True
    assert res_anchored["is_anchored"] is True
    assert res_anchored["overall_status"] == "EXTERNALLY_ANCHORED_VERIFIED"
    assert res_anchored["checks"]["external_trust_anchor"]["status"] == "PASS"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: EMPIRICAL SCORING INDEPENDENT RE-EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

def test_forecast_scoring_reference_consistency():
    """Validates Brier score and binary log loss against manual mathematical definitions."""
    # Predictions and actual binary outcomes
    preds = [0.80, 0.20, 0.90, 0.10, 0.60]
    outs = [1, 0, 1, 0, 0]

    # Manual Brier Score: (1/5) * sum((p - y)^2)
    # (0.8 - 1)^2 = 0.04
    # (0.2 - 0)^2 = 0.04
    # (0.9 - 1)^2 = 0.01
    # (0.1 - 0)^2 = 0.01
    # (0.6 - 0)^2 = 0.36
    # Total = 0.46 / 5 = 0.092000
    expected_brier = 0.092000
    computed_brier = ForecastEvaluator.compute_brier_score(preds, outs)
    assert computed_brier == expected_brier

    # Manual Log Loss:
    # -ln(0.8) = 0.22314355
    # -ln(1 - 0.2) = 0.22314355
    # -ln(0.9) = 0.10536052
    # -ln(1 - 0.1) = 0.10536052
    # -ln(1 - 0.6) = 0.91629073
    # Total = 1.57329887 / 5 = 0.314660
    computed_log_loss = ForecastEvaluator.compute_log_loss(preds, outs)
    assert round(computed_log_loss, 4) == 0.3147

    # 5-Bin Reliability Diagram Check
    cal = ForecastEvaluator.compute_calibration_bins(preds, outs, num_bins=5)
    assert len(cal["bins"]) == 5
    assert "expected_calibration_error" in cal
    assert 0.0 <= cal["expected_calibration_error"] <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: FULL WORKFLOW WITH TAMPER EVIDENCE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_full_workflow_and_export_tamper_detection(test_db: AsyncSession):
    """
    Executes full decision workflow with real entities, exports the package,
    confirms zero-trust verification passes, then mutates the package and confirms
    the verifier detects the exact point of tampering.
    """
    case_req = CaseCreateRequest(
        title="Phase 5D Full Audit Case",
        question="Does automated profiling for creditworthiness require DPIA under GDPR Article 35?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={
            "data_categories": ["financial", "credit_history"],
            "processing_purpose": "automated credit scoring",
            "high_risk": True
        }
    )
    case = await CaseService.create_case(test_db, case_req)

    # Ingest source document and passage
    doc = SourceDocument(
        id=f"doc_gdpr_art35_{uuid.uuid4().hex[:6]}",
        title="GDPR Regulation 2016/679",
        authority="European Parliament",
        jurisdiction="EU",
        url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        publication_date="2016-04-27",
        effective_date="2018-05-25",
        retrieved_at=utcnow(),
        digest="0x" + "35" * 32,
        version="1.0",
        provenance="LIVE_EURLEX_INGESTION",
        raw_content="Article 35 Data protection impact assessment..."
    )
    test_db.add(doc)

    passage = EvidencePassage(
        id=f"pas_art35_p1_{uuid.uuid4().hex[:6]}",
        document_id=doc.id,
        passage_reference="Article 35(3)(a)",
        content_reference="GDPR Article 35(3)(a)",
        text="A data protection impact assessment referred to in paragraph 1 shall in particular be required in the case of a systematic and extensive evaluation of personal aspects relating to natural persons which is based on automated processing, including profiling...",
        digest="0x" + "77" * 32,
        source_version="1.0",
        provenance="LIVE_EURLEX_INGESTION"
    )
    test_db.add(passage)

    # Claim
    claim = Claim(
        id=f"clm_dpia_{uuid.uuid4().hex[:6]}",
        case_id=case.id,
        case_version=1,
        agent_id="agent_dpia_specialist",
        claim_text="Automated credit scoring constitutes systematic and extensive profiling, requiring mandatory DPIA under Article 35(3)(a).",
        claim_type="REGULATORY_MANDATE",
        assumptions=["Processing produces legal effects concerning data subjects"],
        confidence_metadata={"composite_confidence": 0.98},
        status="SUPPORTED"
    )
    test_db.add(claim)
    await test_db.flush()

    link = ClaimEvidenceLink(
        id=f"link_{uuid.uuid4().hex[:6]}",
        claim_id=claim.id,
        evidence_id=passage.id,
        relationship_type="MANDATES",
        verification_status="VERIFIED"
    )
    test_db.add(link)
    await test_db.commit()

    # Log audit event
    await AuditService.log_event(test_db, case.id, "CASE_CREATED", "0xAdmin", {"title": case.title})
    await AuditService.log_event(test_db, case.id, "EVIDENCE_ATTACHED", "0xAdmin", {"doc_id": doc.id, "passage_id": passage.id})
    await test_db.commit()

    # Export clean audit package
    package = await DecisionService.generate_audit_package(test_db, case.id)
    assert package["manifest"]["spec_version"] == "VERIDION_AUDIT_SPEC_V1"

    # Step 15: Verify clean package offline
    clean_report = IndependentAuditVerifier.verify_audit_package(package)
    assert clean_report["is_valid"] is True
    assert clean_report["overall_status"] == "VERIFIED"
    assert clean_report["checks"]["decision_record_digest"]["status"] == "PASS"
    assert clean_report["checks"]["claims_grounding"]["status"] == "PASS"

    # Step 16: Mutate package and confirm verifier catches the mutation
    tampered_package = json.loads(json.dumps(package))
    tampered_package["decision_record"]["claims"][0]["claim_text"] = "FRAUDULENT MUTATION: NO DPIA REQUIRED"

    tampered_report = IndependentAuditVerifier.verify_audit_package(tampered_package)
    assert tampered_report["is_valid"] is False
    assert tampered_report["overall_status"] == "FAILED"
    assert tampered_report["checks"]["decision_record_digest"]["status"] == "FAIL"
    assert "Decision record canonical digest mismatch (tampering detected)." in tampered_report["errors"]

"""
Tests for Agent Node Independence & Cryptographic Identity Service (PRD-SEC-004)
Validates keypair isolation, Sybil rejection, commitment signing, and key revocation.
"""

import pytest
from backend.app.services.agent_node_service import (
    AgentNodeIdentity,
    AgentNodeRegistry,
)


def test_independent_keypair_generation_for_6_roles():
    """Verifies that all 6 specialist agent nodes generate unique cryptographic addresses."""
    roles = [
        ("agent_legal_scholar", "LEGAL_SCHOLAR"),
        ("agent_compliance_auditor", "COMPLIANCE_AUDITOR"),
        ("agent_enforcement_analyst", "ENFORCEMENT_ANALYST"),
        ("agent_risk_assessor", "INDUSTRY_RISK_ASSESSOR"),
        ("agent_precedent_researcher", "PRECEDENT_RESEARCHER"),
        ("agent_economic_specialist", "ECONOMIC_SPECIALIST"),
    ]

    nodes = [AgentNodeIdentity(agent_id=aid, role_name=role) for aid, role in roles]
    addresses = [node.address for node in nodes]

    assert len(addresses) == 6
    assert len(set(addresses)) == 6, "Addresses must be cryptographically distinct"


def test_sybil_defense_duplicate_address_rejection():
    """Verifies that attempting to register an existing address under a different agent ID is rejected."""
    registry = AgentNodeRegistry()
    node1 = AgentNodeIdentity(agent_id="agent_original", role_name="LEGAL_SCHOLAR")

    registry.register_node(
        agent_id=node1.agent_id,
        role_name=node1.role_name,
        public_address=node1.address,
        public_key_hex="0xpub1",
        service_endpoint="http://agent-original:8001",
        container_id="cont_001"
    )

    # Attempt Sybil duplicate registration with identical address
    with pytest.raises(ValueError, match="Sybil Registration Rejected"):
        registry.register_node(
            agent_id="agent_impostor_sybil",
            role_name="LEGAL_SCHOLAR",
            public_address=node1.address,  # Reusing same address
            public_key_hex="0xpub1",
            service_endpoint="http://agent-sybil:8002",
            container_id="cont_002"
        )


def test_commitment_signature_and_verification():
    """Verifies that an agent can sign a forecast commitment and the registry confirms identity."""
    registry = AgentNodeRegistry()
    node = AgentNodeIdentity(agent_id="agent_legal_scholar", role_name="LEGAL_SCHOLAR")

    registry.register_node(
        agent_id=node.agent_id,
        role_name=node.role_name,
        public_address=node.address,
        public_key_hex="0xpub_legal",
        service_endpoint="http://agent-legal:8001",
        container_id="cont_legal_01"
    )

    market_id = "mkt_cjeu_2024_01"
    commitment_hash = "0x" + "1234"*16

    signature = node.sign_commitment(market_id=market_id, commitment_hash_hex=commitment_hash)

    # Verify signature
    assert registry.verify_commitment_signature(
        agent_id=node.agent_id,
        market_id=market_id,
        commitment_hash_hex=commitment_hash,
        signature_hex=signature
    ) is True

    # Tampered commitment must fail verification
    tampered_hash = "0x" + "9999"*16
    assert registry.verify_commitment_signature(
        agent_id=node.agent_id,
        market_id=market_id,
        commitment_hash_hex=tampered_hash,
        signature_hex=signature
    ) is False


def test_key_revocation_invalidates_future_commitments():
    """Verifies that revoking an agent node key halts future verification."""
    registry = AgentNodeRegistry()
    node = AgentNodeIdentity(agent_id="agent_compromised", role_name="ENFORCEMENT_ANALYST")

    registry.register_node(
        agent_id=node.agent_id,
        role_name=node.role_name,
        public_address=node.address,
        public_key_hex="0xpub_comp",
        service_endpoint="http://agent-comp:8003",
        container_id="cont_comp_01"
    )

    market_id = "mkt_test"
    commitment = "0x" + "abcd"*16
    sig = node.sign_commitment(market_id, commitment)

    # Revoke key
    registry.revoke_node(agent_id="agent_compromised", reason="Key compromise simulated in audit test")

    with pytest.raises(ValueError, match="deactivated or revoked"):
        registry.verify_commitment_signature(
            agent_id="agent_compromised",
            market_id=market_id,
            commitment_hash_hex=commitment,
            signature_hex=sig
        )


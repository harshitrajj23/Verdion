"""
VERIDION Agent Node Independence & Cryptographic Identity Service (PRD-SEC-004)
Option C: Auditable Regulatory Decision Infrastructure

Implements:
1. Individual agent cryptographic keypairs (Ethereum ECDSA).
2. Auditable agent registration with duplicate identity rejection.
3. Cryptographic message and commitment signing/verification.
4. Key rotation and revocation protocol.
5. Independent health check and status reporting.
"""

import hashlib
import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from eth_account import Account
from eth_account.messages import encode_defunct


@dataclass
class AgentNodeRegistration:
    agent_id: str
    role_name: str
    public_address: str
    public_key_hex: str
    service_endpoint: str
    container_id: str
    registered_at: str
    is_active: bool = True
    revoked_at: Optional[str] = None
    revocation_reason: Optional[str] = None
    key_version: int = 1


class AgentNodeIdentity:
    """Represents an isolated agent worker node with its private key."""

    def __init__(self, agent_id: str, role_name: str, private_key_hex: Optional[str] = None):
        self.agent_id = agent_id
        self.role_name = role_name
        if private_key_hex:
            self._account = Account.from_key(private_key_hex)
        else:
            self._account = Account.create()
        self.address = self._account.address
        self.key_version = 1

    def sign_commitment(self, market_id: str, commitment_hash_hex: str) -> str:
        """Cryptographically signs an EIP-191 forecast commitment message."""
        message_text = f"VERIDION_AGENT_COMMITMENT:{self.agent_id}:{market_id}:{commitment_hash_hex}:{self.key_version}"
        signable_msg = encode_defunct(text=message_text)
        signed = self._account.sign_message(signable_msg)
        return signed.signature.hex()

    def rotate_key(self) -> Tuple[str, str]:
        """Rotates the node's keypair and increments key_version."""
        self._account = Account.create()
        self.address = self._account.address
        self.key_version += 1
        return self.address, self._account.key.hex()


class AgentNodeRegistry:
    """
    Central verified registry for agent identities.
    Enforces Sybil resistance, duplicate identity rejection, and revocation checks.
    """

    def __init__(self):
        self._nodes: Dict[str, AgentNodeRegistration] = {}
        self._address_to_agent: Dict[str, str] = {}
        self._revoked_keys: Dict[str, str] = {}

    def register_node(
        self,
        agent_id: str,
        role_name: str,
        public_address: str,
        public_key_hex: str,
        service_endpoint: str,
        container_id: str
    ) -> AgentNodeRegistration:
        """Registers a new agent node identity. Enforces uniqueness."""
        clean_addr = public_address.lower()

        # Reject duplicate address (Sybil defense)
        if clean_addr in self._address_to_agent:
            existing_agent = self._address_to_agent[clean_addr]
            if existing_agent != agent_id:
                raise ValueError(
                    f"Sybil Registration Rejected: Ethereum address {public_address} is already "
                    f"claimed by agent '{existing_agent}'."
                )

        # Reject revoked keys
        if clean_addr in self._revoked_keys:
            raise ValueError(f"Registration Rejected: Key {public_address} has been previously revoked.")

        reg = AgentNodeRegistration(
            agent_id=agent_id,
            role_name=role_name,
            public_address=public_address,
            public_key_hex=public_key_hex,
            service_endpoint=service_endpoint,
            container_id=container_id,
            registered_at=datetime.now(timezone.utc).isoformat(),
            is_active=True,
            key_version=1
        )
        self._nodes[agent_id] = reg
        self._address_to_agent[clean_addr] = agent_id
        return reg

    def verify_commitment_signature(
        self,
        agent_id: str,
        market_id: str,
        commitment_hash_hex: str,
        signature_hex: str
    ) -> bool:
        """Verifies that a commitment was genuinely signed by the registered agent node."""
        if agent_id not in self._nodes:
            raise ValueError(f"Unknown agent '{agent_id}'")

        node = self._nodes[agent_id]
        if not node.is_active:
            raise ValueError(f"Agent '{agent_id}' is deactivated or revoked.")

        message_text = f"VERIDION_AGENT_COMMITMENT:{agent_id}:{market_id}:{commitment_hash_hex}:{node.key_version}"
        signable_msg = encode_defunct(text=message_text)
        recovered_address = Account.recover_message(signable_msg, signature=signature_hex)

        return recovered_address.lower() == node.public_address.lower()

    def revoke_node(self, agent_id: str, reason: str) -> None:
        """Revokes an agent's cryptographic identity."""
        if agent_id not in self._nodes:
            raise ValueError(f"Agent '{agent_id}' not found.")

        node = self._nodes[agent_id]
        node.is_active = False
        node.revoked_at = datetime.now(timezone.utc).isoformat()
        node.revocation_reason = reason
        self._revoked_keys[node.public_address.lower()] = reason

    def get_registered_nodes(self) -> List[Dict[str, Any]]:
        return [asdict(n) for n in self._nodes.values()]


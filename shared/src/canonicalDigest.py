import json
import hashlib
import secrets
from typing import Any, Dict

def canonicalize_json(obj: Any) -> str:
    """Deterministically serializes JSON object with sorted keys and no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def keccak256(data: bytes) -> str:
    """Computes Keccak-256 hash (or standard SHA3-256 fallback) and returns 0x-prefixed hex string."""
    try:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256)
        k.update(data)
        return "0x" + k.hexdigest()
    except ImportError:
        # Standard library sha3_256 fallback when pycryptodome is not installed
        h = hashlib.sha3_256(data)
        return "0x" + h.hexdigest()

def compute_evidence_digest(evidence_payload: Dict[str, Any]) -> str:
    """Computes canonical Keccak-256 digest of an evidence object (FR-026)."""
    canonical_str = canonicalize_json(evidence_payload)
    return keccak256(canonical_str.encode('utf-8'))

def compute_commitment_hash(
    chain_id: int,
    market_id_hex: str,
    agent_address_hex: str,
    probability_bps: int,
    evidence_digest_hex: str,
    nonce_hex: str
) -> str:
    """
    Computes commitment hash matching Solidity abi.encodePacked:
    keccak256(abi.encodePacked(uint256, bytes32, address, uint256, bytes32, bytes32))
    """
    if not (0 <= probability_bps <= 10000):
        raise ValueError("probability_bps must be in range [0, 10000]")

    # Canonical ABI encodePacked:
    # uint256 -> 32 bytes big-endian
    # bytes32 -> 32 bytes
    # address -> 20 bytes
    # uint256 -> 32 bytes
    # bytes32 -> 32 bytes
    # bytes32 -> 32 bytes
    
    chain_id_bytes = chain_id.to_bytes(32, byteorder='big')
    
    market_id_clean = market_id_hex.lower().replace("0x", "")
    market_id_bytes = bytes.fromhex(market_id_clean.rjust(64, '0'))
    
    agent_clean = agent_address_hex.lower().replace("0x", "")
    agent_bytes = bytes.fromhex(agent_clean.rjust(40, '0'))
    
    prob_bytes = probability_bps.to_bytes(32, byteorder='big')
    
    evi_clean = evidence_digest_hex.lower().replace("0x", "")
    evi_bytes = bytes.fromhex(evi_clean.rjust(64, '0'))
    
    nonce_clean = nonce_hex.lower().replace("0x", "")
    nonce_bytes = bytes.fromhex(nonce_clean.rjust(64, '0'))
    
    packed = chain_id_bytes + market_id_bytes + agent_bytes + prob_bytes + evi_bytes + nonce_bytes
    return keccak256(packed)

def generate_nonce() -> str:
    """Generates secure 32-byte hexadecimal nonce."""
    return "0x" + secrets.token_hex(32)

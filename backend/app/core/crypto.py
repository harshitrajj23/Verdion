import hashlib
import json
import secrets
from typing import Any, Dict, List, Union
from eth_abi import encode
from eth_utils import keccak


def canonical_json(data: Any) -> str:
    """Produces deterministic, canonical JSON string with sorted keys and no unnecessary whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256_digest(content: Union[str, bytes, Dict, List]) -> str:
    """Computes a SHA-256 digest of arbitrary content, handling dicts/lists canonically."""
    if isinstance(content, (dict, list)):
        payload = canonical_json(content).encode("utf-8")
    elif isinstance(content, str):
        payload = content.strip().encode("utf-8")
    elif isinstance(content, bytes):
        payload = content
    else:
        payload = str(content).encode("utf-8")
    return "0x" + hashlib.sha256(payload).hexdigest()


def generate_nonce() -> str:
    """Generates a secure 32-byte hexadecimal nonce prefixed with 0x."""
    return "0x" + secrets.token_hex(32)


def compute_commitment_hash(
    chain_id: int,
    market_id: str,
    agent_id: str,
    probability: float,
    evidence_digest: str,
    nonce: str
) -> str:
    """
    Computes keccak256 commitment hash adhering to PRD 10.4:
    H(chainId, marketId, agentId, probability, evidenceDigest, nonce)
    Probability is scaled by 10,000 to represent basis points (0 to 10000) for exact EVM integer math.
    """
    prob_bps = int(round(probability * 10000))
    if not (0 <= prob_bps <= 10000):
        raise ValueError(f"Probability must be between 0.0 and 1.0, got {probability}")

    clean_digest = evidence_digest if evidence_digest.startswith("0x") else "0x" + evidence_digest
    digest_bytes = bytes.fromhex(clean_digest[2:].zfill(64))

    clean_nonce = nonce if nonce.startswith("0x") else "0x" + nonce
    nonce_bytes = bytes.fromhex(clean_nonce[2:].zfill(64))

    encoded = encode(
        ["uint256", "string", "string", "uint256", "bytes32", "bytes32"],
        [chain_id, str(market_id), str(agent_id), prob_bps, digest_bytes, nonce_bytes]
    )
    hash_bytes = keccak(encoded)
    return "0x" + hash_bytes.hex()


def verify_commitment_hash(
    expected_hash: str,
    chain_id: int,
    market_id: str,
    agent_id: str,
    probability: float,
    evidence_digest: str,
    nonce: str
) -> bool:
    """Verifies that the revealed probability, digest, and nonce match the committed hash."""
    recomputed = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=probability,
        evidence_digest=evidence_digest,
        nonce=nonce
    )
    return recomputed.lower() == expected_hash.lower()


def compute_brier_score(predictions: List[float], outcomes: List[int]) -> float:
    """
    Computes Brier Score: (1/N) * sum((p_i - y_i)^2), y_i in {0, 1}. Lower is better.
    """
    if not predictions or len(predictions) != len(outcomes):
        raise ValueError("Predictions and outcomes must have non-empty matching lengths")
    total = sum((p - y) ** 2 for p, y in zip(predictions, outcomes))
    return round(total / len(predictions), 6)


def compute_variance(values: List[float]) -> float:
    """
    Computes variance as disagreement metric: (1/N) * sum((p_i - mean(p))^2)
    """
    if not values:
        return 0.0
    mean_val = sum(values) / len(values)
    return round(sum((x - mean_val) ** 2 for x in values) / len(values), 6)


def compute_uncertainty_priority(impact: float, uncertainty: float, research_feasibility: float) -> float:
    """
    Computes Priority(q) = Impact(q) * Uncertainty(q) * ResearchFeasibility(q),
    each normalized to [0, 1].
    """
    i = max(0.0, min(1.0, impact))
    u = max(0.0, min(1.0, uncertainty))
    f = max(0.0, min(1.0, research_feasibility))
    return round(i * u * f, 4)

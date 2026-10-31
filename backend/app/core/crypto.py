import hashlib
import json
import secrets
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union
from eth_abi.packed import encode_packed
from eth_utils import keccak, to_checksum_address

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


def compute_canonical_sha256(content: Union[str, bytes, Dict, List]) -> str:
    """Canonical alias for compute_sha256_digest."""
    return compute_sha256_digest(content)


def generate_nonce() -> str:
    """Generates a secure 32-byte hexadecimal nonce prefixed with 0x."""
    return "0x" + secrets.token_hex(32)


def compute_commitment_hash(
    chain_id: int,
    market_id: Union[str, bytes],
    agent_id: str,
    probability: float,
    evidence_digest: Union[str, bytes],
    nonce: Union[str, bytes],
    wallet_address: Optional[str] = None
) -> str:
    """
    Computes keccak256 commitment hash adhering to PRD 10.4 and Solidity PredictionMarket.sol:
    keccak256(abi.encodePacked(uint256 chainId, bytes32 marketId, address agent, uint256 probabilityBps, bytes32 evidenceDigest, bytes32 nonce))

    The address must be the wallet registered in AgentRegistry, not a hash of agent_id.
    """
    target_wallet = wallet_address or agent_id
    if not (isinstance(target_wallet, str) and target_wallet.startswith("0x") and len(target_wallet) == 42):
        raise ValueError(
            f"A valid 0x Ethereum wallet address must be provided or found on the Agent record, got '{target_wallet}'."
        )
    try:
        agent_wallet = to_checksum_address(target_wallet)
    except Exception as e:
        raise ValueError(f"Invalid Ethereum wallet address '{target_wallet}': {e}")

    # Probability input unambiguous: accept float in [0,1] only. Reject anything else.
    if isinstance(probability, bool) or not isinstance(probability, float):
        raise ValueError(
            f"Probability must be a float in [0, 1], got {type(probability).__name__}: {probability}"
        )
    if not (0.0 <= probability <= 1.0):
        raise ValueError(f"Probability must be in range [0, 1], got {probability}")

    prob_bps = int((Decimal(str(probability)) * Decimal("10000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


    # Format market_id to 32 bytes
    if isinstance(market_id, bytes):
        market_bytes = market_id
    elif isinstance(market_id, str):
        clean_m = market_id.strip()
        if clean_m.startswith("0x"):
            market_bytes = bytes.fromhex(clean_m[2:].zfill(64))
        else:
            market_bytes = keccak(clean_m.encode("utf-8"))
    else:
        market_bytes = bytes(market_id)

    # Format evidence_digest to 32 bytes
    if isinstance(evidence_digest, bytes):
        digest_bytes = evidence_digest
    elif isinstance(evidence_digest, str):
        clean_d = evidence_digest.strip()
        clean_digest = clean_d if clean_d.startswith("0x") else "0x" + clean_d
        digest_bytes = bytes.fromhex(clean_digest[2:].zfill(64))
    else:
        digest_bytes = bytes(evidence_digest)

    # Format nonce to 32 bytes
    if isinstance(nonce, bytes):
        nonce_bytes = nonce
    elif isinstance(nonce, str):
        clean_n = nonce.strip()
        clean_nonce = clean_n if clean_n.startswith("0x") else "0x" + clean_n
        nonce_bytes = bytes.fromhex(clean_nonce[2:].zfill(64))
    else:
        nonce_bytes = bytes(nonce)

    # Solidity-equivalent encoding: abi.encodePacked(uint256, bytes32, address, uint256, bytes32, bytes32)
    encoded = encode_packed(
        ["uint256", "bytes32", "address", "uint256", "bytes32", "bytes32"],
        [chain_id, market_bytes, agent_wallet, prob_bps, digest_bytes, nonce_bytes]
    )
    hash_bytes = keccak(encoded)
    return "0x" + hash_bytes.hex()


# Option C and Phase 5E canonical alias
compute_forecast_commitment = compute_commitment_hash


def verify_commitment_hash(
    expected_hash: str,
    chain_id: int,
    market_id: str,
    agent_id: str,
    probability: float,
    evidence_digest: str,
    nonce: str,
    wallet_address: Optional[str] = None
) -> bool:
    """Verifies that the revealed probability, digest, and nonce match the committed hash."""
    recomputed = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=probability,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=wallet_address
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

"""
Cross-Language Cryptographic Tests for Evaluator Threshold Governance (PRD-SC-008)
and MultiSig Pause Governance (PRD-SEC-015).

Validates EIP-712 signature verification, threshold checks, replay defenses,
domain separation, and adversarial rejection scenarios matching Solidity contract logic.
"""

import pytest
import eth_abi
from eth_account import Account
from web3 import Web3


EIP712_DOMAIN_TYPEHASH = Web3.keccak(
    text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
)

RESOLUTION_TYPEHASH = Web3.keccak(
    text="MarketResolution(bytes32 marketId,uint8 outcome,uint256 nonce,bytes32 evidenceDigest)"
)


def compute_domain_separator(name: str, version: str, chain_id: int, contract_address: str) -> bytes:
    encoded = eth_abi.encode(
        ['bytes32', 'bytes32', 'bytes32', 'uint256', 'address'],
        [
            EIP712_DOMAIN_TYPEHASH,
            Web3.keccak(text=name),
            Web3.keccak(text=version),
            chain_id,
            Web3.to_checksum_address(contract_address)
        ]
    )
    return Web3.keccak(encoded)


def compute_resolution_digest(
    domain_separator: bytes,
    market_id: bytes,
    outcome: int,
    nonce: int,
    evidence_digest: bytes
) -> bytes:
    struct_hash = Web3.keccak(
        eth_abi.encode(
            ['bytes32', 'bytes32', 'uint8', 'uint256', 'bytes32'],
            [RESOLUTION_TYPEHASH, market_id, outcome, nonce, evidence_digest]
        )
    )
    return Web3.keccak(b"\x19\x01" + domain_separator + struct_hash)


def sign_hash_hex(account: Account, digest: bytes) -> str:
    signed = account.unsafe_sign_hash(digest)
    return "0x" + signed.signature.hex()


class MockSolidityThresholdEvaluator:
    """Python simulation of the Solidity ThresholdEvaluator contract state and execution logic."""

    def __init__(self, evaluators: list, threshold: int, chain_id: int = 11155111, contract_address: str = "0x" + "11"*20):
        self.chain_id = chain_id
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.evaluators = set(Web3.to_checksum_address(e) for e in evaluators)
        self.threshold = threshold
        self.domain_separator = compute_domain_separator("VERIDION_EVALUATOR", "1", self.chain_id, self.contract_address)
        self.used_nonces = set()
        self.resolved_markets = {}

    def get_digest(self, market_id: bytes, outcome: int, nonce: int, evidence_digest: bytes) -> bytes:
        return compute_resolution_digest(self.domain_separator, market_id, outcome, nonce, evidence_digest)

    def resolve_market(self, market_id: bytes, outcome: int, nonce: int, evidence_digest: bytes, signatures: list):
        if market_id in self.resolved_markets:
            raise ValueError("ThresholdEvaluator: market already resolved")
        if (market_id, nonce) in self.used_nonces:
            raise ValueError("ThresholdEvaluator: nonce already used")
        if outcome not in (0, 1):
            raise ValueError("ThresholdEvaluator: outcome must be 0 or 1")
        if len(signatures) < self.threshold:
            raise ValueError("ThresholdEvaluator: threshold not reached")

        digest = self.get_digest(market_id, outcome, nonce, evidence_digest)

        recovered_signers = []
        last_signer_int = 0

        for sig in signatures:
            signer = Account._recover_hash(digest, signature=sig)
            signer_addr = Web3.to_checksum_address(signer)
            signer_int = int(signer_addr, 16)

            if signer_addr not in self.evaluators:
                raise ValueError("ThresholdEvaluator: unauthorized signer")
            if signer_int <= last_signer_int:
                raise ValueError("ThresholdEvaluator: signatures must be strictly ascending (no duplicates)")

            last_signer_int = signer_int
            recovered_signers.append(signer_addr)

        self.used_nonces.add((market_id, nonce))
        self.resolved_markets[market_id] = outcome
        return True


@pytest.fixture
def evaluator_setup():
    accounts = [Account.create() for _ in range(3)]
    # Sort accounts by address in ascending numerical order for canonical Ethereum signature aggregation
    accounts.sort(key=lambda a: int(a.address, 16))

    evaluator_addresses = [a.address for a in accounts]
    contract = MockSolidityThresholdEvaluator(evaluators=evaluator_addresses, threshold=2)

    market_id = Web3.keccak(text="market_cjeu_2024_landmark")
    evidence_digest = Web3.keccak(text="curia_ruling_text_hash")
    nonce = 1
    outcome = 1

    return {
        "accounts": accounts,
        "evaluator_addresses": evaluator_addresses,
        "contract": contract,
        "market_id": market_id,
        "evidence_digest": evidence_digest,
        "nonce": nonce,
        "outcome": outcome
    }


def test_valid_threshold_resolution(evaluator_setup):
    """Test 2 of 3 evaluators sign; resolution succeeds."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    digest = c.get_digest(m_id, outcome, nonce, e_dig)

    # Sign with first two evaluators (already in ascending address order)
    sig1 = sign_hash_hex(accs[0], digest)
    sig2 = sign_hash_hex(accs[1], digest)

    success = c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig2])
    assert success is True
    assert c.resolved_markets[m_id] == 1


def test_below_threshold_rejection(evaluator_setup):
    """Test 1 of 3 evaluators signs when threshold is 2; reverts."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    digest = c.get_digest(m_id, outcome, nonce, e_dig)
    sig1 = sign_hash_hex(accs[0], digest)

    with pytest.raises(ValueError, match="threshold not reached"):
        c.resolve_market(m_id, outcome, nonce, e_dig, [sig1])


def test_duplicate_signature_rejection(evaluator_setup):
    """Test same evaluator signs twice; fails ascending duplicate check."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    digest = c.get_digest(m_id, outcome, nonce, e_dig)
    sig1 = sign_hash_hex(accs[0], digest)

    with pytest.raises(ValueError, match="must be strictly ascending"):
        c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig1])


def test_unauthorized_signer_rejection(evaluator_setup):
    """Test signature from an external unauthorized address; reverts."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    impostor = Account.create()
    digest = c.get_digest(m_id, outcome, nonce, e_dig)

    pair = [accs[0], impostor]
    pair.sort(key=lambda a: int(a.address, 16))

    sig1 = sign_hash_hex(pair[0], digest)
    sig2 = sign_hash_hex(pair[1], digest)

    with pytest.raises(ValueError, match="unauthorized signer"):
        c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig2])


def test_replay_attack_rejection(evaluator_setup):
    """Test replaying the identical resolution transaction; reverts."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    digest = c.get_digest(m_id, outcome, nonce, e_dig)
    sig1 = sign_hash_hex(accs[0], digest)
    sig2 = sign_hash_hex(accs[1], digest)

    c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig2])

    with pytest.raises(ValueError, match="already resolved"):
        c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig2])


def test_domain_separation_wrong_chain_id_rejected(evaluator_setup):
    """Test signature created with Mainnet chainId (1) rejected on Sepolia (11155111)."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    # Attacker crafts digest using chainId 1 instead of 11155111
    wrong_domain = compute_domain_separator("VERIDION_EVALUATOR", "1", 1, c.contract_address)
    wrong_digest = compute_resolution_digest(wrong_domain, m_id, outcome, nonce, e_dig)

    sig1 = sign_hash_hex(accs[0], wrong_digest)
    sig2 = sign_hash_hex(accs[1], wrong_digest)

    # When validated by contract on chainId 11155111, recovered address will be invalid
    with pytest.raises(ValueError, match="unauthorized signer"):
        c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig2])


def test_domain_separation_wrong_contract_address_rejected(evaluator_setup):
    """Test signature created for Contract A rejected by Contract B."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]
    outcome = evaluator_setup["outcome"]

    other_contract_addr = "0x" + "22"*20
    wrong_domain = compute_domain_separator("VERIDION_EVALUATOR", "1", c.chain_id, other_contract_addr)
    wrong_digest = compute_resolution_digest(wrong_domain, m_id, outcome, nonce, e_dig)

    sig1 = sign_hash_hex(accs[0], wrong_digest)
    sig2 = sign_hash_hex(accs[1], wrong_digest)

    with pytest.raises(ValueError, match="unauthorized signer"):
        c.resolve_market(m_id, outcome, nonce, e_dig, [sig1, sig2])


def test_outcome_tampering_rejected(evaluator_setup):
    """Test evaluators signed for outcome 0, but adversary submits outcome 1; reverts."""
    c = evaluator_setup["contract"]
    accs = evaluator_setup["accounts"]
    m_id = evaluator_setup["market_id"]
    e_dig = evaluator_setup["evidence_digest"]
    nonce = evaluator_setup["nonce"]

    # Evaluators signed for outcome 0
    signed_outcome = 0
    digest = c.get_digest(m_id, signed_outcome, nonce, e_dig)
    sig1 = sign_hash_hex(accs[0], digest)
    sig2 = sign_hash_hex(accs[1], digest)

    # Adversary attempts to resolve with outcome 1
    tampered_outcome = 1
    with pytest.raises(ValueError, match="unauthorized signer"):
        c.resolve_market(m_id, tampered_outcome, nonce, e_dig, [sig1, sig2])

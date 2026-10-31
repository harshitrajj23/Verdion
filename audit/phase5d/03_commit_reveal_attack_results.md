# Phase 5D — Commit-Reveal Cryptographic Protocol Attack Assessment & 20-Vector Matrix

## Executive Summary

An adversarial audit was conducted on the commit-reveal forecasting protocol across both Python backend services and EVM smart contracts. The audit compared byte-for-byte encodings, analyzed `abi.encodePacked` collision properties, tested replay resistance across chains, markets, and forecasters, and validated a comprehensive 20-vector attack test matrix.

---

## 1. Byte-for-Byte Encoding Comparison: Solidity vs. Python

The actual on-chain implementation in [`contracts/src/PredictionMarket.sol`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/contracts/src/PredictionMarket.sol#L259-L268) evaluates:

```solidity
bytes32 expectedHash = keccak256(
    abi.encodePacked(
        block.chainid,      // uint256 (32 bytes)
        marketId,           // bytes32 (32 bytes)
        msg.sender,         // address (20 bytes)
        probabilityBps,     // uint256 (32 bytes, 0..10000 basis points)
        evidenceDigest,     // bytes32 (32 bytes)
        nonce               // bytes32 (32 bytes)
    )
);
```

The corresponding Python reference implementation in [`backend/app/core/crypto.py`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/core/crypto.py#L101-L106) executes:

```python
encoded = encode_packed(
    ["uint256", "bytes32", "address", "uint256", "bytes32", "bytes32"],
    [chain_id, market_bytes, agent_wallet, prob_bps, digest_bytes, nonce_bytes]
)
hash_bytes = keccak(encoded)
```

### Exact Memory Layout
$$\begin{array}{|c|c|c|c|}
\hline
\textbf{Parameter} & \textbf{Solidity Type} & \textbf{Byte Width} & \textbf{Memory Offset} \\
\hline
\text{chainId} & \text{uint256} & 32\text{ bytes} & [0..31] \\
\text{marketId} & \text{bytes32} & 32\text{ bytes} & [32..63] \\
\text{agentWallet} & \text{address} & 20\text{ bytes} & [64..83] \\
\text{probabilityBps} & \text{uint256} & 32\text{ bytes} & [84..115] \\
\text{evidenceDigest} & \text{bytes32} & 32\text{ bytes} & [116..147] \\
\text{nonce} & \text{bytes32} & 32\text{ bytes} & [148..179] \\
\hline
\textbf{Total Packed Length} & & \mathbf{180\text{ bytes}} & \\
\hline
\end{array}$$

### Analysis of `abi.encodePacked` Collision Vulnerability
In standard Solidity, `abi.encodePacked` with multiple dynamic types (e.g. `string`, `bytes`) is vulnerable to length-extension and delimiter-shifting collisions (e.g., `("AB", "CD")` vs `("A", "BCD")`).
- **Audit Finding:** In VERIDION's schema, **all 6 parameters are strictly fixed-width types**. Because every parameter occupies an unvarying byte width (32, 32, 20, 32, 32, 32), field boundaries cannot shift or overlap. Dynamic concatenation collisions are **mathematically impossible** within this schema.
- **Domain Separation Finding:** The pre-image explicitly incorporates `chainId` (preventing cross-chain replay) and `agentWallet` (preventing copycat front-running). However, it does not bind `contractAddress`. In multi-tenant environments, if identical `marketId` values were initialized across multiple contract deployments on the same chain, commitments could be replayed. Recommendations for future V2 contracts include adding `address(this)` into the packing tuple.

---

## 2. 20-Vector Attack Test Matrix Results

All 20 adversarial attack vectors were implemented and executed in [`backend/tests/test_phase5d_adversarial.py`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/tests/test_phase5d_adversarial.py):

| Vector | Attack Description | Expected Defense Behavior | Result |
| :---: | :--- | :--- | :---: |
| **01** | Correct commitment & reveal | Digest match; verification succeeds | **PASS** |
| **02** | Changed probability ($0.825 \rightarrow 0.824$) | Pre-image hash mismatch; rejected | **PASS** |
| **03** | Changed secret nonce | Pre-image hash mismatch; rejected | **PASS** |
| **04** | Changed market ID | Pre-image hash mismatch; rejected | **PASS** |
| **05** | Cross-market replay attack | Hash bound to `marketId`; rejected | **PASS** |
| **06** | Front-running copycat (attacker wallet copies hash) | Hash bound to `msg.sender`; rejected | **PASS** |
| **07** | Cross-chain replay (Mainnet vs Sepolia) | Hash bound to `chainId`; rejected | **PASS** |
| **08** | Evidence digest alteration | Pre-image hash mismatch; rejected | **PASS** |
| **09** | Negative probability ($p = -0.1$) | Range validation raises `ValueError` | **PASS** |
| **10** | Probability $> 1.0$ ($p = 1.0001$) | Range validation raises `ValueError` | **PASS** |
| **11** | Malformed type (boolean $p = \text{True}$) | Type validation raises `ValueError` | **PASS** |
| **12** | Malformed Ethereum address string | Address validation raises `ValueError` | **PASS** |
| **13** | 1-bit flip in 256-bit nonce | Avalanche effect produces complete mismatch | **PASS** |
| **14** | Nonce entropy inspection | Generated via `secrets.token_hex(32)` (256 bits) | **PASS** |
| **15** | Address case-insensitivity (checksum vs lower) | EIP-55 checksum normalization matches | **PASS** |
| **16** | Zero probability boundary ($p = 0.0$) | Encoded as `0` bps; matches | **PASS** |
| **17** | One probability boundary ($p = 1.0$) | Encoded as `10000` bps; matches | **PASS** |
| **18** | Basis point rounding half-up ($0.8256 \rightarrow 8256$) | Deterministic rounding verified | **PASS** |
| **19** | Raw string vs Hex `marketId` handling | Deterministic 32-byte conversion | **PASS** |
| **20** | Pre-image collision resistance (neighbor hash) | Negligible probability difference alters digest | **PASS** |

---

## 3. Confidentiality and Pre-Reveal Information Leakage

1. **Information Disclosed at Commitment Time:**
   - Forecaster Wallet Address (`msg.sender`)
   - Target Market Identifier (`marketId`)
   - Submission Timestamp
   - 32-Byte Keccak-256 Commitment Digest
2. **Zero Information Leakage:**
   - The probability prediction $p$ and evidence digest are blinded by 256 bits of cryptographic entropy in `nonce`.
   - Brute-force pre-image calculation across $2^{256}$ states is computationally infeasible.
   - Nonce values remain in secure local client memory and are never sent to the backend, audit logs, or smart contract before the reveal window opens.

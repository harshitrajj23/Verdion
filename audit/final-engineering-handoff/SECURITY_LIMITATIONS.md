# VERIDION — Security Review & Operational Limitations

## 1. Hardened Security Controls

1. **Input Sanitization & Injection Defense:** Case facts and external inputs are evaluated via strict Pydantic models. Prompt injection in case facts is ignored by deterministic deontic AST rules.
2. **Untrusted Legal Evidence Handling:** External legal source passages are treated as untrusted inputs. They are strictly bounded by cryptographic SHA-256 digests and validated across 9 dimensions before entering decision synthesis.
3. **Commit-Reveal Replay Protection:** Forecast commitments bind `chainId`, `marketId`, and `agentWallet` into the keccak256 hash, preventing cross-market, cross-chain, or identity-spoofing replay attacks.
4. **Fail-Closed Evidence Verification:** Any passage integrity failure, jurisdictional mismatch, temporal expiration, or unauthenticated source immediately sets `is_fully_grounded: False` and requires human review.

## 2. Operational Limitations & Disclosures

- **Prospective Live Judicial Cases ($N = 0$):** Zero live European court cases are pending live outcome adjudication. All forecasting metrics reflect synthetic benchmark scenarios and historical CJEU landmark precedents.
- **Remote Model Provider Offline Fallback:** When remote API keys (`HUGGINGFACE_API_KEY`, `OPENAI_COMPATIBLE_API_KEY`) are unset, the system falls back to deterministic statutory exception rules and explicitly labels execution mode as `DETERMINISTIC_FALLBACK`.

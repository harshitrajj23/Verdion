# Audit 14: Remaining Blockers and Operational Disclosures

## 1. Identified Operational Boundaries
1. **Deployer Sepolia Balance**: Deployer address `0xF733bB7fe878B3830c2B1a1E13837494D28c50E2` currently holds 0 testnet ETH. All 5 contracts are already deployed with active bytecode and support real read calls. New write transactions require funding or explicit operator authorization.
2. **Third-Party Cloud LLM API Keys**: Hugging Face token is optional. When absent, the system operates in `DETERMINISTIC_RULES` mode with full disclosure in `ConfidenceContract`.
3. **Judicial Prospective Outcomes**: N=0 prospective cases have been resolved in live courtrooms; historical CJEU benchmark dataset is used for retrospective calibration.

# Audit 05: Model Provider Reality & Inference Verification

## 1. Inference Modes and Transparency
VERDION supports dual-path inference:
- **Cloud/Local Model Inference**: Hugging Face Inference API / Ollama (`HF_MODEL_ID`, `OLLAMA_ENDPOINT`).
- **Deterministic Rule Engine**: High-fidelity expert system evaluating GDPR Articles 5, 6, 9, 22, and 89.

## 2. Zero-Hidden-Fallback Guarantee
When model inference is unconfigured or unavailable, VERDION:
1. Discloses `execution_mode: DETERMINISTIC_RULES` in the execution output.
2. Marks `confidence_contract.confidence_type: RULE_DERIVED`.
3. Sets `calibration_status: HEURISTIC_BOUNDED`.
4. Never fabricates probabilistic hallucinations as live LLM tokens.

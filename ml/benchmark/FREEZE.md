# Benchmark Pipeline Freeze & Ablation Designation

## 1. Pipeline Designation

* **Primary Pipeline**: **v1** ([`results_train_live.json`](file:///Users/harshitrajsingh/verdion/ml/benchmark/results_train_live.json))
* **Labeled Ablation**: **v2** ([`results_train_live_v2.json`](file:///Users/harshitrajsingh/verdion/ml/benchmark/results_train_live_v2.json))
* **Reason**: v2 was not selected on train means. While v2 perfectly separated positive cases ($y=1 \implies p=0.7500$, Brier $0.0625$), the stricter contract rubric framing introduced high false positive predictions on negative cases ($y=0 \implies p \ge 0.6500$, Brier $0.5625$). As a result, v2's mean Brier score increased to **0.2354**, compared to v1's mean Brier score of **0.1611**. Consequently, v1 remains the primary baseline pipeline, and v2 is preserved as a documented ablation.

---

## 2. Git Commit Lineage

* **v1 Primary Pipeline Commit**: `d2e1ca7` (`feat(benchmark): live train pipeline results, quarantine isolation, and audit runners`)
* **v2 Ablation Pipeline Commit**: `8c9dc7b` (`feat(benchmark): v2 forecaster ablation (conflict section and PredictionMarket event wording)`)
* **Current HEAD**: `8c9dc7b` (prior to freezing documentation)

---

## 3. Forecaster System Prompt SHA-256 Digests

The SHA-256 digests were computed by extracting the exact prompt tuple from `agent_swarm.py` at each respective commit:

* **v1 Forecaster System Prompt SHA-256**:
  `62b4d321822dfbe89269332cbeca90a714297f39792e412c2c0b012919f1ff3a`
* **v2 Forecaster System Prompt SHA-256**:
  `a6c6880e3237370bccabcf428a86aaf2d0180243a63720dddc83f944057c9b40`

### Extraction Command Used:
```bash
python3 -c "
import subprocess, hashlib, re
def get_sha(commit):
    content = subprocess.check_output(['git', 'show', f'{commit}:ml/agents/agent_swarm.py'], text=True)
    fc_code = content[content.find('def run_quantitative_forecaster'):]
    match = re.search(r'system_prompt = \((.*?)\)\n\n\s+user_prompt', fc_code, re.DOTALL)
    prompt = eval('(' + match.group(1) + ')')
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

print('v1:', get_sha('d2e1ca7'))
print('v2:', get_sha('8c9dc7b'))
"
```

---

## 4. Resolution Event Definitions

* **v1 Event Definition**:
  * *Specification*: Probability that an independent evaluator identifies an unresolved compliance violation or legal liability under general statutory standards.
  * *Format*: `"The independent benchmark evaluator finds an unresolved compliance violation or legal liability for the described case facts."`
* **v2 Event Definition**:
  * *Specification*: Aligned directly with [`PredictionMarket.sol`](file:///Users/harshitrajsingh/verdion/contracts/src/PredictionMarket.sol) line 33 resolution criterion (`proposedOutcome: true = YES / COMPLIANCE_GAP, false = NO`).
  * *Format*: `"The authorized evaluator proposes resolution outcome true (YES / COMPLIANCE_GAP: statutory compliance gap identified under evaluation rubric) for the described case facts."`

---

## 5. Placeholder Evidence Digest Status

* **Digest Value**: `0x0000000000000000` (zero-bytes stub)
* **Consequence**:
  Neither v1 nor v2 evaluations ingest a real canonical digest generated via `compute_evidence_digest`. Stored scores were not evaluated against real cryptographically linked evidence digests. The pipeline remains an unvalidated prototype until real Merkle/Keccak canonical evidence digests are wired from upstream roles into the prediction market contracts.

---

## 6. Held-Out Evaluation Status & Decision

* **Decision**: **not run, out of scope for the hackathon**
* **Status**: The 6 held-out test scenarios (`scen_15` through `scen_20`) have **NOT been run**.
* **Rationale**:
  - In strict compliance with the benchmark evaluation guidelines and evaluation protocol freeze, the held-out split (`scen_15`–`scen_20`) is held in blind reserve to preserve zero data leakage and guarantee zero train-set contamination.
  - Running held-out evaluation during development or pre-competition tuning would invalidate its role as an unbiased, unseen test set.
  - Consequently, the official hackathon submission evaluation figures reflect the primary baseline pipeline (`v1`) across the 14 training scenarios, and held-out test evaluation is designated as **not run, out of scope for the hackathon**.

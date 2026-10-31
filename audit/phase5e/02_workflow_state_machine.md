# VERIDION PHASE 5E AUDIT REPORT — ARTIFACT 02
# Workflow State Machine Specification & Verification

**Document Reference:** `VERIDION-AUDIT-P5E-002`  
**Phase:** 5E (Option C — Auditable Regulatory Decision Infrastructure)  
**Date of Verification:** 2026-10-28  
**Verification Lead:** Principal Systems Architect & Quality Assurance Lead  
**State Machine Status:** **STRICTLY ENFORCED & IDEMPOTENT**

---

## 1. Formal State Machine Definition

The Option C lifecycle is implemented as an explicit, deterministic finite state machine defined in [`WorkflowService`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/services/workflow_service.py) via the `WorkflowState` enumeration:

```python
class WorkflowState(str, Enum):
    CASE_CREATED = "CASE_CREATED"
    EVIDENCE_BOUND = "EVIDENCE_BOUND"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ANALYSIS_RECORDED = "ANALYSIS_RECORDED"
    DECISION_VERIFIED = "DECISION_VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FORECAST_OPEN = "FORECAST_OPEN"
    FORECAST_COMMITTED = "FORECAST_COMMITTED"
    FORECAST_REVEALED = "FORECAST_REVEALED"
    REVEAL_EXPIRED = "REVEAL_EXPIRED"
    RESOLUTION_PENDING = "RESOLUTION_PENDING"
    RESOLVED = "RESOLVED"
    DISPUTED = "DISPUTED"
    SCORED = "SCORED"
    AUDIT_PACKAGE_VERIFIED = "AUDIT_PACKAGE_VERIFIED"
    UNANCHORED = "UNANCHORED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
```

---

## 2. Permitted State Transitions Table

| Current State | Permitted Next States | Authorization / Actor Role | Required Artifacts / Pre-conditions |
| :--- | :--- | :--- | :--- |
| `CASE_CREATED` | `EVIDENCE_BOUND`, `INSUFFICIENT_EVIDENCE`, `CANCELLED` | Case Author / Orchestrator | Case entity saved with valid scope and facts. |
| `EVIDENCE_BOUND` | `ANALYSIS_RECORDED`, `INSUFFICIENT_EVIDENCE`, `CANCELLED` | Analysis Engine / Orchestrator | Minimum 1 valid official passage with SHA-256 digest bound. |
| `INSUFFICIENT_EVIDENCE` | `EVIDENCE_BOUND`, `CANCELLED` | Case Author / Legal Analyst | Updated query or supplementary authoritative legal corpus. |
| `ANALYSIS_RECORDED` | `DECISION_VERIFIED`, `PARTIALLY_VERIFIED`, `FAILED` | Decision Service / Verifier | VCP-1 canonical decision record computed and saved. |
| `DECISION_VERIFIED` | `FORECAST_OPEN`, `AUDIT_PACKAGE_VERIFIED`, `CANCELLED` | Market Creator / Auditor | Zero-trust verification report returns `is_valid: true`. |
| `PARTIALLY_VERIFIED` | `DECISION_VERIFIED`, `FORECAST_OPEN`, `AUDIT_PACKAGE_VERIFIED` | Case Author / Auditor | Unresolved citations or partial grounding acknowledged. |
| `FORECAST_OPEN` | `FORECAST_COMMITTED`, `REVEAL_EXPIRED`, `CANCELLED` | Forecaster / Market Agent | Market registered with resolution criteria and opening timestamp. |
| `FORECAST_COMMITTED`| `FORECAST_REVEALED`, `REVEAL_EXPIRED`, `CANCELLED` | Forecaster / Market Agent | 32-byte commitment hash recorded on-chain or in ledger. |
| `FORECAST_REVEALED`  | `RESOLUTION_PENDING`, `RESOLVED`, `CANCELLED` | Market Evaluator / Forecaster | Probability, nonce, and evidence digest byte-equality verified. |
| `REVEAL_EXPIRED`    | `RESOLUTION_PENDING`, `RESOLVED`, `CANCELLED` | Evaluator / System | Reveal deadline passed without valid reveal submitted. |
| `RESOLUTION_PENDING`| `RESOLVED`, `DISPUTED`, `CANCELLED` | Authorized Evaluator | Outcome occurred; official resolution document awaited. |
| `RESOLVED`          | `SCORED`, `DISPUTED` | Settlement Engine | Authoritative resolution source reference and outcome recorded. |
| `DISPUTED`          | `RESOLVED`, `CANCELLED` | Dispute Board / Admin | Formal adjudication review and amended resolution evidence. |
| `SCORED`            | `AUDIT_PACKAGE_VERIFIED` | Settlement Engine / Verifier | Brier scores and quadratic payoff recalculations verified. |
| `AUDIT_PACKAGE_VERIFIED` | *Terminal State* | Independent Auditor | Standalone audit package offline validation passes. |

---

## 3. Invalid Transition & Concurrency Enforcement

Any attempt to execute an unpermitted transition (e.g. transitioning directly from `CASE_CREATED` to `FORECAST_COMMITTED` or `SCORED`) raises a strict `InvalidStateTransitionException`:

```python
if to_state not in allowed:
    raise InvalidStateTransitionException(
        f"Invalid workflow transition from '{from_state}' to '{to_state}' for case '{case_id}'.",
        details={"current_state": from_state, "target_state": to_state, "allowed_transitions": allowed}
    )
```

### Idempotency Behavior
- If an operation requests a transition where `case.status == to_state`, the service detects the state identity, logs an idempotent audit trace, and returns immediately without duplicate audit events or state mutation.
- When an `idempotency_key` is supplied, repeated network requests within the active lease window return the exact recorded execution result.

---

## 4. Verification in Test Suite

The state machine logic was verified via `test_workflow_state_transition_idempotency_and_validation` in `backend/tests/test_phase5e_workflow.py`:
- `CASE_CREATED -> EVIDENCE_BOUND`: **PASS**
- `EVIDENCE_BOUND -> EVIDENCE_BOUND` (Idempotent replay): **PASS (No duplicate events)**
- `EVIDENCE_BOUND -> SCORED` (Illegal jump): **REJECTED (`InvalidStateTransitionException` confirmed)**

# VERIDION PHASE 5B — CASE ANALYSIS SOURCE TRACEABILITY REPORT

**Document ID:** `audit/phase5b/05_case_analysis_source_traceability.md`  
**Execution Timestamp:** 2026-10-27T17:05:00+05:30  
**Focus Area:** End-to-End Linkage between Ingested Sources, Swarm Agents, and Legal Claims  

---

## 1. Executive Summary

Legal intelligence systems must never treat substring matches or digest verifications as proof of legal entailment. In Phase 5B, the reasoning engine (`AgentService` and `CaseService`) was updated so that every generated legal claim explicitly links to its supporting document identifiers and provides transparent disclosures regarding the reasoning engine and verification mode.

---

## 2. Updated Claim Generation Schema (`backend/app/schemas/agent.py`)

The `ClaimOutput` data contract was enhanced with five explicit provenance and verification attributes:

```python
class ClaimOutput(BaseModel):
    claim_text: str
    claim_type: str
    assumptions: List[str]
    confidence: float
    confidence_rationale: str
    is_supported: bool
    evidence_refs: List[EvidenceRef]
    
    # Phase 5B Traceability & Entailment Disclosures
    source_document_ids: List[str]
    analysis_engine: str = "deterministic_rule_engine_v1.2"
    execution_mode: str = "DETERMINISTIC_RULES"  # LIVE_MODEL, DETERMINISTIC_RULES, CACHE
    verification_mode: str = "MECHANICAL_CITATION_MATCH"  # MECHANICAL_CITATION_MATCH, SEMANTIC_LLM_ASSESSMENT, UNVERIFIED
    entailment_disclosure: str = (
        "Mechanical citation and digest verification confirms textual match; "
        "does not constitute proof of semantic legal entailment."
    )
```

---

## 3. Legal Researcher & Interpreter Execution Trace

When `AgentService.run_legal_researcher` or `run_legal_interpreter` processes a case:
1. `RetrievalService.retrieve_passages` queries active passages from `evidence_passages` joined with `source_documents`.
2. When live ingested sources (such as `doc_eurlex_32024r1689` or `doc_cjeu_62021cj0487`) are present in the database, they are retrieved dynamically based on term relevance to the case facts.
3. Every claim records:
   - `source_document_ids`: e.g. `['doc_eurlex_32024r1689']`.
   - `analysis_engine`: `"deterministic_rule_engine_v1.2"`.
   - `verification_mode`: `"MECHANICAL_CITATION_MATCH"`.
   - `entailment_disclosure`: Discloses that textual citation match is verified, but judicial interpretation remains a human/legal prerogative.

---

## 4. Verification Verdict

All claim outputs in the agent swarm now trace directly to authoritative source documents in `veridion.db`, while truthfully declaring the mechanical nature of deterministic citation verification.

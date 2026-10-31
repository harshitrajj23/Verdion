# VERIDION PHASE 3 — LEGAL SOURCE & VERIFICATION INTEGRITY REPORT
**Document Reference:** `audit/phase3/05_legal_source_and_verification_integrity.md`  
**Evaluation Standard:** PRD Sections 14, 16.2, 16.8  
**Timestamp:** 2026-10-27T06:42:30Z  
**Corpus Root:** `ml/corpus/` & `backend/app/data/curated_corpus.json`

---

## 1. Traceable Legal Source Ingestion Pipeline

VERIDION establishes an unbroken, cryptographically verified path from raw legal sources to claims appearing in the final report:

1. **Source Registration:**
   - Raw statutory texts and regulatory statements (e.g., *Regulation (EU) 2016/679 (GDPR)*, *EDPB Statement 01/2024*, *EU AI Act*) are ingested with metadata: authority, jurisdiction, publication date, effective date, and source URL.
   - A canonical document-level SHA-256 digest is generated over serialized metadata.
2. **Passage Segmentation & Granular Identifiers:**
   - Text is segmented into retrievable passages with stable section references (e.g., `gdpr_art_5_1_b`, `gdpr_art_6_1_f`, `gdpr_art_13_1`).
   - Each passage receives a SHA-256 digest computed over its exact normalized content:
     `digest = SHA-256(passage_text)`
3. **Passage Persistence & Indexing:**
   - Passages are durably stored in the `evidence_passages` table in SQLite.
   - Text is sanitized against system-prompt injection tokens (e.g., stripping `### System:` and `<script>` sequences).
4. **Context-Aware Retrieval:**
   - `RetrievalService.retrieve_passages` performs jurisdiction-scoped term-overlap and semantic matching over passage text and statutory references.
5. **Cryptographic Claim Grounding:**
   - `AgentService.run_evidence_verifier` verifies that every cited passage in a claim exists in `evidence_passages` and that its SHA-256 digest matches the stored record.

---

## 2. Statutory-Clause Segmentation v1.2.0 Verification

Phase 2 enhanced `ml/agents/validator.py` with the v1.2.0 sub-clause splitter. In Phase 3:
- Verified that long statutory articles containing enumerations (e.g., `(a)`, `(b)`, `(1)`, `(2)`, `;`) are split at true syntactic and sub-clause boundaries.
- Re-tested the 5 segmentation regression scenarios in `ml/agents/test_segmentation_v1_2.py`:
  - `test_complex_multiclause_statutory_split`: Passes.
  - `test_semicolon_clause_enumeration`: Passes.
  - `test_numbered_statutory_subsections`: Passes.
  - `test_short_sentence_no_split`: Passes.
  - `test_citation_boundary_integrity`: Passes.
- All 99 automated tests in the regression suite continue to pass.

---

## 3. Grounding vs. URL Checking Distinction

VERIDION explicitly rejects the fallacy that a valid URL equates to supporting legal evidence:
- A claim is marked `is_supported = True` if and only if the exact quoted passage text matches the cryptographic digest in `evidence_passages`.
- If an agent generates an assertion without a verified passage link, the claim status is marked `is_supported = False` and labeled `UNVERIFIED_ASSERTION`.
- In the final 10-section report, unverified claims are segregated into Section 8 (*Unresolved Questions & Evidence Bounties*) rather than masquerading as established law.

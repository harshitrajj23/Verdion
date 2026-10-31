# Phase 5C — Independent Audit Verifier & Zero-Trust Verification Engine

## Overview

A critical requirement of Option C is that an external auditor, opposing counsel, compliance inspector, or judicial authority must be able to verify a VERIDION decision record **without trusting VERIDION's servers, databases, agents, or frontend UI**.

To achieve this, VERIDION provides a standalone, zero-network verification engine: `AuditVerifier` (`backend/app/services/audit_verifier.py`).

---

## 1. Zero-Trust Verification Architecture

```
+----------------------------------------------------------------------------------+
| EXPORTABLE AUDIT PACKAGE (.json or .zip)                                         |
| 1. manifest.json: Checksums, export timestamp, verifier instructions             |
| 2. decision_record.json: Canonical decision record with digests                  |
| 3. evidence_documents/: Raw source text snapshots                                |
| 4. audit_events.json: Ordered sequence of hash-linked audit records               |
+----------------------------------------+-----------------------------------------+
                                         |
                                         v
+----------------------------------------------------------------------------------+
| STANDALONE AUDIT VERIFIER (audit_verifier.py / CLI)                              |
| - Runs on air-gapped machine with standard Python 3.10+                          |
| - Requires zero internet connection, zero API keys, zero DB access               |
|                                                                                  |
|   Step 1: Validate Manifest SHA-256 Checksums                                    |
|   Step 2: Re-serialize Canonical Decision Record (RFC 8785) & Compare Digest     |
|   Step 3: Verify Evidence Source Hashes & Passage Character Bounds               |
|   Step 4: Check Grounding of Claims to Validated Passages                        |
|   Step 5: Verify Keccak-256 Commit-Reveal Hashes for Forecasts                   |
|   Step 6: Mathematically Recalculate Brier Scores & Payoffs                      |
|   Step 7: Trace Audit Event Hash Chain & Recompute Merkle Root Checkpoint        |
+----------------------------------------+-----------------------------------------+
                                         |
                                         v
+----------------------------------------------------------------------------------+
| AUDIT VERIFICATION CERTIFICATE                                                   |
| - Overall Status: VERIFIED | PARTIALLY_VERIFIED | FAILED                         |
| - Explicit checklist of 7 cryptographic and mathematical proofs                  |
| - Detailed list of any discrepancies, missing records, or hash mismatches        |
+----------------------------------------------------------------------------------+
```

---

## 2. Verification Steps & Algorithms

### Step 1: Decision Record Canonical Integrity
The verifier extracts the `decision_record` dictionary, strips the `decision_record_digest` property, canonicalizes the remainder using RFC 8785 rules (Unicode NFC, sorted keys, compact separators), and computes $\text{SHA256}(\text{CanonicalBytes})$.
- **Pass Condition:** $\text{ComputedDigest} == \text{RecordedDigest}$.

### Step 2: Evidence Source & Passage Offsets
For each source document in `evidence_sources`:
- $\text{SHA256}(\text{document\_text}) == \text{content\_digest}$.
For each passage in `evidence_passages`:
- The passage text matches `document_text[char_start:char_end]`.
- $\text{SHA256}(\text{text\_excerpt}) == \text{passage\_digest}$.

### Step 3: Claim Citation Grounding
For each claim in `claims`:
- Every `passage_id` referenced in the claim must exist in the validated passage collection.
- Uncited or dangling claim citations are flagged as `UNGROUNDED_CLAIM`.

### Step 4: Commit-Reveal Pre-image Matching
For each forecast in `forecasts`:
- For revealed commitments, the verifier calculates:
  $$\text{keccak256}\Big(\text{abi.encodePacked}(\text{market\_id}, \text{outcome}, \text{nonce})\Big)$$
- If the result does not match `commitment_hash`, it flags `COMMITMENT_HASH_MISMATCH`.

### Step 5: Brier Scoring Recalculation
For resolved markets:
- The verifier independently evaluates $\text{Brier} = \sum_{k=1}^K (p_k - o_k)^2$ to 6 decimal places and compares against recorded settlement scores.

### Step 6: Audit Chain Continuity & Merkle Root Checkpoint
The verifier loops through `audit_event_links`:
1. Validates that sequence numbers increase by 1 without gaps.
2. Re-computes canonical payload digests.
3. Checks $\text{previous\_event\_digest}_i == \text{event\_digest}_{i-1}$.
4. Rebuilds the binary Merkle tree across all leaf digests and verifies that the resulting Merkle root equals `merkle_root`.

---

## 3. CLI & Programmatic Usage

### Offline CLI Execution
```bash
# Verify an exported audit package JSON artifact offline:
python -m backend.app.services.audit_verifier export_case_123_audit_package.json
```

### Output Certificate Example
```json
{
  "is_valid": true,
  "status": "VERIFIED",
  "decision_record_id": "dec_case_123_v1",
  "decision_record_digest_valid": true,
  "evidence_sources_verified": 2,
  "passages_verified": 4,
  "claims_verified": 3,
  "commitments_verified": 2,
  "scores_recalculated_valid": true,
  "audit_chain_length": 6,
  "audit_chain_valid": true,
  "merkle_root_valid": true,
  "merkle_root": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "discrepancies": []
}
```

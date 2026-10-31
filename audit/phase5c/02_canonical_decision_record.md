# Phase 5C — Canonical Decision Record & Serialization Specification

## Overview

A fundamental flaw in naive audit systems is hashing un-normalized JSON. In Python, JavaScript, and database drivers, JSON serialization can vary based on whitespace, key ordering, floating-point precision, and Unicode normalization forms (NFD vs. NFC). Hashing un-normalized representations produces divergent hashes across platforms, destroying offline reproducibility.

Option C specifies and implements **RFC 8785 Canonical JSON Serialization and Unicode NFC Hashing** in `backend/app/core/canonical.py`.

---

## 1. Canonical Serialization Rules

### Rule A: Recursive Key Sorting
All dictionary/object keys are sorted recursively in lexicographical UTF-8 byte order prior to serialization.

### Rule B: Unicode Normalization (NFC)
All string values and dictionary keys are normalized to **Unicode Normalization Form C (NFC)** using `unicodedata.normalize('NFC', text)`. This guarantees that characters like `é` (composed `\u00e9` vs decomposed `e\u0301`) yield identical byte sequences regardless of operating system or editor.

### Rule C: Floating-Point Determinism
Floating-point numbers in regulatory metrics (e.g., confidence scores, Brier scores, probabilities) are rounded to exactly **6 decimal places**. Floats with integer values are formatted with a trailing zero or standardized representation to avoid exponential notation variance (`1e-05` vs `0.000010`).

### Rule D: Timestamp Representation
All timestamps must be UTC ISO 8601 strings ending in `Z` (e.g., `2026-10-27T12:00:00Z`). Milliseconds are zero-padded or truncated deterministically.

### Rule E: Treatment of Null and Optional Fields
Keys with `None` values are preserved or omitted consistently according to schema definitions; dictionary fields are never randomly serialized as undefined or omitted.

### Rule F: Whitespace and Delimiters
Strict compact serialization without extraneous whitespace:
- Separators: `(",", ":")`
- No newlines or indentation in canonical hash payloads.

---

## 2. Schema Structure: `CanonicalDecisionRecord`

Defined in `backend/app/schemas/decision_record.py` under schema version `veridion_decision_record_v1.0.0`:

```json
{
  "schema_version": "veridion_decision_record_v1.0.0",
  "decision_record_id": "dec_case_123_v1",
  "case_id": "case_123",
  "factual_scope_version": 1,
  "engine_version": "veridion-engine-5c-v1.0.0",
  "timestamp": "2026-10-27T12:00:00Z",
  "question": "Does transferring EU personal data to a US third party without SCCs violate GDPR?",
  "factual_scope": { ... },
  "evidence_sources": [
    {
      "source_id": "src_gdpr_art44",
      "publisher": "European Parliament and Council",
      "official_id": "32016R0679",
      "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
      "jurisdiction": "EU",
      "doc_type": "REGULATION",
      "document_version": "2016-04-27",
      "normalization_procedure": "v1.0-clean_whitespace",
      "content_digest": "4a5e3...",
      "retrieved_at": "2026-10-27T10:00:00Z"
    }
  ],
  "evidence_passages": [
    {
      "passage_id": "pas_gdpr_art44_p1",
      "source_id": "src_gdpr_art44",
      "official_id": "32016R0679",
      "char_start": 12040,
      "char_end": 12450,
      "text_excerpt": "Any transfer of personal data which are undergoing processing...",
      "passage_digest": "9b1c2..."
    }
  ],
  "claims": [
    {
      "claim_id": "clm_001",
      "claim_type": "SYNTHESIS",
      "agent_type": "SYNTHESIS_SPECIALIST",
      "claim_text": "Transfer of personal data to a third country without adequacy or SCCs violates Article 44.",
      "passage_ids": ["pas_gdpr_art44_p1"],
      "confidence": 0.950000,
      "counterarguments": ["Derogations under Article 49 may apply in specific exceptional circumstances."],
      "unresolved_questions": []
    }
  ],
  "forecasts": [
    {
      "market_id": "mkt_case_123",
      "proposition": "Will the DPA issue an enforcement notice within 6 months?",
      "resolution_criteria": "Official publication in national DPA sanctions register",
      "resolution_source": "DPA Enforcement Portal",
      "opening_time": "2026-10-27T12:00:00Z",
      "closing_time": "2026-11-27T12:00:00Z",
      "outcomes": ["YES", "NO"],
      "status": "OPEN",
      "commitments": [],
      "resolution": null,
      "settlement": null
    }
  ],
  "audit_event_links": [
    {
      "event_id": 1,
      "event_type": "CASE_CREATED",
      "sequence_number": 1,
      "event_digest": "a1b2...",
      "previous_event_digest": "0000000000000000000000000000000000000000000000000000000000000000"
    }
  ],
  "merkle_root": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---

## 3. SHA-256 Digest Computation

The top-level `decision_record_digest` is computed strictly over the canonicalized JSON representation excluding the `decision_record_digest` field itself:

$$\text{CanonicalBytes} = \text{RFC8785\_Canonical}(\text{Record} \setminus \{\text{decision\_record\_digest}\})$$
$$\text{Digest} = \text{SHA256}(\text{CanonicalBytes})$$

This formulation guarantees that any party can independently reproduce the exact SHA-256 hash given the JSON artifact.

---

## 4. Backward Compatibility and Migration

1. **Schema Non-Destructive Addition:** The `decision_records` table was added to SQLite `veridion.db` via `DecisionRecordModel` without modifying or dropping existing tables.
2. **Schema Versioning:** The `schema_version` attribute allows future evolutions (e.g., `v1.1.0`) while legacy decision records can still be validated by the independent verifier using legacy rule sets.
3. **Database Migration Script:** `scripts/migrate_audit_chain.py` successfully backfilled sequential numbering and hash pointers for all 700 existing historical events with zero downtime and zero data loss.

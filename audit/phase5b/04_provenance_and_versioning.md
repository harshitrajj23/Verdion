# VERIDION PHASE 5B — PROVENANCE AND VERSIONING REPORT

**Document ID:** `audit/phase5b/04_provenance_and_versioning.md`  
**Execution Timestamp:** 2026-10-27T17:00:00+05:30  
**Entities Audited:** `source_documents`, `evidence_passages`  

---

## 1. Executive Summary

Phase 5B extends the Phase 5A provenance classification system into the legal evidence layer. Legal documents and evidence passages are no longer treated as uniform strings; they are formally segregated by their origin.

Bundled benchmark fixtures are explicitly labeled as `BUNDLED_FIXTURE` and isolated from claims of live official retrieval. Authentic documents retrieved from live gazettes carry the label `REMOTE_OFFICIAL_SOURCE`.

---

## 2. Provenance Taxonomy in the Legal Evidence Layer

| Provenance Label | Meaning | Applied To | Example Entities |
| :--- | :--- | :--- | :--- |
| **`REMOTE_OFFICIAL_SOURCE`** | Retrieved live from official government/statutory publisher; provenance URL, timestamp, and digest recorded. | Documents and passages fetched via `EURLexAdapter`, `CJEUAdapter`, `EDPBAdapter`. | `doc_eurlex_32024r1689`, `doc_cjeu_62021cj0487`, `doc_edpb_guidelines_032026_on_web_scrapin` |
| **`BUNDLED_FIXTURE`** | Bundled static benchmark corpus populated on startup. Contains authentic legal text but was ingested offline. | Curated corpus from `ml/corpus/` and `curated_corpus.json`. | `doc_gdpr_2016_679`, `doc_eu_ai_act_2024`, `doc_ccpa_cpra_2020` |
| **`USER_SUBMITTED`** | Legal text or contracts supplied by user. | User-uploaded evidence or contract clauses. | User case fact attachments |
| **`TEST`** | Temporary fixtures generated during pytest runs. | In-memory test suites (`sqlite+aiosqlite:///:memory:`). | Isolated test records |
| **`UNKNOWN`** | Provenance cannot be independently verified. | Historical untracked fragments. | Unverified external references |

---

## 3. Database Schema Changes & Backward-Compatible Migration

### 3.1 Schema Modifications (`backend/app/models/entities.py`)
```python
# SourceDocument entity
provenance = Column(String(32), default="BUNDLED_FIXTURE", nullable=True, index=True)

# EvidencePassage entity
provenance = Column(String(32), default="BUNDLED_FIXTURE", nullable=True, index=True)
```

### 3.2 Non-Destructive Migration Script (`scratch/migrate_phase5b.py`)
- Executed on `veridion.db`:
  - `ALTER TABLE source_documents ADD COLUMN provenance VARCHAR(32) DEFAULT 'BUNDLED_FIXTURE';`
  - `ALTER TABLE evidence_passages ADD COLUMN provenance VARCHAR(32) DEFAULT 'BUNDLED_FIXTURE';`
  - Existing 3 source documents and 10 passages backfilled to `BUNDLED_FIXTURE`.
  - Zero rows deleted; zero data destroyed.

---

## 4. Document Versioning & Change Detection

The ingestion pipeline handles version transitions deterministically:
1. When an adapter retrieves a document whose `source_id` already exists in `source_documents`:
   - It compares `doc.digest` with `existing.digest`.
   - **Case A (Exact Match):** Skips idempotently without creating duplicate rows (`duplicates_skipped += 1`).
   - **Case B (Different Digest):** Treats the revised document as a new minor version (`1.0` -> `1.1`), updates `version`, `digest`, `raw_content`, `retrieved_at`, and `provenance`, incrementing `new_versions += 1`.
2. Triggers an impact analysis on affected cases whose factual scope intersects with the new legislation.
3. Records an auditable event in `audit_events`.

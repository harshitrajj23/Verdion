# Audit 02: Strict Real-Data Architecture & Provenance Model

## 1. Provenance Schema Standard
Every primary artifact in VERDION conforms to a verifiable provenance contract:
- `source_id`: Canonical identifier (e.g., CELEX number, ECLI, or internal UUID)
- `source_url`: Official verified URL (must pass `validate_official_url` against whitelist)
- `content_hash`: Canonical SHA-256 digest of original raw text
- `retrieved_at`: ISO-8601 UTC timestamp of retrieval
- `temporal_cutoff`: Statutory cutoff date matching case assessment date
- `execution_mode`: `OPERATIONAL_REAL`, `DETERMINISTIC_RULES`, or `MODEL_INFERENCE`
- `verification_status`: `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `QUALIFIED`

## 2. Temporal Sequence Enforcement
Under Section 3.3, retrospective cases must never ingest future precedents. VERDION enforces this at the database and service layer in `JudicialPipelineService`:
- Query filters explicitly reject any evidence passage with `publication_date > case.assessment_date`.
- Verified in `backend/tests/test_judicial_pipeline.py::test_temporal_cutoff_prevents_future_leakage`.

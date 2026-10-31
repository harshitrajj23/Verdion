# Audit 08: Database and Persistence Reality Audit

## 1. Dual-Engine Persistence
- **Production Serverless Engine**: Neon PostgreSQL (`ep-billowing-sunset-azje04un-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb`) with `asyncpg`.
- **Local Development / Test Engine**: SQLite (`veridion.db`) with `aiosqlite`.

## 2. Schema Integrity
All 17 tables verified across both engines:
`cases`, `source_documents`, `agents`, `settlements`, `transaction_records`, `evidence_passages`, `claims`, `prediction_markets`, `evidence_bounties`, `audit_events`, `decision_records`, `analysis_jobs`, `reputation_records`, `claim_evidence_links`, `argument_edges`, `forecasts`, `evidence_submissions`.

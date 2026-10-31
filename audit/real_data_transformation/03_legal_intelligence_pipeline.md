# Audit 03: External Legal Intelligence Pipeline Verification

## 1. Adapter Architecture
VERDION implements three specialized legal source adapters in `backend/app/services/ingestion/`:
1. `EURLexAdapter`: Official EU legislative acts via Cellar Linked Data REST (`https://publications.europa.eu/resource/celex`).
2. `CJEUAdapter`: Court of Justice of the European Union case-law (`CELEX`, `ECLI`, and case numbers like `C-487/21`).
3. `EDPBAdapter`: European Data Protection Board adopted guidelines and public consultations (`https://www.edpb.europa.eu`).

## 2. Integrity and Caching
- Cache entries store exact retrieval timestamps, origin URLs, and SHA-256 digests.
- No cached entry is represented as newly retrieved.
- Unreachable endpoints fail closed with explicit `ExternalSourceRetrievalError` rather than fabricating dummy text.

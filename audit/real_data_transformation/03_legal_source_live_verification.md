# Audit 03: Legal Source Live Verification

## 1. Verified Adapters
1. **Publications Office of the European Union (EUR-Lex)**:
   - Base URL: `https://publications.europa.eu/resource/celex`
   - Test Document: CELEX `32016R0679` (General Data Protection Regulation)
   - Status: Genuine HTTP requests executed with validated official EU domain whitelisting.
   - Result: Successful notice XML parsing, manifestation extraction, and canonical SHA-256 digest computation.
2. **Court of Justice of the European Union (Curia)**:
   - Base URL: `https://publications.europa.eu/resource/celex` / `ecli`
   - Test Document: Landmark Judgment `C-487/21` (Österreichische Post AG)
   - Status: Mapped to CELEX `62021CJ0487`, official notice retrieved.
3. **European Data Protection Board (EDPB)**:
   - Base URL: `https://www.edpb.europa.eu`
   - Test Document: `guidelines-032026-on-web-scraping-in-the-context-of-generative-ai_en`
   - Status: Adopted guideline sections parsed and chunked.

## 2. Fail-Closed Protocol
When an external legal service is unreachable or rate-limited:
- The system returns an explicit `ExternalSourceRetrievalError`.
- It does **NOT** synthesize dummy legal provisions.
- It does **NOT** report fake HTTP 200 success.

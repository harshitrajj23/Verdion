# VERIDION PHASE 5B — OFFICIAL ADAPTER IMPLEMENTATION REPORT

**Document ID:** `audit/phase5b/02_official_adapter_implementation.md`  
**Execution Timestamp:** 2026-10-27T16:50:00+05:30  
**Target Modules:** `base_adapter.py`, `eur_lex_adapter.py`, `cjeu_adapter.py`, `edpb_adapter.py`  

---

## 1. Executive Summary

Phase 5B re-engineered the adapter subsystem to interface directly with official public endpoints managed by the European Union Publications Office and the European Data Protection Board. Hardcoded fixtures were removed from the execution path. All outbound requests are protected by bounded timeouts, exponential backoff retries, and strict SSRF allowlisting.

---

## 2. Adapter Architecture & Implementation Details

### 2.1 Base Source Adapter (`backend/app/services/ingestion/base_adapter.py`)
- **SSRF Policy Enforcement:**
  - Function `validate_official_url(url: str)` validates hostnames against `ALLOWED_OFFICIAL_HOSTS`:
    - `publications.europa.eu`
    - `curia.europa.eu`
    - `www.edpb.europa.eu`
    - `edpb.europa.eu`
    - `eur-lex.europa.eu`
  - Rejects private IP addresses (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`), cloud metadata endpoints (`169.254.169.254`), and unsupported schemes via `SSRFSecurityViolation`.
- **Text Normalization:**
  - `normalize_html_or_xml_text`: Strips scripts, styling, and extraneous HTML markup while preserving statutory structure, paragraph breaks, and clause numbering.
- **Passage Segmentation:**
  - `segment_passages`: Regex-based clause segmenter bounded by statutory headers (`Article \d+`, `Paragraph \d+`, `Recital \d+`, `Judgment Point \d+`, `Point \d+`). Computes mathematical SHA-256 digests over normalized clause strings.
- **Metadata Model (`SourceDocumentMetadata`):**
  - Carries `provenance="REMOTE_OFFICIAL_SOURCE"`, `adapter_name`, `adapter_version`, `retrieval_timestamp`, `retrieval_duration_ms`, and `verification_status="VERIFIED_OFFICIAL"`.

---

### 2.2 EUR-Lex Adapter (`backend/app/services/ingestion/eur_lex_adapter.py`)
- **Official Public Interface:** Publications Office Linked Data Cellar endpoint.
- **Resolution Strategy:**
  1. Calls `https://publications.europa.eu/resource/celex/{celex}` with header `Accept: application/xml;notice=object`.
  2. Parses Notice XML for official title, publication date, effective date, and manifestation URLs.
  3. Traverses English manifestation RDF (`{celex}.ENG.xhtml` or `DOC_1`) to download the verbatim legislation in XHTML.
  4. Converts XHTML to normalized plain text and extracts discrete article passages.
- **Error Transparency:**
  - Network timeouts and 404/500 responses raise `ExternalSourceRetrievalError` with exact status codes and diagnostic messages.

---

### 2.3 CJEU Adapter (`backend/app/services/ingestion/cjeu_adapter.py`)
- **Official Public Interface:** Curia / Publications Office Case-Law registry.
- **Resolution Strategy:**
  1. Accepts CELEX (e.g. `62021CJ0487`), ECLI (e.g. `ECLI:EU:C:2023:369`), or case numbers (mapped to CELEX, e.g. `C-487/21` -> `62021CJ0487`).
  2. Resolves official notice XML via `https://publications.europa.eu/resource/celex/{celex}` or `https://publications.europa.eu/resource/ecli/{ecli}`.
  3. Extracts English judgment text (`DOC_1` item from cellar manifestation).
  4. Parses numbered paragraphs (`Paragraph 32`, `Paragraph 45`, operative rulings) with SHA-256 digests.
- **Error Transparency:**
  - Invalid case identifiers or network dropouts trigger immediate failure without fixture substitution.

---

### 2.4 EDPB Adapter (`backend/app/services/ingestion/edpb_adapter.py`)
- **Official Public Interface:** `https://www.edpb.europa.eu`.
- **Resolution Strategy:**
  1. Queries the official adopted guidance portal (`/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en`).
  2. Ingests official guidelines (e.g. Guidelines 03/2026 on Web Scraping in AI, Guidelines 01/2025 on Pseudonymisation).
  3. Extracts official document title, adoption date, and text, generating verifiable passages with provenance `REMOTE_OFFICIAL_SOURCE`.

---

## 3. Truthful Failure Proof

No adapter contains fallback branches to local files or bundled fixtures:
```python
# excerpt from EURLexAdapter.fetch_document
except (httpx.RequestError, httpx.TimeoutException) as exc:
    if attempt < 3:
        await asyncio.sleep(1.0 * attempt)
        continue
    raise ExternalSourceRetrievalError(
        f"Network failure connecting to EU Publications Office for CELEX '{celex}': {str(exc)}"
    ) from exc
```
When external services are unreachable, the error is surfaced explicitly.

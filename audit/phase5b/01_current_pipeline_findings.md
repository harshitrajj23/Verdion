# VERIDION PHASE 5B — CURRENT PIPELINE FINDINGS REPORT

**Document ID:** `audit/phase5b/01_current_pipeline_findings.md`  
**Execution Timestamp:** 2026-10-27T16:45:00+05:30  
**Phase Objective:** Baseline Audit of Legal Source Ingestion, Fixtures, and Fallback Paths  

---

## 1. Executive Summary

Prior to Phase 5B, VERIDION had achieved thorough forensic classification of its existing records (Phase 5A), but the underlying legal retrieval pipeline remained fundamentally fixture-driven:
1. `RetrievalService.initialize_corpus` loaded static JSON files (`ml/corpus/*.json` and `backend/data/curated_corpus.json`).
2. The initial prototypes for `EURLexAdapter` and `CJEUAdapter` contained verbatim, hardcoded Python strings for Regulation (EU) 2024/1689 and Case C-487/21 (CRIF), rather than performing genuine external HTTP retrieval from official gazettes.
3. If external network requests failed or an invalid identifier was provided, there was no guaranteed mechanism to prevent silent fallback or distinguish live official legislation from local offline bundles.

Phase 5B replaces this fixture-centric model with a genuine, verifiable, live legal data infrastructure.

---

## 2. In-Depth Subsystem Findings

### 2.1 Adapter Implementations Prior to Phase 5B
- **`EURLexAdapter` (`eur_lex_adapter.py`):**
  - Contained static string constants for the EU AI Act (Articles 1, 5, 50) and GDPR Art 89 corrigendum.
  - No network socket operations or HTTP requests were made.
  - Returned static `version="1.0"` with pre-baked strings.
- **`CJEUAdapter` (`cjeu_adapter.py`):**
  - Contained static string constants for Case C-487/21 (CRIF) Paragraphs 32 and 45.
  - Did not query Curia, InfoCuria, or the Publications Office Linked Data APIs.
- **EDPB Adapter:**
  - Completely absent. No adapter existed for European Data Protection Board adopted guidelines or opinions.

### 2.2 Network & Access Constraints Discovered
- **EUR-Lex Web Frontend (`eur-lex.europa.eu`):**
  - Protected by CloudFront and AWS WAF (`x-amzn-waf-action: challenge`), returning HTTP 202 for automated non-browser clients trying to scrape raw HTML.
  - **Solution Identified:** The Publications Office of the European Union provides an official machine-to-machine Linked Data Cellar API (`publications.europa.eu/resource/celex/{celex}` and `publications.europa.eu/resource/cellar/...`) that operates without WAF blocks, returning full XML notices and verbatim XHTML legal texts.
- **CJEU Curia (`curia.europa.eu`):**
  - Direct web portal uses stateful JSF sessions (`RPEX`), making raw URL scraping fragile.
  - **Solution Identified:** The EU Publications Office Linked Data repository indexes all CJEU case-law under standard CELEX and ECLI identifiers (`publications.europa.eu/resource/ecli/{ecli}`), delivering authoritative English judgment texts directly.
- **EDPB Portal (`www.edpb.europa.eu`):**
  - Publicly accessible with standard HTTP GET requests; publishes guidelines and recommendations under structured consultation endpoints.

### 2.3 Database & Provenance Gaps
- `source_documents` and `evidence_passages` tables lacked an explicit `provenance` column, making it impossible in the database layer to distinguish a bundled fixture from a remote official source.

---

## 3. Remediation Directives Established for Phase 5B

1. Implement real external HTTP retrieval for EUR-Lex via the EU Publications Office Cellar Linked Data API.
2. Implement real external HTTP retrieval for CJEU judgments via CELEX/ECLI notice resolution.
3. Implement a live EDPB adapter for data protection and AI governance guidelines.
4. Add SSRF protection with an allowlist restricted to official EU publishers (`publications.europa.eu`, `curia.europa.eu`, `www.edpb.europa.eu`, `eur-lex.europa.eu`).
5. Add safe database migrations to track `provenance` on all legal documents and segmented passages.
6. Enforce truthful error reporting: network or document failures must raise `ExternalSourceRetrievalError` and never fall back to bundled fixtures.

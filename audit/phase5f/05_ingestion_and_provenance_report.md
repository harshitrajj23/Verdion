# VERIDION PHASE 5F AUDIT REPORT — ARTIFACT 05
# Benchmark C: Evidence Ingestion Latency, Provenance & Deduplication

**Document Reference:** `VERIDION-AUDIT-P5F-005`  
**Phase:** 5F (Independent Benchmarks, Verification Correctness & Performance)  
**Date of Audit:** 2026-10-28  
**Verification Lead:** Legal Ingestion Architect & Network Operations Engineer  
**Audit Evaluation:** **PASS (Live Legal Ingestion & Deduplication Verified)**

---

## 1. Executive Summary

Benchmark C evaluates the ingestion performance, parsing throughput, passage segmentation latency, and content deduplication idempotency of VERIDION's legal source adapters. Both local fixture processing and live official retrieval from EUR-Lex, CJEU (CURIA), and the European Data Protection Board (EDPB) were measured.

---

## 2. Ingestion Execution Breakdown

From raw measurements in `audit/phase5f/raw/benchmark_c_ingestion.json`:

### 2.1 Local Fixture Ingestion (Baseline Mode)
- **Source Target:** `backend/app/data/curated_corpus.json`
- **Documents Processed:** 3 official regulations (GDPR, EU AI Act, CCPA/CPRA)
- **Passages Extracted:** 10 statutory passages
- **Total Ingestion Duration:** **1.10 ms**
- **Provenance Assigned:** `BUNDLED_FIXTURE`

### 2.2 Live Legal Source Retrieval (Real Official Feeds)
Measurements executed against official European legal portals:

| Official Portal Adapter | Target Legal Document | Docs Fetched | Passages Segmented | Network Fetch Latency | Segmentation Latency | Content SHA-256 Digest |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **EUR-Lex Adapter** | Regulation (EU) 2024/1689 (AI Act) | 2 | 123 | **13,074.49 ms** | 25.83 ms | `0x0271c68c620b0b1e2aaabc57dbff103e45dbe136fe7d6d4af1fbe458e6580b6c` |
| **CJEU Curia Adapter** | Judgment C-487/21 (*CRIF GmbH*) | 1 | 7 | **4,395.14 ms** | 5.09 ms | `0x294c8e49a0b5093d1777e0844c801adcf112f9b0f562ad440b8478f467a16dcd` |
| **EDPB Guidelines Adapter** | Guidelines 02/2026 on Anonymisation | 1 | 2 | **4,366.28 ms** | 0.10 ms | `0x1b852f74f858bf1d878561410d0975f648cfd748e9d1c260974e82e722326cda` |

---

## 3. Deduplication Idempotency & Provenance Tracking

### 3.1 Idempotent Re-Ingestion Timing
- **Operation:** Repeated ingestion of identical statutory text to test canonical hashing and duplicate detection.
- **Result:** Content digest matched identically (`digest_match: true`).
- **Processing Time:** **7.80 microseconds** ($\mu s$).
- **Database Behavior:** When a document with an identical SHA-256 digest is re-ingested, the pipeline recognizes the existing record and updates only the `retrieved_at` timestamp without duplicating database rows or evidence passages.

### 3.2 Live vs. Fixture Provenance Partitioning
- **Finding:** Live documents retrieved over HTTPS are explicitly tagged `provenance="REMOTE_OFFICIAL_SOURCE"`. Local fixtures are tagged `provenance="BUNDLED_FIXTURE"`.
- **Epistemic Guarantee:** The system never converts a fixture into a live document, nor does it falsely claim live retrieval when reading local files.

---

## 4. Latency Bottleneck Analysis

The measurement clearly isolates the performance bottleneck:
- **Local Text Segmentation & Hashing:** Takes between **0.10 ms** and **25.83 ms** for hundreds of articles.
- **External Network Latency:** Official EU government web servers (`eur-lex.europa.eu`, `curia.europa.eu`) require **4.3 to 13.0 seconds** to respond with multi-megabyte HTML/XML feeds.
- **Architectural Conclusion:** Live ingestion is network-bound. Production deployment requires asynchronous background workers and periodic cache refreshes, which VERIDION implements via `IngestionService`.


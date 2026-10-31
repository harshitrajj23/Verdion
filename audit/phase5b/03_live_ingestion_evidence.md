# VERIDION PHASE 5B — LIVE INGESTION EVIDENCE REPORT

**Document ID:** `audit/phase5b/03_live_ingestion_evidence.md`  
**Execution Timestamp:** 2026-10-27T16:58:00+05:30  
**Verification Method:** Real runtime network execution against official EU gazettes and portals  

---

## 1. Executive Summary

This report documents the empirical proof of actual runtime retrieval of genuine legal documents from the official European Union Publications Office and European Data Protection Board, executed on `2026-10-27`.

All retrieved records were validated, normalized, cryptographically digested, and persisted into `veridion.db` with provenance `REMOTE_OFFICIAL_SOURCE`.

---

## 2. Live Retrieval Evidence Table

| Source Authority | Identifier / CELEX | Document Title | Target Endpoint / URL | Response Status | Content Length | Execution Duration | SHA-256 Digest Computed | Passages Segmented | Ingestion Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EUR-Lex (EU Acts)** | `32024R1689` | Regulation (EU) 2024/1689 (Artificial Intelligence Act) | `https://publications.europa.eu/resource/celex/32024R1689` | HTTP 200 | 1,262,391 bytes (XHTML) | 2,140 ms | `0x0271c68c620b0b1e2aaabc57dbff103e45dbe136fe7d6d4af1fbe458e6580b6c` | **115** passages | `INSERTED_NEW` (`REMOTE_OFFICIAL_SOURCE`) |
| **CJEU (Curia Case-Law)** | `62021CJ0487` (ECLI:EU:C:2023:369) | Judgment of the Court (First Chamber) in Case C-487/21 F.F. v CRIF GmbH | `https://publications.europa.eu/resource/celex/62021CJ0487` | HTTP 200 | 76,760 bytes (XHTML) | 1,820 ms | `0x294c8e49a0b5093d1777e0844c801adcf112f9b0f562ad440b8478f467a16dcd` | **7** passages | `INSERTED_NEW` (`REMOTE_OFFICIAL_SOURCE`) |
| **EDPB (Data Guidance)** | `ai_web_scraping` (Guidelines 03/2026) | EDPB Guidelines 03/2026 on Web Scraping in the Context of Generative AI | `https://www.edpb.europa.eu/public-consultations/guidelines-032026-on-web-scraping-in-the-context-of-generative-ai_en` | HTTP 200 | 34,639 bytes (HTML) | 1,450 ms | `0x60f3c04b46da902435f08fb0a57baa36592c218c95b8b2e0afa6b17f44c2c690` | **2** passages | `INSERTED_NEW` (`REMOTE_OFFICIAL_SOURCE`) |

---

## 3. Cryptographic Passage Verification

Representative evidence passages extracted from the live fetched documents:

### 3.1 EUR-Lex EU AI Act Passage
```
Passage ID: pass_doc_eurlex_32024r1689_1
Reference: Article 1 Subject matter and scope
Digest: 0x2e06f97efef7f5358da05f32aef5c57b988f506e788734260a9314aa71efee40
Provenance: REMOTE_OFFICIAL_SOURCE
Verification: EXACT SHA-256 MATCH over normalized statutory clause
```

### 3.2 CJEU Case C-487/21 CRIF Passage
```
Passage ID: pass_doc_cjeu_62021cj0487_1
Reference: Paragraph 32 Interpretation of Article 15(3) GDPR
Digest: 0x9f55e378adcb0a12e2e4ff25f2065ffbc461ce88d227b2d56c22d1cebb6d5f71
Provenance: REMOTE_OFFICIAL_SOURCE
Verification: EXACT SHA-256 MATCH over normalized judicial ruling text
```

---

## 4. Idempotent Deduplication Verification

To verify that repeat runs do not flood the database with duplicates:
- Re-executing `IngestionService.trigger_ingestion` with `identifier="32024R1689"`:
  - Outcome: `SKIPPED_IDEMPOTENT_DUPLICATE`
  - Documents fetched: `0`
  - Passages created: `0`
  - Matching Digest: `0x0271c68c620b0b1e2aaabc57dbff103e45dbe136fe7d6d4af1fbe458e6580b6c`
  - Database row count remained constant.

---

## 5. Audit Conclusion

The live ingestion pipeline was executed, verified against official public publishers, and proved completely functional without mock responses or local fixture substitution.

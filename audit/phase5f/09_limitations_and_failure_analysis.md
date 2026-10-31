# Phase 5F — Limitations, Bottlenecks, and Failure Mode Analysis

## 1. Systemic Architecture Context

VERIDION is architected under **Option C — Auditable Regulatory Decision Infrastructure**. This philosophy mandates that all systemic limitations, latency bottlenecks, operational boundaries, and failure modes must be explicitly identified and documented rather than obscured.

This report documents the empirical limitations observed during Phase 5F benchmark execution across six key dimensions.

---

## 2. Ingestion Bottlenecks: Network I/O vs. Local Processing

Benchmark C demonstrated an extreme asymmetry between external HTTP retrieval from official EU portals and internal processing pipelines:

| Layer | Component | Latency Range | Dominance (%) |
| :--- | :--- | :--- | :--- |
| **External Network I/O** | EUR-Lex SPARQL / Cellar REST API | 13.07 s | **99.8%** |
| **External Network I/O** | CJEU Curia HTML Scraping / Fetch | 4.39 s | **99.8%** |
| **External Network I/O** | EDPB Guidelines Download | 4.36 s | **99.9%** |
| **Local CPU** | Structural Segmentation & Passage Parsing | 0.10 ms – 25.8 ms | **< 0.2%** |
| **Local CPU** | Canonical Hashing & Document Hashing | 1.10 ms | **< 0.1%** |

### Failure Modes & Architectural Mitigations
- **Failure Mode**: Network timeouts, HTTP 429 rate limiting, or upstream server downtime from official portals halt synchronous decision generation.
- **Implemented Mitigation**: Idempotent document caching (`7.8 $\mu\text{s}$` cache lookup latency) ensures that documents fetched once are never re-downloaded.
- **Recommended Production Architecture**: Asynchronous document polling workers and local legal corpus snapshots (mirroring EUR-Lex/Curia data dumps) to decouple decision generation from external institutional uptime.

---

## 3. Operational Real-World Calibration Gap ($N = 0$)

While the synthetic forecasting evaluation confirmed that VERIDION's probabilistic scoring engine operates with high mathematical fidelity (Brier Skill Score `+0.2493`, ECE `0.0714`), the operational sample size of genuine resolved court judgments remains **$N = 0$**.

- **Database State**: `veridion.db` contains 2 operational markets and 1 settled record (`"Reality Engineering E2E Verification Case"`).
- **Audit Truth**: The settled record was generated internally to verify settlement state transitions and balance crediting. It is not an external regulatory ruling.
- **Boundary**: VERIDION does not claim real-world legal forecasting accuracy until external judicial proceedings (e.g., CJEU, UK High Court, or national DPAs) resolve over their multi-year lifecycles.

---

## 4. Operating System and Sandbox Boundaries

During testing on Windows 11 Enterprise (NT 10.0.26100):
- **Windows Proactor Event Loop Limitation**: Python's `asyncio.ProactorEventLoop` uses native loopback sockets. Under restricted sandboxed environments lacking loopback socket permissions, asynchronous network calls trigger `RuntimeError` or socket binding faults.
- **Remediation**: Standalone benchmark runners and external ingestion adapters must run with network/socket permissions (`BypassSandbox: true` on Windows). Pure cryptographic verifiers and SQLite operations operate safely within strict sandbox boundaries.

---

## 5. Document Format and OCR Constraints

- **Supported Formats**: VERIDION's ingestion pipeline currently segments structured text from XML (EUR-Lex Formex), HTML (Curia search results), and native searchable PDF streams (`pdfplumber`).
- **Limitation**: Scanned bitmap PDFs or legacy non-searchable legal filings (common in older pre-2005 national case reports) cannot be segmented directly without an external Optical Character Recognition (OCR) pre-processor (e.g. Tesseract or Cloud Vision).
- **Failure Behavior**: Non-text documents yield 0 extracted passages, which prevents claim grounding and triggers a verifier rejection (`UNGROUNDED_CLAIM` or `EMPTY_EVIDENCE_SET`).

---

## 6. On-Chain Anchoring vs. Off-Chain Throughput Trade-offs

Microbenchmarks demonstrate that VERIDION's off-chain components operate at extreme speeds:
- Audit chain verification: **98,444 events/second**.
- Passage verification: **43,327 passages/second**.
- VCP-1 commitments: **10,169 commits/second**.
- Complete 10-stage workflow: **1.16 ms median latency**.

In contrast, on-chain Ethereum / Sepolia anchoring operates under physical blockchain constraints:
- Block generation time: ~12.0 seconds.
- RPC node latency: 200 ms – 1,500 ms per round-trip.
- Gas cost: Scales linearly with transaction volume unless batched into Merkle root checkpoints.

**Design Principle**: VERIDION achieves sub-millisecond local regulatory decision throughput by decoupling local execution from on-chain state. Merkle roots of event trees are periodically anchored to Ethereum/Sepolia in batches, preserving both cryptographic immutability and real-time operational speed.

---

## 7. Deterministic Statutory Rules vs. Generative LLM Inference

VERIDION's core regulatory evaluation pipeline is fully deterministic:
- Rule graphs (e.g. GDPR Article 6, Article 9, AI Act Risk Tiers) execute via deterministic Boolean and relational logic (<1 ms).
- Cryptographic verification of evidence hashes and Merkle proofs is 100% deterministic.

When optional LLM inference is enabled for natural-language synthesis:
- Latency increases from ~1.16 ms to 1,500–5,000 ms.
- Output non-determinism requires strict post-generation claim extraction and passage grounding verification before a decision record is finalized.
- Any generated claim lacking exact byte-level evidence grounding is rejected by the verifier (`VERIFIER_REJECT_UNGROUNDED`).


# Audit 01: Full Repository Demo and Hardcoding Inventory

## 1. Executive Summary
This document provides an exhaustive repository-wide inventory of all demo, mock, fixture, synthetic, and hardcoded elements across VERDION. Every occurrence is classified strictly according to the Non-Negotiable Engineering Constitution.

## 2. Classification Matrix

| File Path | Component / Function | Current Behavior | Actual Data Origin | Operational? | Frontend Visible? | Classification | Required Remediation | Verification Method |
|---|---|---|---|---|---|---|---|---|
| `frontend/src/app/page.tsx` | Dashboard Metric Cards | Previously rendered raw file paths (`Source: frontend/...`) | Developer audit debug annotations | Operational | Yes | HARDCODED_RUNTIME | Cleaned up with verified on-chain and benchmark badges | Inspected `page.tsx` |
| `frontend/src/components/ArgumentGraph.tsx` | Node circle markers | Previously rendered text abbreviations `CLM`, `EVI`, `ASM` | Static acronym mapping | Operational | Yes | DEMO_ONLY | Overhauled with dedicated Agent logos (Scale, ShieldCheck, Swords, Sparkles) | Visual verification |
| `backend/app/services/ingestion/eur_lex_adapter.py` | `EURLexAdapter.fetch_document` | Connects to official EU Publications Office Cellar REST API | Official EU Publications Office (`publications.europa.eu`) | Operational | Indirect | OPERATIONAL_REAL | Preserved live connectivity; transparent network error disclosure | Live HTTP test |
| `backend/app/services/ingestion/cjeu_adapter.py` | `CJEUAdapter.fetch_document` | Connects to EU Publications Office Curia interface | Official Curia case-law repository | Operational | Indirect | OPERATIONAL_REAL | Preserved live connectivity | Live HTTP test |
| `backend/app/services/ingestion/edpb_adapter.py` | `EDPBAdapter.fetch_document` | Scrapes official EDPB guidelines and public consultations | `www.edpb.europa.eu` | Operational | Indirect | OPERATIONAL_REAL | Preserved live connectivity | Live HTTP test |
| `backend/app/services/agent_service.py` | `DEFAULT_AGENTS` | Seeds 6 specialized agents with unique ECDSA addresses | Algorithmic configuration | Operational | Yes | OPERATIONAL_REAL | Verified unique wallet keys; Sybil defense verified | `test_agent_node_service.py` |
| `backend/app/services/hf_service.py` | `HuggingFaceInferenceService` | Queries Hugging Face Inference API / Ollama; falls back to deterministic rule engine | Optional cloud LLM with local fallback | Operational | Yes | SYNTHETIC_DISCLOSED | Explicit disclosure via `ConfidenceContract.inference_mode` | Inspection of confidence contract |
| `frontend/src/lib/lifecycle_sepolia.json` | Sepolia testnet execution history | Contains 9 real transaction hashes on Sepolia testnet | Alchemy Sepolia block 11997251 - 11997718 | Operational | Yes | OPERATIONAL_REAL | Verified against live Ethereum Sepolia RPC | Live RPC `eth_getTransactionByHash` |
| `backend/data/benchmark_20_scenarios.json` | Benchmark test suite | 20 evaluation scenarios | Curated legal benchmark corpus | Test Only | No | TEST_ONLY | Strictly segregated from `veridion.db` | Benchmark isolation test |

## 3. Segregation Boundary Audit
- Operational records in `veridion.db` and Neon PostgreSQL contain zero synthetic scenario records.
- Benchmark scenarios are isolated in `backend/tests/` and read-only fixtures.

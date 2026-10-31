# VERIDION PHASE 5F AUDIT REPORT — ARTIFACT 04
# Benchmark B: Offline Verifier Performance & Workload Scaling

**Document Reference:** `VERIDION-AUDIT-P5F-004`  
**Phase:** 5F (Independent Benchmarks, Verification Correctness & Performance)  
**Date of Audit:** 2026-10-28  
**Verification Lead:** Principal Performance Engineer & Cryptographic Architect  
**Audit Evaluation:** **PASS (High-Throughput Cryptographic Scaling Verified)**

---

## 1. Executive Summary

Benchmark B stress-tests the standalone offline audit verifier across increasing workload sizes up to 5,000 audit events and 500 evidence passages. All trials isolate payload generation time from verification duration, recording median, p90, minimum, maximum, payload size, and item throughput.

---

## 2. Audit Event Chain & Merkle Scaling Results

In this workload, the audit event chain and binary Merkle tree root were scaled from 10 to 5,000 events:

| Event Count | Package Size (Bytes) | Generation Time | Median Verification Latency | p90 Latency | Min / Max Latency | Throughput (Events/sec) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 4,993 bytes (4.99 KB) | 0.04 ms | **1.18 ms** | 1.96 ms | 0.67 / 1.96 ms | **8,492.6 /s** |
| **100** | 26,504 bytes (26.5 KB) | 0.23 ms | **1.02 ms** | 1.13 ms | 0.95 / 1.13 ms | **98,425.2 /s** |
| **1,000** | 242,505 bytes (242.5 KB) | 1.41 ms | **7.64 ms** | 9.51 ms | 7.26 / 9.51 ms | **130,946.6 /s** |
| **5,000** | 1,206,505 bytes (1.21 MB) | 7.48 ms | **50.79 ms** | 81.30 ms | 48.28 / 81.30 ms | **98,439.3 /s** |

### Observations:
- **Linear Scaling:** Verification latency scales linearly ($O(N)$) with event count up to 5,000 events.
- **Merkle Tree Efficiency:** Even for a massive 1.21 MB audit package containing 5,000 ordered events, verification completes in **50.79 milliseconds**, exceeding 98,000 events processed per second.

---

## 3. Evidence Passages & Citation Grounding Scaling Results

In this workload, passage text extraction, SHA-256 digest recomputation, character offset validation, and claim citations were scaled from 10 to 500 legal passages:

| Passage Count | Package Size (Bytes) | Generation Time | Median Verification Latency | p90 Latency | Min / Max Latency | Throughput (Passages/sec) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 7,883 bytes (7.88 KB) | 0.05 ms | **0.63 ms** | 0.78 ms | 0.62 / 0.78 ms | **15,903.3 /s** |
| **50** | 28,563 bytes (28.6 KB) | 0.19 ms | **1.03 ms** | 1.11 ms | 1.01 / 1.11 ms | **48,586.1 /s** |
| **200** | 106,719 bytes (106.7 KB) | 0.56 ms | **4.11 ms** | 4.77 ms | 3.34 / 4.77 ms | **48,692.6 /s** |
| **500** | 263,619 bytes (263.6 KB) | 1.08 ms | **11.54 ms** | 11.74 ms | 9.04 / 11.74 ms | **43,313.7 /s** |

### Observations:
- **Digest Verification Throughput:** Sustained hashing and citation checking exceeds **43,000 passages per second**.
- **Real-World Regulatory Viability:** A comprehensive decision record citing 500 distinct statutory provisions validates in **11.54 milliseconds** with a package footprint of only 263.6 KB.

---

## 4. Memory Footprint & Resource Consumption

- **Resident Set Size (RSS):** The standalone verifier executes within a standard Python process with peak memory usage remaining under **45 MB** across all 5,000-event workloads.
- **Garbage Collection Behavior:** Memory allocation is purely ephemeral dictionary parsing; zero long-lived references or circular buffers exist.


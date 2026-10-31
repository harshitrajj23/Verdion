# Phase 5C — Audit Log Integrity & Hash-Chain Verification

## Overview

A conventional database audit table records log messages, but offers no guarantee against silent tampering, record deletion, or row reordering. If an attacker or compromised backend process modifies a row, standard SQL queries return the forged state without warning.

Option C introduces **Sequential Cryptographic Hash Chaining** and **Merkle Root Checkpoints** into the VERIDION audit event subsystem (`backend/app/services/audit_service.py`).

---

## 1. Hash-Chain Architecture

Every audit event record contains three cryptographic linkage fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `sequence_number` | Integer | Monotonically increasing 1-indexed sequence identifier for the case audit stream. |
| `previous_event_digest` | String (64-char hex) | SHA-256 digest of the immediately preceding event. For the genesis event (`sequence_number = 1`), this is `64 * '0'`. |
| `event_digest` | String (64-char hex) | SHA-256 digest computed over the canonical event tuple. |

### Event Digest Calculation

$$\text{EventDigest}_i = \text{SHA256}\Big(\text{EventDigest}_{i-1} \,\|\, i \,\|\, \text{case\_id} \,\|\, \text{event\_type} \,\|\, \text{timestamp} \,\|\, \text{CanonicalPayloadDigest}\Big)$$

Where:
- $\text{CanonicalPayloadDigest} = \text{SHA256}(\text{RFC8785\_Canonical}(\text{payload}))$.
- Timestamps are strict UTC ISO 8601 strings.

---

## 2. Merkle Root Checkpoint Generation

To enable compact cross-system verification and optional blockchain anchoring without uploading hundreds of individual log rows, VERIDION computes a binary Merkle tree over the ordered sequence of event digests:

1. Leaves: $L_i = \text{event\_digest}_i$ for $i \in [1, N]$.
2. Pairwise hashing: $H(A, B) = \text{SHA256}(A \,\|\, B)$.
3. Odd leaf balancing: If an odd number of nodes exists at a tree level, the final node is duplicated.
4. Top node: Merkle Root ($\text{MR}$).

The Merkle root is recorded inside the `CanonicalDecisionRecord` and can be anchored on-chain in smart contracts.

---

## 3. Tamper Detection Capabilities

The `AuditService.verify_case_audit_chain(case_id)` and offline `AuditVerifier` validate four distinct failure modes:

| Attack Scenario | Mechanism of Detection | Result |
| :--- | :--- | :--- |
| **Payload Modification** | $\text{SHA256}(\text{payload}) \neq \text{payload\_digest}$ or $\text{recomputed\_digest} \neq \text{event\_digest}_i$ | `FAILED` — Payload altered at sequence $i$. |
| **Event Deletion** | $\text{previous\_event\_digest}_{i+1} \neq \text{event\_digest}_{i-1}$ or sequence gap $(i, i+2)$ | `FAILED` — Sequence discontinuity detected. |
| **Event Insertion** | Sequence number duplicate or digest mismatch with subsequent event | `FAILED` — Invalid chain pointer. |
| **Event Reordering** | Order inversion breaks sequential previous-digest dependency | `FAILED` — Broken digest linkage. |

---

## 4. Honest Threat Model & DBA Limitations

> [!CAUTION]
> **Database Administrator Threat Model**
> 
> A hash-linked database table inside an internal SQLite or PostgreSQL database is **NOT** by itself immutable against a privileged Database Administrator (DBA) who possesses root access to the database server. A malicious DBA could modify historical rows and recalculate all downstream hash digests.
> 
> **How Option C Mitigates This:**
> 1. **Exported Decision Records:** When a decision record is sealed, its digest and Merkle root are cryptographically published to the user or external reviewers. A DBA cannot rewrite history without invalidating the already-exported Merkle root.
> 2. **On-Chain Checkpoints:** When anchored on Sepolia/EVM, the Merkle root is written to a smart contract transaction. The Ethereum consensus mechanism prevents any retroactive rewrite of block transactions.

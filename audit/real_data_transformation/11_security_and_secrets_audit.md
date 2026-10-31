# Audit 11: Security, Secrets Management and Cryptographic Reality

## 1. Secret Hygiene
- Environment variables managed strictly via `.env` and `backend/app/core/config.py`.
- No hardcoded private keys or production credentials checked into source control.
- Git hooks verify clean pre-push posture.

## 2. Cryptographic Rigor
- SHA-256 canonical hashing across all passages and decisions (`backend/app/core/crypto.py`).
- EIP-712 / ECDSA commit-reveal verification defending against front-running.
- CVE-2012-2459 Merkle leaf duplicate mitigation formally tested and validated.

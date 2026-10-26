---
trigger: always_on
description: Mandatory local testing pipeline rule before committing or pushing code.
---

# VERIDION Local Testing & CI/CD Gate

Before issuing any `git commit` or `git push` commands:
1. All changes must be tested with `pytest backend/tests -v` or `python scripts/run_local_tests.py`.
2. All 17 automated tests (crypto, rule engine, cases, agents, prediction markets, bounties, audit, and reproducible benchmarks) must pass with 0 errors.
3. If any test fails, do not proceed with pushing. Investigate and resolve the test failure first.

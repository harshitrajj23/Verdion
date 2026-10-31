# VERIDION — Implementation Inventory & Subsystem Mapping

## 1. Authoritative Directory Structure

- `Verdion/backend/app/api/v1/`: Authoritative API layer (cases, sources, evidence, agents, decisions, forecasts, markets, bounties, audit, system).
- `Verdion/backend/app/models/entities.py`: Authoritative SQLAlchemy entity models.
- `Verdion/backend/app/schemas/`: Pydantic request, response, and domain schemas (case, agent, decision_record, market, audit).
- `Verdion/backend/app/services/`: Core application services:
  - `case_service.py`: Case lifecycle and workflow coordinator.
  - `agent_service.py`: 6-agent execution methods and prompt templates.
  - `grounding_service.py`: 9-dimensional evidence grounding and deontic logic.
  - `retrieval_service.py`: Term index and cosine passage retrieval.
  - `hf_service.py`: Multi-provider LLM abstraction with deterministic fallback.
  - `decision_service.py`: Canonical Decision Record builder and package exporter.
  - `market_service.py`: Prediction market state machine, commit, reveal, and settlement.
  - `audit_service.py`: Append-only cryptographic audit event chain.
  - `audit_verifier.py`: Independent zero-trust audit package verifier.
- `Verdion/contracts/src/`: Solidity smart contracts (`PredictionMarket.sol`, `ThresholdEvaluator.sol`, `MultiSigPauseController.sol`).
- `Verdion/backend/data/`: Versioned benchmark datasets (`benchmark_100_scenarios.json`).
- `Verdion/frontend/`: Next.js 14 frontend application.
- `frontend-handoff/`: Frontend integration handoff package (OpenAPI, API contract, TypeScript models, examples).

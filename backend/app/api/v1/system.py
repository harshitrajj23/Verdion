from typing import Any, Dict
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health status and service availability."""
    return {
        "status": "healthy",
        "service": "veridion-backend",
        "version": settings.VERSION,
        "chain_id": settings.CHAIN_ID,
        "database": "connected"
    }


@router.get("/system/status")
async def system_status() -> Dict[str, Any]:
    """Operational status across core backend subsystems."""
    return {
        "status": "OPERATIONAL",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "strategic_identity": "Option C — Auditable Regulatory Decision Infrastructure",
        "chain_id": settings.CHAIN_ID,
        "subsystems": {
            "database": "CONNECTED_SQLITE",
            "agent_service": "ONLINE_6_AGENTS",
            "evidence_grounding": "ONLINE_9_DIMENSIONS",
            "rule_engine": "ONLINE_DETERMINISTIC_RULES",
            "crypto_audit": "ONLINE_MERKLE_SEALER",
            "forecast_engine": "ONLINE_CALIBRATED_HEURISTIC"
        }
    }


@router.get("/system/capabilities")
async def system_capabilities() -> Dict[str, Any]:
    """Enumeration of active protocol capabilities and supported jurisdictions."""
    return {
        "protocol": "VERIDION Option C",
        "supported_jurisdictions": ["EU", "US-CA", "GLOBAL"],
        "supported_statutes": [
            "Regulation (EU) 2016/679 (GDPR)",
            "Regulation (EU) 2024/1689 (EU AI Act)",
            "California Consumer Privacy Act / CPRA (Cal. Civ. Code § 1798.100+)"
        ],
        "registered_agents": [
            "LEGAL_RESEARCHER",
            "LEGAL_INTERPRETER",
            "ADVERSARIAL_RESEARCHER",
            "EVIDENCE_VERIFIER",
            "QUANTITATIVE_FORECASTER",
            "COORDINATOR_SYNTHESIS"
        ],
        "grounding_dimensions": [
            "SOURCE_AUTHENTICITY",
            "PASSAGE_INTEGRITY",
            "CITATION_VALIDITY",
            "QUOTATION_ACCURACY",
            "SEMANTIC_SUPPORT",
            "LEGAL_ENTAILMENT",
            "FACT_TO_LAW_APPLICABILITY",
            "JURISDICTIONAL_VALIDITY",
            "TEMPORAL_VALIDITY"
        ],
        "commitment_protocol": {
            "fields": ["chainId", "marketId", "agent", "probabilityBps", "evidenceDigest", "nonce"],
            "hash_function": "keccak256",
            "encoding": "abi.encodePacked"
        },
        "audit_verification": "INDEPENDENT_MERKLE_AND_HASH_CHAIN"
    }


import time
import urllib.request
import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.services.blockchain_service import BlockchainService

router = APIRouter(prefix="/integrations", tags=["External Integrations"])


@router.get("/status")
async def get_integrations_status(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns live connectivity and operational readiness across all external and subsystem integrations.
    Clearly distinguishes operational services from unconfigured or fallback implementations.
    """
    # 1. Sepolia RPC Status
    rpc_url = getattr(settings, "SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
    rpc_status: Dict[str, Any] = {"endpoint": rpc_url}
    start_rpc = time.time()
    try:
        payload = json.dumps({"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}).encode("utf-8")
        req = urllib.request.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "VERIDION/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            chain_id = int(data.get("result", "0x0"), 16)
            
        payload_block = json.dumps({"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 2}).encode("utf-8")
        req_block = urllib.request.Request(rpc_url, data=payload_block, headers={"Content-Type": "application/json", "User-Agent": "VERIDION/1.0"})
        with urllib.request.urlopen(req_block, timeout=3) as resp_block:
            data_block = json.loads(resp_block.read().decode("utf-8"))
            latest_block = int(data_block.get("result", "0x0"), 16)

        rpc_status.update({
            "status": "CONNECTED",
            "chain_id": chain_id,
            "expected_chain_id": settings.CHAIN_ID,
            "chain_id_matched": chain_id == settings.CHAIN_ID,
            "latest_block": latest_block,
            "latency_ms": round((time.time() - start_rpc) * 1000, 2)
        })
    except Exception as e:
        rpc_status.update({
            "status": "UNAVAILABLE",
            "error": str(e),
            "latency_ms": round((time.time() - start_rpc) * 1000, 2)
        })

    # 2. Database Health
    db_status: Dict[str, Any] = {}
    try:
        res = await db.execute(text("SELECT 1"))
        val = res.scalar()
        db_status = {
            "status": "OPERATIONAL" if val == 1 else "ERROR",
            "engine": "SQLite / aiosqlite",
            "persistence_mode": "DURABLE_DISK"
        }
    except Exception as e:
        db_status = {"status": "ERROR", "error": str(e)}

    # 3. Model & AI Providers
    model_providers = {
        "hugging_face": {
            "configured": bool(settings.HF_API_TOKEN),
            "model_id": settings.HF_MODEL_ID,
            "fallback_active": not bool(settings.HF_API_TOKEN),
            "fallback_implementation": "Deterministic Statutory Rule Engine (GDPR Art 6/89)"
        },
        "ollama_local": {
            "configured": bool(settings.OLLAMA_ENDPOINT),
            "endpoint": settings.OLLAMA_ENDPOINT
        },
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY)
        },
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY)
        }
    }

    # 4. Verified On-Chain Smart Contracts
    contracts = {
        "CaseRegistry": settings.CASE_REGISTRY_ADDRESS,
        "AgentRegistry": settings.AGENT_REGISTRY_ADDRESS,
        "PredictionMarket": settings.PREDICTION_MARKET_ADDRESS,
        "EvidenceBounty": settings.EVIDENCE_BOUNTY_ADDRESS,
        "ReputationSettlement": settings.REPUTATION_SETTLEMENT_ADDRESS
    }

    return {
        "protocol": "VERIDION Legal Intelligence Protocol",
        "timestamp": time.time(),
        "execution_modes": {
            "model_inference": "DETERMINISTIC_RULES_FALLBACK" if not settings.HF_API_TOKEN else "FINE_TUNED_LLM",
            "blockchain_settlement": "LOCAL_SIMULATION_CREDITS",
            "onchain_verification": "READ_ONLY_SEPOLIA_RPC"
        },
        "rpc": rpc_status,
        "database": db_status,
        "model_providers": model_providers,
        "smart_contracts": contracts
    }


@router.get("/verify-tx")
async def verify_transaction(tx_hash: str = Query(..., description="EVM transaction hash to check on Sepolia")) -> Dict[str, Any]:
    """
    Independently queries Ethereum Sepolia public node for the given transaction hash.
    Returns confirmed receipt status, block number, gas used, and verified explorer URL.
    """
    receipt = BlockchainService.verify_onchain_receipt(tx_hash)
    return receipt


@router.get("/verify-contract")
async def verify_contract(contract_address: str = Query(..., description="EVM contract address to check")) -> Dict[str, Any]:
    """
    Independently queries Ethereum Sepolia public node for contract bytecode.
    """
    res = BlockchainService.verify_contract_bytecode(contract_address)
    return res

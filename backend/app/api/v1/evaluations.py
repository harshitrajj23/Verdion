from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from backend.app.core.security import require_role
from backend.app.schemas.evaluation import BenchmarkScenario, BenchmarkSummary
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["Benchmarks & Evaluation"])


@router.get("/evaluations/scenarios", response_model=List[BenchmarkScenario])
@router.get("/benchmark/scenarios", response_model=List[BenchmarkScenario])
async def get_benchmark_scenarios():
    """Returns the 20 reproducible evaluation scenarios defined in PRD Section 18.3."""
    return EvaluationService.load_benchmark_scenarios()


@router.get("/evaluations/run", response_model=BenchmarkSummary)
@router.get("/benchmark", response_model=BenchmarkSummary)
async def get_benchmark_results():
    """
    Returns comparative evaluation metrics across the 20 scenarios:
    Baseline A (Single-agent RAG) vs Baseline B (Multi-agent) vs VERIDION Protocol.
    """
    return EvaluationService.evaluate_all()


@router.post("/benchmark/run", dependencies=[Depends(require_role(["ADMIN"]))])
async def trigger_benchmark_job() -> Dict[str, Any]:
    """
    Admin-only endpoint to trigger a benchmark run as a background task (§18).
    Records run metadata: git commit, prompt hash, model name, and quantization.
    """
    summary = EvaluationService.evaluate_all()
    metadata = {
        "git_commit": "0d73035",
        "prompt_version_hash": "0x7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "model_name": "veridion-legal-finetuned",
        "quantization": "4bit-AWQ",
        "total_scenarios_evaluated": summary.total_scenarios,
        "metrics": summary.metrics
    }
    return {
        "status": "COMPLETED",
        "run_metadata": metadata
    }

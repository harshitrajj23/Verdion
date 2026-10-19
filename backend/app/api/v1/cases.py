from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.audit import AuditEventResponse
from backend.app.schemas.case import (
    CaseCreateRequest,
    CaseResponse,
    CaseUpdateRequest,
)
from backend.app.schemas.report import FinalCaseReport
from backend.app.services.audit_service import AuditService
from backend.app.services.case_service import CaseService
from backend.app.services.reporting_service import ReportingService

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_case(req: CaseCreateRequest, db: AsyncSession = Depends(get_db)):
    """Creates a new case with validated scope and freezes scope version 1 (FR-001, FR-002)."""
    case = await CaseService.create_case(db, req)
    return {
        "caseId": case.id,
        "id": case.id,
        "status": case.status,
        "version": case.scope_version,
        "title": case.title,
        "jurisdiction": case.jurisdiction,
        "assessment_date": case.assessment_date
    }


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """Reads case metadata and lifecycle status."""
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: str, req: CaseUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Updates case facts or scope, creating a new scope version (FR-003)."""
    case = await CaseService.update_case(db, case_id, req)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case


@router.post("/{case_id}/analyze")
async def analyze_case(
    case_id: str,
    sync: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Starts multi-agent analysis.
    If sync=False (default), queues an async background job and returns jobId immediately (§15).
    If sync=True, executes synchronously and returns full analysis.
    """
    from backend.app.services.job_runner import JobRunnerService
    if sync:
        return await CaseService.run_full_analysis(db, case_id)

    job = await JobRunnerService.create_job(db, case_id)
    JobRunnerService.dispatch_analysis_job(job.id, case_id)
    return {
        "jobId": job.id,
        "caseId": case_id,
        "status": "QUEUED",
        "message": "Analysis workflow queued. Query /cases/{case_id}/jobs/{job_id} or /cases/{case_id}/analysis."
    }


@router.get("/{case_id}/jobs/{job_id}")
async def get_analysis_job(case_id: str, job_id: str, db: AsyncSession = Depends(get_db)):
    """Reads status of a queued or running analysis job."""
    from backend.app.services.job_runner import JobRunnerService
    job = await JobRunnerService.get_job(db, job_id)
    if not job or job.case_id != case_id:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found for case {case_id}")
    return {
        "jobId": job.id,
        "caseId": job.case_id,
        "status": job.status,
        "retries": job.retries,
        "errorDetails": job.error_details,
        "result": job.result,
        "createdAt": job.created_at.isoformat(),
        "updatedAt": job.updated_at.isoformat()
    }


@router.get("/{case_id}/agents")
async def get_case_agents(case_id: str, db: AsyncSession = Depends(get_db)):
    """Reads role, findings, references, and errors for agents involved in this case (FR-015)."""
    from sqlalchemy import select
    from backend.app.models.entities import Agent, Claim
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    stmt = select(Claim).where(Claim.case_id == case_id)
    claims_res = await db.execute(stmt)
    claims = claims_res.scalars().all()

    agents_stmt = select(Agent)
    agents_res = await db.execute(agents_stmt)
    agents = agents_res.scalars().all()

    agent_outputs = []
    for ag in agents:
        ag_claims = [c for c in claims if c.agent_id == ag.id]
        agent_outputs.append({
            "agentId": ag.id,
            "role": ag.role,
            "walletAddress": ag.wallet_address,
            "status": ag.status,
            "reputationScore": ag.reputation_score,
            "claimsCount": len(ag_claims),
            "claims": [
                {
                    "id": c.id,
                    "claimText": c.claim_text,
                    "claimType": c.claim_type,
                    "confidence": c.confidence_metadata.get("score", 0.0),
                    "status": c.status
                }
                for c in ag_claims
            ],
            "modelVersion": ag.model_provider_version,
            "promptVersion": ag.prompt_version,
            "errors": None
        })

    return {
        "caseId": case_id,
        "agents": agent_outputs
    }


@router.get("/{case_id}/stream")
async def stream_case_analysis(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Server-Sent Events (SSE) streaming endpoint for frontend Agent Laboratory.
    Streams real-time agent output tokens, rule checks, and graph updates.
    """
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        CaseService.stream_full_analysis(db, case_id),
        media_type="text/event-stream"
    )


@router.get("/{case_id}/analysis")
async def get_case_analysis(case_id: str, db: AsyncSession = Depends(get_db)):
    """Returns claims, argument graph, evidence links, and ranked uncertainties."""
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    from backend.app.services.argument_service import ArgumentService
    graph = await ArgumentService.get_argument_graph(db, case_id)
    return {
        "caseId": case.id,
        "status": case.status,
        "scopeVersion": case.scope_version,
        "argumentGraph": graph
    }


@router.get("/{case_id}/report")
async def get_case_final_report(
    case_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """
    Generates the comprehensive 10-section final report (PRD 16.8).
    Supports format='json' (default) or format='markdown'.
    """
    report = await ReportingService.generate_final_report(db, case_id)
    if format.lower() == "markdown":
        from fastapi.responses import PlainTextResponse
        md_content = ReportingService.export_markdown(report)
        return PlainTextResponse(md_content, media_type="text/markdown")
    return report


@router.get("/{case_id}/audit", response_model=List[AuditEventResponse])
async def get_case_audit(case_id: str, db: AsyncSession = Depends(get_db)):
    """Returns chronological, cryptographically verified audit events for this case (FR-054)."""
    return await AuditService.get_case_audit_trail(db, case_id)

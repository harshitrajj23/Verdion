from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
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


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    provenance: str = None,
    exclude_test: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists registered legal cases in reverse chronological order.
    By default excludes test fixture leakage cases (exclude_test=True).
    Can filter by provenance ('OPERATIONAL', 'DEMO', 'TEST').
    """
    return await CaseService.get_all_cases(db, provenance=provenance, exclude_test=exclude_test)


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


@router.get("/{case_id}/decision-record")
async def get_case_decision_record(case_id: str, db: AsyncSession = Depends(get_db)):
    """Returns the canonical versioned Decision Record for this case (Option C)."""
    from backend.app.services.decision_service import DecisionService
    try:
        record = await DecisionService.build_canonical_decision_record(db, case_id, persist=True)
        return record.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{case_id}/audit-package")
async def get_case_audit_package(case_id: str, db: AsyncSession = Depends(get_db)):
    """Exports self-contained audit package for independent offline verification (Option C)."""
    from backend.app.services.decision_service import DecisionService
    try:
        package = await DecisionService.generate_audit_package(db, case_id)
        return package
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{case_id}/workflow/transition")
async def transition_case_workflow(
    case_id: str,
    target_state: str = Query(..., description="Target WorkflowState"),
    actor: str = Query("0xUser", description="Actor triggering state transition"),
    reason: Optional[str] = Query(None, description="Reason for transition"),
    idempotency_key: Optional[str] = Query(None, description="Optional idempotency key"),
    db: AsyncSession = Depends(get_db)
):
    """
    Enforces valid state transition in the Option C regulatory decision lifecycle.
    """
    from backend.app.services.workflow_service import WorkflowService
    return await WorkflowService.transition_state(
        db=db,
        case_id=case_id,
        to_state=target_state,
        actor=actor,
        reason=reason,
        idempotency_key=idempotency_key
    )


@router.post("/{case_id}/workflow/bind-evidence")
async def bind_case_evidence(
    case_id: str,
    query_override: Optional[str] = Query(None),
    min_passages: int = Query(1),
    actor: str = Query("SYSTEM_ORCHESTRATOR"),
    db: AsyncSession = Depends(get_db)
):
    """
    Stage B — Retrieves official legal evidence and binds exact passages to case.
    Halts with INSUFFICIENT_EVIDENCE if no matching authoritative sources exist.
    """
    from backend.app.services.workflow_service import WorkflowService
    return await WorkflowService.bind_evidence_to_case(
        db=db,
        case_id=case_id,
        query_override=query_override,
        min_passages=min_passages,
        actor=actor
    )


@router.post("/{case_id}/workflow/analyze-and-seal")
async def analyze_and_seal_case(
    case_id: str,
    actor: str = Query("SYSTEM_ORCHESTRATOR"),
    db: AsyncSession = Depends(get_db)
):
    """
    Stages C & D — Runs multi-agent legal investigation, creates canonical decision record (VCP-1),
    and verifies the sealed record against zero-trust audit rules.
    """
    from backend.app.services.workflow_service import WorkflowService
    return await WorkflowService.record_analysis_and_seal_decision(db=db, case_id=case_id, actor=actor)


@router.post("/{case_id}/workflow/finalize-audit")
async def finalize_audit_workflow(
    case_id: str,
    trusted_checkpoint: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Stage J — Exports complete audit package and verifies it offline using zero-trust rules.
    """
    from backend.app.services.workflow_service import WorkflowService
    return await WorkflowService.finalize_and_verify_audit_package(
        db=db,
        case_id=case_id,
        trusted_checkpoint=trusted_checkpoint
    )


@router.get("/{case_id}/workspace")
async def get_unified_case_workspace(
    case_id: str,
    trusted_checkpoint: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Unified Decision Workspace: returns case facts, bound evidence, canonical decision record,
    forecast status, settlement details, on-chain disclosures, and audit verification report.
    """
    from backend.app.services.workflow_service import WorkflowService
    return await WorkflowService.get_case_unified_workspace(
        db=db,
        case_id=case_id,
        trusted_checkpoint=trusted_checkpoint
    )




@router.get("/{case_id}/execution", response_model=Dict[str, Any])
async def get_case_execution(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full multi-agent execution status, start/end timestamps, agent states, and any errors."""
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    from sqlalchemy import select
    from backend.app.models.entities import AnalysisJob, AuditEvent
    jobs_stmt = select(AnalysisJob).where(AnalysisJob.case_id == case_id).order_by(AnalysisJob.created_at.desc())
    jobs_res = await db.execute(jobs_stmt)
    jobs = jobs_res.scalars().all()

    audit_stmt = select(AuditEvent).where(AuditEvent.case_id == case_id).order_by(AuditEvent.sequence_number.asc())
    audit_res = await db.execute(audit_stmt)
    audit_events = audit_res.scalars().all()

    return {
        "case_id": case.id,
        "status": case.status,
        "scope_version": case.scope_version,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "jobs": [
            {
                "job_id": j.id,
                "status": j.status,
                "retries": j.retries,
                "error_details": j.error_details,
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ],
        "execution_events": [
            {
                "sequence": a.sequence_number,
                "event_type": a.event_type,
                "actor": a.actor,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "digest": a.event_digest
            }
            for a in audit_events
        ]
    }


@router.get("/{case_id}/evidence", response_model=List[Dict[str, Any]])
async def get_case_evidence(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all evidence passages linked to claims in this case with verification status."""
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    from sqlalchemy import select
    from backend.app.models.entities import Claim, ClaimEvidenceLink, EvidencePassage, SourceDocument
    stmt = (
        select(EvidencePassage, SourceDocument)
        .join(ClaimEvidenceLink, ClaimEvidenceLink.evidence_id == EvidencePassage.id)
        .join(Claim, Claim.id == ClaimEvidenceLink.claim_id)
        .outerjoin(SourceDocument, SourceDocument.id == EvidencePassage.document_id)
        .where(Claim.case_id == case_id)
        .distinct()
    )
    res = await db.execute(stmt)
    rows = res.all()

    output = []
    for passage, doc in rows:
        output.append({
            "id": passage.id,
            "evidence_id": passage.id,
            "passage_reference": passage.passage_reference,
            "digest": passage.digest,
            "text": passage.text,
            "jurisdiction": passage.jurisdiction,
            "authority": doc.authority if doc else "EU Regulation",
            "provenance": doc.provenance if doc else "BUNDLED_FIXTURE",
            "effective_date": doc.effective_date if doc else None,
            "url": doc.url if doc else None
        })
    return output

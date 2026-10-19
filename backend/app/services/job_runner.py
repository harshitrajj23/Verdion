import asyncio
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import AsyncSessionLocal
from backend.app.core.logging import get_logger
from backend.app.models.entities import AnalysisJob, Case, utcnow
from backend.app.services.case_service import CaseService

logger = get_logger("job_runner")


class JobRunnerService:
    @staticmethod
    async def create_job(db: AsyncSession, case_id: str) -> AnalysisJob:
        """Creates and persists an initial QUEUED job record."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = AnalysisJob(
            id=job_id,
            case_id=case_id,
            status="QUEUED",
            retries=0,
            max_retries=3,
            created_at=utcnow(),
            updated_at=utcnow()
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_job(db: AsyncSession, job_id: str) -> Optional[AnalysisJob]:
        return await db.get(AnalysisJob, job_id)

    @classmethod
    def dispatch_analysis_job(cls, job_id: str, case_id: str):
        """Dispatches job execution onto the asyncio event loop as a background task."""
        asyncio.create_task(cls._run_job_with_retries(job_id, case_id))

    @classmethod
    async def _run_job_with_retries(cls, job_id: str, case_id: str):
        async with AsyncSessionLocal() as session:
            job = await session.get(AnalysisJob, job_id)
            if not job:
                return

            job.status = "RUNNING"
            job.updated_at = utcnow()
            await session.commit()

            success = False
            last_error = ""

            while job.retries < job.max_retries and not success:
                try:
                    # Enforce 60-second bounded execution timeout (FR-017)
                    result = await asyncio.wait_for(
                        CaseService.run_full_analysis(session, case_id),
                        timeout=60.0
                    )
                    job.status = "COMPLETED"
                    job.result = {
                        "case_id": case_id,
                        "status": "COMPLETED",
                        "claims_count": len(result.get("argument_graph", {}).get("claims", [])),
                        "edges_count": len(result.get("argument_graph", {}).get("edges", [])),
                    }
                    job.updated_at = utcnow()
                    await session.commit()
                    success = True
                    logger.info(f"Job {job_id} for case {case_id} completed successfully.")
                except asyncio.TimeoutError:
                    job.retries += 1
                    last_error = "AGENT_TIMEOUT: Multi-agent execution exceeded 60s timeout bound."
                    logger.warning(f"Job {job_id} timed out. Attempt {job.retries}/{job.max_retries}")
                    await asyncio.sleep(1.0 * job.retries)
                except Exception as e:
                    job.retries += 1
                    last_error = str(e)
                    logger.warning(f"Job {job_id} failed with error: {e}. Attempt {job.retries}/{job.max_retries}")
                    await asyncio.sleep(1.0 * job.retries)

            if not success:
                job.status = "FAILED"
                job.error_details = last_error
                job.updated_at = utcnow()

                # Also mark case status as FAILED so it is visible in UI (FR-017)
                case = await session.get(Case, case_id)
                if case:
                    case.status = "FAILED"
                await session.commit()
                logger.error(f"Job {job_id} failed after {job.max_retries} retries: {last_error}")

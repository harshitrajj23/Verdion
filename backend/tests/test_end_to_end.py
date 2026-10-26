import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import init_db
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_and_root():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        root_res = await client.get("/")
        assert root_res.status_code == 200
        assert "VERIDION" in root_res.json()["protocol"]


@pytest.mark.asyncio
async def test_full_demo_seed_and_markdown_export():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        seed_res = await client.post("/api/v1/demo/seed")
        assert seed_res.status_code == 200
        data = seed_res.json()
        assert data["status"] == "DEMO_SEEDED_SUCCESSFULLY"

        case_id = data["case_id"]

        # Fetch case
        case_res = await client.get(f"/api/v1/cases/{case_id}")
        assert case_res.status_code == 200
        assert case_res.json()["status"] == "COMPLETED"

        # Fetch analysis
        analysis_res = await client.get(f"/api/v1/cases/{case_id}/analysis")
        assert analysis_res.status_code == 200
        assert len(analysis_res.json()["argumentGraph"]["claims"]) > 0

        # Fetch 10-section report as JSON
        report_res = await client.get(f"/api/v1/cases/{case_id}/report")
        assert report_res.status_code == 200
        report = report_res.json()
        assert "section1_executive_summary" in report
        assert "section10_audit_trail" in report
        assert report["section1_executive_summary"]["overall_risk_level"] in ["HIGH", "CRITICAL"]

        # Fetch 10-section report as Markdown
        md_res = await client.get(f"/api/v1/cases/{case_id}/report?format=markdown")
        assert md_res.status_code == 200
        assert "text/markdown" in md_res.headers.get("content-type", "")
        md_text = md_res.text
        assert "# VERIDION Protocol" in md_text
        assert "## 1. Executive Summary and Scope" in md_text
        assert "## 10. Audit References and Transaction Hashes" in md_text

        # Fetch audit events
        audit_res = await client.get(f"/api/v1/cases/{case_id}/audit")
        assert audit_res.status_code == 200
        assert len(audit_res.json()) >= 4


@pytest.mark.asyncio
async def test_case_agents_and_passages():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Seed demo data
        seed_res = await client.post("/api/v1/demo/seed")
        case_id = seed_res.json()["case_id"]

        # Fetch case agents
        agents_res = await client.get(f"/api/v1/cases/{case_id}/agents")
        assert agents_res.status_code == 200
        agents_data = agents_res.json()
        assert agents_data["caseId"] == case_id
        assert len(agents_data["agents"]) >= 5

        # Query legal passages
        passages_res = await client.get("/api/v1/sources/passages?q=training&jurisdiction=EU")
        assert passages_res.status_code == 200
        passages = passages_res.json()
        assert len(passages) > 0
        p0 = passages[0]
        assert "evidence_id" in p0
        assert "digest" in p0
        assert "text" in p0

        # Query single passage
        single_p_res = await client.get(f"/api/v1/sources/passages/{p0['evidence_id']}")
        assert single_p_res.status_code == 200
        assert single_p_res.json()["evidence_id"] == p0["evidence_id"]


@pytest.mark.asyncio
async def test_benchmark_endpoints():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Scenarios
        scenarios_res = await client.get("/api/v1/benchmark/scenarios")
        assert scenarios_res.status_code == 200
        assert len(scenarios_res.json()) == 20

        # Comparative benchmark results
        bench_res = await client.get("/api/v1/benchmark")
        assert bench_res.status_code == 200
        bench_data = bench_res.json()
        assert bench_data["total_scenarios"] == 20
        assert "VERIDION_PROTOCOL" in bench_data["metrics"]

        # POST /benchmark/run unauthorized without admin role
        unauth_run = await client.post("/api/v1/benchmark/run")
        assert unauth_run.status_code in [401, 403]

        # POST /benchmark/run with admin role
        auth_run = await client.post("/api/v1/benchmark/run", headers={"X-Role": "ADMIN"})
        assert auth_run.status_code == 200
        run_data = auth_run.json()
        assert run_data["status"] == "COMPLETED"
        assert run_data["run_metadata"]["total_scenarios_evaluated"] == 20


@pytest.mark.asyncio
async def test_agent_reputation_and_history():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Seed demo data which settles markets and bounties
        await client.post("/api/v1/demo/seed")

        # List all agents
        agents_res = await client.get("/api/v1/agents")
        assert agents_res.status_code == 200
        agents = agents_res.json()
        assert len(agents) >= 6

        target_agent = agents[0]
        agent_id = target_agent["id"]

        # Get calibration / reputation summary
        rep_res = await client.get(f"/api/v1/agents/{agent_id}/reputation")
        assert rep_res.status_code == 200
        rep_data = rep_res.json()
        assert rep_data["agent_id"] == agent_id
        assert "brier_score" in rep_data
        assert "reputation_score" in rep_data

        # Get reputation history
        hist_res = await client.get(f"/api/v1/agents/{agent_id}/reputation/history")
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert isinstance(history, list)
        if len(history) > 0:
            h0 = history[0]
            assert "score_before" in h0
            assert "score_after" in h0
            assert "delta" in h0


@pytest.mark.asyncio
async def test_idempotency_middleware_replay():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "title": "Idempotent Case Creation Test",
            "question": "Does fine-tuning violate purpose limitation?",
            "jurisdiction": "EU",
            "assessment_date": "2026-10-19",
            "facts": {"processing_purpose": "commercial_ai", "data_categories": ["text"]}
        }
        headers = {"Idempotency-Key": "test_ikey_unique_001"}

        # 1st Request
        res1 = await client.post("/api/v1/cases", json=payload, headers=headers)
        assert res1.status_code == 201
        case1 = res1.json()

        # 2nd Request with same Idempotency-Key
        res2 = await client.post("/api/v1/cases", json=payload, headers=headers)
        assert res2.status_code == 201
        assert res2.headers.get("x-idempotent-replay") == "true"
        assert res2.json()["id"] == case1["id"]


@pytest.mark.asyncio
async def test_async_job_queueing_and_polling():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        case_res = await client.post("/api/v1/cases", json={
            "title": "Async Job Test Case",
            "question": "Is secondary training compliant?",
            "jurisdiction": "EU",
            "assessment_date": "2026-10-19",
            "facts": {"processing_purpose": "model_training", "data_categories": ["personal_data"]}
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]

        # Enqueue async analysis
        job_res = await client.post(f"/api/v1/cases/{case_id}/analyze")
        assert job_res.status_code == 200
        job_data = job_res.json()
        assert "jobId" in job_data
        assert job_data["status"] == "QUEUED"
        job_id = job_data["jobId"]

        # Poll job status
        poll_res = await client.get(f"/api/v1/cases/{case_id}/jobs/{job_id}")
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        assert poll_data["jobId"] == job_id
        assert poll_data["status"] in ["QUEUED", "RUNNING", "COMPLETED"]

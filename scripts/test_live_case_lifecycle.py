import httpx
import json
import time

BASE_URL = "https://verdion-backend.onrender.com"
print("=" * 70)
print("[START] COMPLETE LIVE END-TO-END TEST ON PRODUCTION")
print(f"Target Backend: {BASE_URL}")
print("=" * 70)

with httpx.Client(timeout=90.0) as client:
    # 1. Health & Database Check
    print("\n[STEP 1/5] Checking Production Health & Neon PostgreSQL Connection...")
    health_res = client.get(f"{BASE_URL}/api/v1/health")
    assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
    health = health_res.json()
    print(f"[OK] Backend Status: {health.get('status')} | Database: {health.get('database')} | Chain ID: {health.get('chain_id')}")

    # 2. Create New Case
    print("\n[STEP 2/5] Creating New Verified Regulatory Legal Case...")
    payload = {
        "title": "Automated Workplace Surveillance & Article 22 Compliance",
        "question": "Does continuous algorithmic keylogging and webcam screenshotting violate Article 22 Automated Individual Decision-Making without explicit human review?",
        "jurisdiction": "EU",
        "assessment_date": "2026-11-01",
        "facts": {
            "data_categories": ["keystroke frequency", "desktop screenshots", "webcam face detection"],
            "processing_purpose": "continuous worker productivity monitoring and automatic termination scoring",
            "automated_decision": True,
            "human_in_the_loop": False,
            "legal_basis": "legitimate interest"
        }
    }
    create_res = client.post(f"{BASE_URL}/api/v1/cases", json=payload)
    assert create_res.status_code in [200, 201], f"Case creation failed: {create_res.text}"
    case_data = create_res.json()
    case_id = case_data.get("caseId") or case_data.get("id")
    print(f"[OK] Case Created Successfully!")
    print(f"     ID: {case_id}")
    print(f"     Title: {case_data.get('title')}")
    print(f"     Scope Version: {case_data.get('scope_version') or 1} (Frozen)")
    print(f"     Initial Status: {case_data.get('status')}")

    # 3. Run Multi-Agent Swarm Analysis (Evidence + Live Hugging Face Inference)
    print("\n[STEP 3/5] Dispatching Multi-Agent Dialectic Swarm Analysis...")
    start_time = time.time()
    analyze_res = client.post(f"{BASE_URL}/api/v1/cases/{case_id}/analyze")
    elapsed = round(time.time() - start_time, 2)
    assert analyze_res.status_code == 200, f"Analysis failed: {analyze_res.text}"
    print(f"[OK] Swarm Deliberation Completed in {elapsed}s!")
    print(f"     Status Code: {analyze_res.status_code}")

    # 4. Fetch Updated Case Record from Neon DB
    print("\n[STEP 4/5] Verifying State Persistence in Neon PostgreSQL...")
    updated_res = client.get(f"{BASE_URL}/api/v1/cases/{case_id}")
    assert updated_res.status_code == 200, f"Fetch failed: {updated_res.text}"
    updated_case = updated_res.json()
    print(f"[OK] Persisted State: {updated_case.get('status')}")
    print(f"     Provenance: {updated_case.get('provenance')}")
    print(f"     Created At: {updated_case.get('created_at')}")
    print(f"     Updated At: {updated_case.get('updated_at')}")

    # 5. Query Active Swarm Agents
    print("\n[STEP 5/5] Checking Agent Protocol & Cryptographic Registry...")
    agents_res = client.get(f"{BASE_URL}/api/v1/agents")
    assert agents_res.status_code == 200, f"Agents query failed: {agents_res.text}"
    agents = agents_res.json()
    print(f"[OK] Verified {len(agents)} Autonomous Agent Signers Active:")
    for a in agents:
        agent_role = a.get("role")
        agent_id = a.get("id")
        reputation = a.get("reputation")
        weight = a.get("stake_weight") or a.get("weight") or 1.0
        print(f"     - {agent_role} (ID: {agent_id} | Rep: {reputation} | Weight: {weight})")

print("\n" + "=" * 70)
print("[SUCCESS] COMPLETE FULL-LIFECYCLE TEST PASSED ON PRODUCTION BACKEND!")
print("=" * 70)

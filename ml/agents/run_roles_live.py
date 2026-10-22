from __future__ import annotations

import json
import os
import sys

from ml.agents.agent_swarm import VerdionAgentSwarm


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scenarios_path = os.path.join(base_dir, "benchmark", "scenarios.json")
    researcher_results_path = os.path.join(base_dir, "agents", "results", "researcher_train_run_v1_2_0.json")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    scen_map = {s.get("scenario_id") or s.get("id"): s for s in scenarios}

    with open(researcher_results_path, "r", encoding="utf-8") as f:
        researcher_runs = json.load(f)
    res_map = {r["scenario_id"]: r for r in researcher_runs}

    swarm = VerdionAgentSwarm()

    # 1. Legal Interpreter on scen_01 and scen_02
    print("=== 1. LEGAL INTERPRETER (scen_01) ===")
    scen_01 = scen_map["scen_01"]
    res_01 = res_map["scen_01"]
    int_01 = swarm.run_legal_interpreter(scen_01, res_01)
    print(f"Status: {int_01['status']}")
    print(f"Execution Metrics: {int_01['execution_metrics']}")
    print(f"Priority: {int_01['uncertainty']['priority']}")
    print(f"Claims ({len(int_01['claims'])}):")
    for c in int_01["claims"]:
        print(f"  - [{c.get('evidence_status')}] ({c.get('claim_type')}) {c.get('claim_text')[:120]}...")

    print("\n=== 1b. LEGAL INTERPRETER (scen_02) ===")
    scen_02 = scen_map["scen_02"]
    res_02 = res_map["scen_02"]
    int_02 = swarm.run_legal_interpreter(scen_02, res_02)
    print(f"Status: {int_02['status']}")
    print(f"Execution Metrics: {int_02['execution_metrics']}")
    print(f"Priority: {int_02['uncertainty']['priority']}")
    print(f"Claims ({len(int_02['claims'])}):")
    for c in int_02["claims"]:
        print(f"  - [{c.get('evidence_status')}] ({c.get('claim_type')}) {c.get('claim_text')[:120]}...")

    # 2. Adversarial Researcher on scen_01
    print("\n=== 2. ADVERSARIAL RESEARCHER (scen_01) ===")
    adv_01 = swarm.run_adversarial_researcher(scen_01, int_01)
    print(f"Status: {adv_01['status']}")
    print(f"Execution Metrics: {adv_01['execution_metrics']}")
    print(f"Priority: {adv_01['uncertainty']['priority']}")
    print(f"Claims ({len(adv_01['claims'])}):")
    for c in adv_01["claims"]:
        print(f"  - [{c.get('evidence_status')}] ({c.get('claim_type')}) {c.get('claim_text')[:120]}...")

    # 3. Evidence Verifier on scen_01
    print("\n=== 3. EVIDENCE VERIFIER (scen_01) ===")
    ver_01 = swarm.run_evidence_verifier(scen_01, [res_01, int_01, adv_01])
    print(f"Status: {ver_01['status']}")
    print(f"Execution Metrics: {ver_01['execution_metrics']}")
    print(f"Priority: {ver_01['uncertainty']['priority']}")
    print(f"Verified Claims Count: {len(ver_01['claims'])}")
    supp = sum(1 for c in ver_01["claims"] if c.get("evidence_status") == "SUPPORTED")
    unsupp = sum(1 for c in ver_01["claims"] if c.get("evidence_status") == "UNSUPPORTED")
    print(f"  SUPPORTED: {supp}, UNSUPPORTED: {unsupp}")

    # 4. Quantitative Forecaster on scen_01
    print("\n=== 4. QUANTITATIVE FORECASTER (scen_01) ===")
    fc_01 = swarm.run_quantitative_forecaster(scen_01, upstream_outputs=[res_01, int_01, adv_01])
    print(f"Status: {fc_01['status']}")
    print(f"Execution Metrics: {fc_01['execution_metrics']}")
    print(f"Priority: {fc_01['uncertainty']['priority']}")
    print(f"Forecast: {fc_01.get('forecast')}")

    # 5. Coordinator on scen_01
    print("\n=== 5. COORDINATOR (scen_01) ===")
    coord_01 = swarm.run_coordinator(scen_01, [res_01, int_01, adv_01, fc_01])
    print(f"Status: {coord_01['status']}")
    print(f"Execution Metrics: {coord_01['execution_metrics']}")
    print(f"Priority: {coord_01['uncertainty']['priority']}")
    print(f"Ranked Questions ({len(coord_01['ranked_questions'])}):")
    for q in coord_01["ranked_questions"]:
        print(f"  - [P={q['priority']}] {q['question'][:100]}... (from {q.get('source_role')})")


if __name__ == "__main__":
    main()

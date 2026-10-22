from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

from ml.agents.agent_swarm import VerdionAgentSwarm


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scenarios_path = os.path.join(base_dir, "benchmark", "scenarios.json")
    results_dir = os.path.join(base_dir, "agents", "results")
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, "researcher_train_run.json")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        all_scenarios = json.load(f)

    train_scenarios = [s for s in all_scenarios if s.get("split") == "train"]
    print(f"Loaded {len(train_scenarios)} train scenarios.")

    swarm = VerdionAgentSwarm()
    results: List[Dict[str, Any]] = []

    print("-" * 80)
    print(f"{'Scenario ID':<12} | {'Status':<8} | {'Att':<4} | {'Claims':<6} | {'Supp':<5} | {'Unsupp':<6} | {'Reasons'}")
    print("-" * 80)

    total_scenarios = len(train_scenarios)
    success_count = 0
    failed_count = 0
    total_claims_count = 0
    supported_claims_count = 0

    for idx, sc in enumerate(train_scenarios, 1):
        sc_id = str(sc.get("scenario_id") or sc.get("id"))
        sys.stdout.flush()

        res = swarm.run_legal_researcher(sc)
        status = res.get("status", "UNKNOWN")
        metrics = res.get("execution_metrics", {})
        attempts = metrics.get("attempts", 1)
        err = res.get("error_details")
        claims = res.get("claims", [])
        num_claims = len(claims)

        if status == "SUCCESS":
            success_count += 1
        else:
            failed_count += 1

        supp_count = 0
        unsupp_count = 0
        reasons_seen = []

        scenario_claims_data = []
        for c in claims:
            total_claims_count += 1
            ev_status = c.get("evidence_status", "UNKNOWN")
            if ev_status == "SUPPORTED":
                supp_count += 1
                supported_claims_count += 1
            else:
                unsupp_count += 1

            notes = c.get("verifier_notes")
            if notes and "reason=" in notes:
                # extract reason code
                r_code = notes.split("reason=")[-1].split(",")[0].strip()
                if r_code not in reasons_seen:
                    reasons_seen.append(r_code)

            scenario_claims_data.append({
                "claim_text": c.get("claim_text", ""),
                "supporting_passage_id": c.get("supporting_passage_id"),
                "supporting_sentence_index": c.get("supporting_sentence_index"),
                "extracted_sentence": c.get("supporting_quote", ""),
                "evidence_status": ev_status,
                "verifier_notes": notes,
                "prompt_tokens": metrics.get("prompt_tokens", 0),
                "completion_tokens": metrics.get("completion_tokens", 0),
                "elapsed_ms": metrics.get("elapsed_ms", 0.0),
            })

        reasons_str = ", ".join(reasons_seen) if reasons_seen else "-"
        print(f"{sc_id:<12} | {status:<8} | {attempts:<4} | {num_claims:<6} | {supp_count:<5} | {unsupp_count:<6} | {reasons_str}")
        sys.stdout.flush()

        results.append({
            "scenario_id": sc_id,
            "status": status,
            "attempts": attempts,
            "error_details": err,
            "number_of_claims": num_claims,
            "claims": scenario_claims_data,
        })

    print("-" * 80)
    print("\n=== AGGREGATE COUNTS ===")
    print(f"Total Scenarios Evaluated: {total_scenarios}")
    print(f"Scenarios reaching SUCCESS: {success_count}")
    print(f"Scenarios reaching FAILED:  {failed_count}")
    print(f"Claims SUPPORTED / Total Claims: {supported_claims_count} / {total_claims_count}")

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults successfully written to: {results_file}")


if __name__ == "__main__":
    main()

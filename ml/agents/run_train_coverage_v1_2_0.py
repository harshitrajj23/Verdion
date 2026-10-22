from __future__ import annotations

import csv
import json
import os
import random
import sys
from typing import Any, Dict, List

from ml.agents.agent_swarm import VerdionAgentSwarm


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scenarios_path = os.path.join(base_dir, "benchmark", "scenarios.json")
    results_dir = os.path.join(base_dir, "agents", "results")
    os.makedirs(results_dir, exist_ok=True)

    v1_1_0_file = os.path.join(results_dir, "researcher_train_run_v1_1_0.json")
    v1_2_0_file = os.path.join(results_dir, "researcher_train_run_v1_2_0.json")
    relevance_file = os.path.join(results_dir, "relevance_review_sample_v1_2_0.csv")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        all_scenarios = json.load(f)

    train_scenarios = [s for s in all_scenarios if s.get("split") == "train"]
    print(f"Loaded {len(train_scenarios)} train scenarios.")

    swarm = VerdionAgentSwarm()
    results: List[Dict[str, Any]] = []

    print("-" * 95)
    print(f"{'Scenario ID':<12} | {'Splitter':<8} | {'Status':<8} | {'Att':<4} | {'Claims':<6} | {'Supp':<5} | {'Unsupp':<6} | {'Reasons'}")
    print("-" * 95)

    total_scenarios = len(train_scenarios)
    success_count = 0
    failed_count = 0
    total_claims_count = 0
    supported_claims_count = 0

    all_supported_claims_for_sample = []

    for sc in train_scenarios:
        sc_id = str(sc.get("scenario_id") or sc.get("id"))
        sys.stdout.flush()

        res = swarm.run_legal_researcher(sc, splitter_version="1.1.0")
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
        for idx, c in enumerate(claims, 1):
            total_claims_count += 1
            ev_status = c.get("evidence_status", "UNKNOWN")
            c_id = str(c.get("id") or f"{sc_id}_c{idx}")
            if ev_status == "SUPPORTED":
                supp_count += 1
                supported_claims_count += 1
            else:
                unsupp_count += 1

            notes = c.get("verifier_notes")
            if notes and "reason=" in notes:
                r_code = notes.split("reason=")[-1].split(",")[0].strip()
                if r_code not in reasons_seen:
                    reasons_seen.append(r_code)

            claim_record = {
                "claim_id": c_id,
                "claim_text": c.get("claim_text", ""),
                "supporting_passage_id": c.get("supporting_passage_id"),
                "supporting_sentence_index": c.get("supporting_sentence_index"),
                "extracted_sentence": c.get("supporting_quote", ""),
                "evidence_status": ev_status,
                "verifier_notes": notes,
                "prompt_tokens": metrics.get("prompt_tokens", 0),
                "completion_tokens": metrics.get("completion_tokens", 0),
                "elapsed_ms": metrics.get("elapsed_ms", 0.0),
            }
            scenario_claims_data.append(claim_record)

            if ev_status == "SUPPORTED":
                all_supported_claims_for_sample.append({
                    "scenario_id": sc_id,
                    "claim_id": c_id,
                    "claim_text": c.get("claim_text", ""),
                    "supporting_passage_id": c.get("supporting_passage_id"),
                    "supporting_sentence_index": c.get("supporting_sentence_index"),
                    "extracted_sentence": c.get("supporting_quote", ""),
                })

        reasons_str = ", ".join(reasons_seen) if reasons_seen else "-"
        print(f"{sc_id:<12} | {'1.1.0':<8} | {status:<8} | {attempts:<4} | {num_claims:<6} | {supp_count:<5} | {unsupp_count:<6} | {reasons_str}")
        sys.stdout.flush()

        results.append({
            "scenario_id": sc_id,
            "splitter_version": "1.1.0",
            "status": status,
            "attempts": attempts,
            "error_details": err,
            "number_of_claims": num_claims,
            "claims": scenario_claims_data,
        })

    print("-" * 95)
    print("\n=== AGGREGATE COUNTS (v1.2.0) ===")
    print(f"Total Scenarios Evaluated: {total_scenarios}")
    print(f"Scenarios reaching SUCCESS: {success_count}")
    print(f"Scenarios reaching FAILED:  {failed_count}")
    print(f"Claims SUPPORTED / Total Claims: {supported_claims_count} / {total_claims_count}")

    with open(v1_2_0_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults successfully written to: {v1_2_0_file}")

    # Comparison with v1.1.0
    if os.path.exists(v1_1_0_file):
        with open(v1_1_0_file, "r", encoding="utf-8") as f:
            v1_1_0_data = json.load(f)
        v1_1_0_map = {item["scenario_id"]: item for item in v1_1_0_data}

        print("\n=== COMPARISON: v1.1.0 vs v1.2.0 ===")
        claim_count_changed = []
        supp_changed = []

        for item in results:
            sid = item["scenario_id"]
            if sid in v1_1_0_map:
                old_item = v1_1_0_map[sid]
                old_claims = old_item.get("number_of_claims", len(old_item.get("claims", [])))
                new_claims = item.get("number_of_claims", len(item.get("claims", [])))
                if old_claims != new_claims:
                    claim_count_changed.append((sid, old_claims, new_claims))

                old_supp = sum(1 for c in old_item.get("claims", []) if c.get("evidence_status") == "SUPPORTED")
                new_supp = sum(1 for c in item.get("claims", []) if c.get("evidence_status") == "SUPPORTED")
                if old_supp != new_supp:
                    supp_changed.append((sid, old_supp, new_supp))

        print(f"Scenarios with changed total claim counts: {len(claim_count_changed)}")
        for sid, old_c, new_c in claim_count_changed:
            print(f"  {sid}: {old_c} -> {new_c} claims")

        print(f"Scenarios with changed SUPPORTED counts: {len(supp_changed)}")
        for sid, old_c, new_c in supp_changed:
            print(f"  {sid}: {old_c} -> {new_c} supported claims")
    else:
        print("\nPrior v1.1.0 results file not found for comparison.")

    # Relevance Sample Generation (Human Review Set)
    # Sort by claim_id first for deterministic repeatability
    all_supported_claims_for_sample.sort(key=lambda x: (x["scenario_id"], x["claim_id"]))
    rng = random.Random(20261019)
    sample_size = min(5, len(all_supported_claims_for_sample))
    sampled_claims = rng.sample(all_supported_claims_for_sample, sample_size)

    fieldnames = [
        "scenario_id",
        "claim_id",
        "claim_text",
        "supporting_passage_id",
        "supporting_sentence_index",
        "extracted_sentence",
        "relevance_label",
        "reviewer_note",
    ]

    with open(relevance_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in sampled_claims:
            writer.writerow({
                "scenario_id": c["scenario_id"],
                "claim_id": c["claim_id"],
                "claim_text": c["claim_text"],
                "supporting_passage_id": c["supporting_passage_id"],
                "supporting_sentence_index": c["supporting_sentence_index"],
                "extracted_sentence": c["extracted_sentence"],
                "relevance_label": "",
                "reviewer_note": "",
            })

    print(f"\nRelevance sample written to: {relevance_file}")
    print("\n--- relevance_review_sample_v1_2_0.csv ---")
    with open(relevance_file, "r", encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    main()

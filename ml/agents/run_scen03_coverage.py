from __future__ import annotations

import csv
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from ml.agents.agent_swarm import VerdionAgentSwarm
from ml.agents.validator import split_passage_into_sentences, verify_claim_quote


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scenarios_path = os.path.join(base_dir, "benchmark", "scenarios.json")
    passages_path = os.path.join(base_dir, "corpus", "passages.json")
    results_dir = os.path.join(base_dir, "agents", "results")
    os.makedirs(results_dir, exist_ok=True)
    out_json = os.path.join(results_dir, "roles_scen03.json")
    out_csv = os.path.join(results_dir, "reconciliation_scen03.csv")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    scen_03 = next(s for s in scenarios if (s.get("scenario_id") or s.get("id")) == "scen_03")

    with open(passages_path, "r", encoding="utf-8") as f:
        passages = json.load(f)
    passage_lookup = {p["passage_id"]: p for p in passages}
    passage_sentences = {
        p["passage_id"]: split_passage_into_sentences(p.get("content", ""), version="1.1.0")
        for p in passages
    }

    swarm = VerdionAgentSwarm()

    print(f"Executing full coverage pipeline for scenario: {scen_03.get('scenario_id') or scen_03.get('id')} - {scen_03.get('title')}")
    print("Running in order: Researcher -> Interpreter -> Adversarial -> Forecaster -> Coordinator -> Evidence Verifier")
    sys.stdout.flush()

    # 1. Researcher
    print("\n[1/6] Running Legal Researcher...")
    sys.stdout.flush()
    res_03 = swarm.run_legal_researcher(scen_03)

    # 2. Interpreter
    print("[2/6] Running Legal Interpreter...")
    sys.stdout.flush()
    int_03 = swarm.run_legal_interpreter(scen_03, res_03)

    # 3. Adversarial Researcher
    print("[3/6] Running Adversarial Researcher...")
    sys.stdout.flush()
    adv_03 = swarm.run_adversarial_researcher(scen_03, int_03)

    # 4. Quantitative Forecaster
    print("[4/6] Running Quantitative Forecaster...")
    sys.stdout.flush()
    fc_03 = swarm.run_quantitative_forecaster(scen_03, upstream_outputs=[res_03, int_03, adv_03])

    # 5. Coordinator
    print("[5/6] Running Coordinator...")
    sys.stdout.flush()
    coord_03 = swarm.run_coordinator(scen_03, [res_03, int_03, adv_03, fc_03])

    # 6. Evidence Verifier (code over all collected claims)
    print("[6/6] Running Evidence Verifier...")
    sys.stdout.flush()
    ver_03 = swarm.run_evidence_verifier(scen_03, [res_03, int_03, adv_03, fc_03])

    role_outputs = {
        "LEGAL_RESEARCHER": res_03,
        "LEGAL_INTERPRETER": int_03,
        "ADVERSARIAL_RESEARCHER": adv_03,
        "QUANTITATIVE_FORECASTER": fc_03,
        "COORDINATOR": coord_03,
        "EVIDENCE_VERIFIER": ver_03,
    }

    # Collect per-role summary metrics
    role_summaries = []
    for role_name, out in role_outputs.items():
        metrics = out.get("execution_metrics", {})
        role_summaries.append({
            "role": role_name,
            "status": out.get("status", "UNKNOWN"),
            "attempts": metrics.get("attempts", 1),
            "prompt_tokens": metrics.get("prompt_tokens", 0),
            "completion_tokens": metrics.get("completion_tokens", 0),
            "total_tokens": metrics.get("token_usage", 0),
            "elapsed_ms": metrics.get("elapsed_ms", 0.0),
        })

    # Save roles_scen03.json
    full_output_record = {
        "scenario_id": "scen_03",
        "scenario_title": scen_03.get("title"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role_summaries": role_summaries,
        "roles": role_outputs,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(full_output_record, f, indent=2)
    print(f"\nSaved roles output to: {out_json}")

    # Build reconciliation table for scen_03
    claims_by_role = [
        ("LEGAL_RESEARCHER", res_03.get("claims", [])),
        ("LEGAL_INTERPRETER", int_03.get("claims", [])),
        ("ADVERSARIAL_RESEARCHER", adv_03.get("claims", [])),
        ("EVIDENCE_VERIFIER", ver_03.get("claims", [])),
        ("QUANTITATIVE_FORECASTER", fc_03.get("claims", [])),
        ("COORDINATOR", coord_03.get("claims", [])),
    ]

    reconciliation_rows = []
    mismatch_rows = []

    for role_name, claims in claims_by_role:
        for idx, c in enumerate(claims, 1):
            c_id = str(c.get("id") or c.get("claim_id") or f"{role_name.lower()}_{idx}")
            c_type = str(c.get("claim_type") or "-")
            role_reported_status = str(c.get("evidence_status") or "-")
            claim_text = str(c.get("claim_text") or "-")
            sup_id = c.get("supporting_passage_id")
            sent_idx = c.get("supporting_sentence_index")
            ev_refs = c.get("evidence_refs", [sup_id] if sup_id else [])

            verbatim_sentence = "-"
            if sup_id and sup_id in passage_sentences and sent_idx is not None and isinstance(sent_idx, int) and not isinstance(sent_idx, bool):
                sents = passage_sentences[sup_id]
                if 0 <= sent_idx < len(sents):
                    verbatim_sentence = sents[sent_idx]

            # Verifier re-evaluation
            if sup_id and verbatim_sentence != "-":
                v_status, v_notes = verify_claim_quote(
                    evidence_refs=ev_refs if sup_id in ev_refs else ev_refs + [sup_id],
                    supporting_quote=verbatim_sentence,
                    supporting_passage_id=sup_id,
                    passage_lookup=passage_lookup,
                    supporting_sentence_index=sent_idx,
                )
            else:
                v_status = "UNSUPPORTED"
                if not sup_id:
                    v_notes = "reason=MISSING_PASSAGE_ID"
                else:
                    v_notes = "reason=INDEX_OUT_OF_RANGE"

            v_reason_code = "-"
            if v_status != "SUPPORTED" and v_notes:
                if "reason=" in v_notes:
                    v_reason_code = v_notes.split("reason=")[-1].split(",")[0].strip()
                else:
                    v_reason_code = v_notes

            row = {
                "scenario_id": "scen_03",
                "role": role_name,
                "claim_id": c_id,
                "claim_type": c_type,
                "role_reported_status": role_reported_status,
                "verifier_status": v_status,
                "verifier_reason_code": v_reason_code,
                "supporting_passage_id": sup_id or "-",
                "supporting_sentence_index": str(sent_idx) if sent_idx is not None else "-",
                "extracted_sentence": verbatim_sentence,
                "claim_text": claim_text,
            }
            reconciliation_rows.append(row)

            # Check for Mismatch: role reported SUPPORTED but verifier produced != SUPPORTED
            if role_reported_status == "SUPPORTED" and v_status != "SUPPORTED":
                if "Rule check" in claim_text:
                    cause = "Rule-engine result (deterministic code evaluation without passage citation)"
                elif role_name == "QUANTITATIVE_FORECASTER":
                    cause = "Interpretation (statistical probability estimate without passage citation)"
                elif not sup_id:
                    cause = "Interpretation (assertion lacks supporting_passage_id)"
                else:
                    cause = f"Citation the verifier did not check or failed verification ({v_reason_code})"

                mismatch_rows.append({
                    "scenario_id": "scen_03",
                    "role": role_name,
                    "claim_id": c_id,
                    "claim_text": claim_text,
                    "cause": cause,
                    "reason_code": v_reason_code,
                })

    # Write reconciliation_scen03.csv
    fieldnames = [
        "scenario_id",
        "role",
        "claim_id",
        "claim_type",
        "role_reported_status",
        "verifier_status",
        "verifier_reason_code",
        "supporting_passage_id",
        "supporting_sentence_index",
        "extracted_sentence",
        "claim_text",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reconciliation_rows)

    print(f"Saved reconciliation table to: {out_csv}")

    # Print Per-Role Summary
    print("\n" + "=" * 90)
    print("PER-ROLE EXECUTION SUMMARY: scen_03")
    print("=" * 90)
    print(f"{'Role':<26} | {'Status':<10} | {'Attempts':<8} | {'Prompt Tok':<10} | {'Compl Tok':<10} | {'Elapsed ms'}")
    print("-" * 90)
    for s in role_summaries:
        print(f"{s['role']:<26} | {s['status']:<10} | {s['attempts']:<8} | {s['prompt_tokens']:<10} | {s['completion_tokens']:<10} | {s['elapsed_ms']:<10.2f}")
    print("-" * 90)

    # Print Reconciliation Table
    print("\n" + "=" * 115)
    print("RECONCILIATION TABLE: scen_03")
    print("=" * 115)
    print(f"{'Role':<24} | {'Claim ID':<16} | {'Role Status':<12} | {'Verif Status':<12} | {'Reason Code':<18} | {'Passage ID'}")
    print("-" * 115)
    for r in reconciliation_rows:
        print(f"{r['role']:<24} | {r['claim_id']:<16} | {r['role_reported_status']:<12} | {r['verifier_status']:<12} | {r['verifier_reason_code']:<18} | {r['supporting_passage_id']}")
    print("-" * 115)

    # Print Mismatches
    print("\n" + "=" * 115)
    print(f"MISMATCH REPORT (scen_03): Total Mismatches = {len(mismatch_rows)}")
    print("=" * 115)
    if mismatch_rows:
        for m in mismatch_rows:
            print(f"- [{m['role']} | {m['claim_id']}]")
            print(f"  Claim: {m['claim_text']}")
            print(f"  Cause: {m['cause']}")
            print(f"  Verifier Reason Code: {m['reason_code']}\n")
    else:
        print("No mismatches found.")

    # Coordinator Audit (scen_03)
    print("=" * 115)
    print("COORDINATOR RANKED QUESTIONS AUDIT (scen_03)")
    print("=" * 115)
    ranked_questions = coord_03.get("ranked_questions", [])
    all_upstream_texts = []
    for out in [res_03, int_03, adv_03, fc_03]:
        for c in out.get("claims", []):
            all_upstream_texts.append(str(c.get("claim_text", "")).lower())
        u = out.get("uncertainty", {})
        if u.get("rationale"):
            all_upstream_texts.append(str(u.get("rationale", "")).lower())
        for ca in out.get("counterarguments", []):
            all_upstream_texts.append(str(ca).lower())
        fc = out.get("forecast", {})
        if fc.get("event_definition"):
            all_upstream_texts.append(str(fc.get("event_definition")).lower())

    flagged_questions = []
    for q in ranked_questions:
        qid = q.get("id")
        q_text = q.get("question")
        imp = q.get("impact", 0.0)
        unc = q.get("uncertainty", 0.0)
        fea = q.get("feasibility", 0.0)
        arithmetic = round(imp * unc * fea, 3)
        stored_p = q.get("priority")
        src_role = q.get("source_role") or "UPSTREAM"

        q_words = [w for w in q_text.lower().replace("how to address counter-argument:", "").replace("resolve contradiction:", "").split() if len(w) > 4]
        appears_upstream = any(
            any(w in text for w in q_words[:3]) for text in all_upstream_texts
        ) if q_words else False

        source_claims = []
        for out in [res_03, int_03, adv_03, fc_03]:
            for c in out.get("claims", []):
                c_id = c.get("id") or c.get("claim_id")
                c_txt = str(c.get("claim_text", "")).lower()
                if any(w in c_txt for w in q_words[:3]) if q_words else False:
                    source_claims.append(f"{c_id} ({out.get('role')})")

        source_claims_str = ", ".join(source_claims) if source_claims else "Uncertainty Rationale / Counterargument"

        flagged = not appears_upstream
        if flagged:
            flagged_questions.append(q)

        flag_str = " [FLAGGED: INPUTS NOT IN UPSTREAM]" if flagged else ""
        print(f"Question ID:  {qid}{flag_str}")
        print(f"Question:     {q_text}")
        print(f"Source Role:  {src_role}")
        print(f"Source Claims:{source_claims_str}")
        print(f"Factors:      Impact={imp}, Uncertainty={unc}, Feasibility={fea}")
        print(f"Arithmetic:   {imp} * {unc} * {fea} = {arithmetic} (stored priority: {stored_p})")
        print("-" * 60)

    print(f"\nTotal Coordinator Questions Flagged: {len(flagged_questions)}")


if __name__ == "__main__":
    main()

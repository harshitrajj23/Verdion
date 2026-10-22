from __future__ import annotations

import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

from ml.agents.agent_swarm import VerdionAgentSwarm
from ml.agents.validator import split_passage_into_sentences, verify_claim_quote


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scenarios_path = os.path.join(base_dir, "benchmark", "scenarios.json")
    passages_path = os.path.join(base_dir, "corpus", "passages.json")
    researcher_results_path = os.path.join(base_dir, "agents", "results", "researcher_train_run_v1_2_0.json")
    results_dir = os.path.join(base_dir, "agents", "results")
    os.makedirs(results_dir, exist_ok=True)
    out_csv = os.path.join(results_dir, "reconciliation_scen01_scen02.csv")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    scen_map = {s.get("scenario_id") or s.get("id"): s for s in scenarios}

    with open(passages_path, "r", encoding="utf-8") as f:
        passages = json.load(f)
    passage_lookup = {p["passage_id"]: p for p in passages}
    passage_sentences = {
        p["passage_id"]: split_passage_into_sentences(p.get("content", ""), version="1.1.0")
        for p in passages
    }

    with open(researcher_results_path, "r", encoding="utf-8") as f:
        researcher_runs = json.load(f)
    res_map = {r["scenario_id"]: r for r in researcher_runs}

    swarm = VerdionAgentSwarm()

    print("Executing roles for scen_01 and scen_02...")
    sys.stdout.flush()

    # 1. scen_01 outputs
    scen_01 = scen_map["scen_01"]
    res_01 = res_map["scen_01"]
    int_01 = swarm.run_legal_interpreter(scen_01, res_01)
    adv_01 = swarm.run_adversarial_researcher(scen_01, int_01)
    ver_01 = swarm.run_evidence_verifier(scen_01, [res_01, int_01, adv_01])
    fc_01 = swarm.run_quantitative_forecaster(scen_01, upstream_outputs=[res_01, int_01, adv_01])
    coord_01 = swarm.run_coordinator(scen_01, [res_01, int_01, adv_01, fc_01])

    # 2. scen_02 outputs (Researcher and Interpreter per prompt spec)
    scen_02 = scen_map["scen_02"]
    res_02 = res_map["scen_02"]
    int_02 = swarm.run_legal_interpreter(scen_02, res_02)

    all_role_outputs = [
        ("scen_01", "LEGAL_RESEARCHER", res_01.get("claims", [])),
        ("scen_01", "LEGAL_INTERPRETER", int_01.get("claims", [])),
        ("scen_01", "ADVERSARIAL_RESEARCHER", adv_01.get("claims", [])),
        ("scen_01", "EVIDENCE_VERIFIER", ver_01.get("claims", [])),
        ("scen_01", "QUANTITATIVE_FORECASTER", fc_01.get("claims", [])),
        ("scen_01", "COORDINATOR", coord_01.get("claims", [])),
        ("scen_02", "LEGAL_RESEARCHER", res_02.get("claims", [])),
        ("scen_02", "LEGAL_INTERPRETER", int_02.get("claims", [])),
    ]

    reconciliation_rows = []
    mismatch_rows = []

    for sc_id, role_name, claims in all_role_outputs:
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
                "scenario_id": sc_id,
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
                # Categorize cause
                if "Rule check" in claim_text:
                    cause = "Rule-engine result (deterministic code evaluation without passage citation)"
                elif role_name == "QUANTITATIVE_FORECASTER":
                    cause = "Interpretation (statistical probability estimate without passage citation)"
                elif not sup_id:
                    cause = "Interpretation (assertion lacks supporting_passage_id)"
                else:
                    cause = f"Citation the verifier did not check or failed verification ({v_reason_code})"

                mismatch_rows.append({
                    "scenario_id": sc_id,
                    "role": role_name,
                    "claim_id": c_id,
                    "claim_text": claim_text,
                    "cause": cause,
                    "reason_code": v_reason_code,
                })

    # Write CSV
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

    print(f"\nReconciliation table successfully written to: {out_csv}")
    print("\n" + "=" * 115)
    print("RECONCILIATION TABLE: scen_01 & scen_02")
    print("=" * 115)
    print(f"{'Scenario':<8} | {'Role':<22} | {'Claim ID':<18} | {'Role Status':<12} | {'Verif Status':<12} | {'Reason Code':<16} | {'Passage ID'}")
    print("-" * 115)
    for r in reconciliation_rows:
        print(f"{r['scenario_id']:<8} | {r['role']:<22} | {r['claim_id']:<18} | {r['role_reported_status']:<12} | {r['verifier_status']:<12} | {r['verifier_reason_code']:<16} | {r['supporting_passage_id']}")
    print("-" * 115)

    # Print Mismatches
    print("\n" + "=" * 115)
    print(f"MISMATCH REPORT: Total Mismatches = {len(mismatch_rows)}")
    print("=" * 115)
    if mismatch_rows:
        for m in mismatch_rows:
            print(f"- [{m['scenario_id']} | {m['role']} | {m['claim_id']}]")
            print(f"  Claim: {m['claim_text']}")
            print(f"  Cause: {m['cause']}")
            print(f"  Verifier Reason Code: {m['reason_code']}\n")
    else:
        print("No mismatches found.")

    # Coordinator Audit (scen_01)
    print("=" * 115)
    print("COORDINATOR RANKED QUESTIONS AUDIT (scen_01)")
    print("=" * 115)
    ranked_questions = coord_01.get("ranked_questions", [])
    all_upstream_texts = []
    for out in [res_01, int_01, adv_01, fc_01]:
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

        # Check if question text or key substrings appear in any upstream output
        q_words = [w for w in q_text.lower().replace("how to address counter-argument:", "").replace("resolve contradiction:", "").split() if len(w) > 4]
        appears_upstream = any(
            any(w in text for w in q_words[:3]) for text in all_upstream_texts
        ) if q_words else False

        source_claims = []
        for out in [res_01, int_01, adv_01, fc_01]:
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

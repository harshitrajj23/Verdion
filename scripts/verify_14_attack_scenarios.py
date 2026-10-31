import json
import copy
from backend.app.core.canonical import compute_canonical_sha256
from backend.app.core.crypto import compute_forecast_commitment
from backend.app.services.audit_verifier import IndependentAuditVerifier

def create_valid_base_package():
    # Construct an authentic standalone package with real passage, decision record, forecast, audit chain, and Merkle root
    case_id = "case_audit_base_001"
    
    # 1. Evidence source and passage
    doc_id = "eurlex_32016R0679"
    passage_id = "passage_gdpr_art5_1b"
    text = "Personal data shall be collected for specified, explicit and legitimate purposes..."
    p_digest = "0x7a8341b5592cdcb08e3eb3c042d3adfa89db3163aa87ef227fa5be0a0f91a0eb"
    doc_digest = "0x4f128bc94a97475be6e2a21e649ceee7424adcfc7161b9a978f44ffaa60bba3b"
    
    # 2. Forecast commit-reveal
    market_id = "market_gdpr_01"
    agent_id = "ag_forecaster_01"
    wallet_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    prob = 0.75
    nonce = "0x" + "aa" * 32
    chain_id = 11155111
    
    commit_hash = compute_forecast_commitment(
        chain_id=chain_id,
        market_id=market_id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=p_digest,
        nonce=nonce,
        wallet_address=wallet_address
    )
    
    # 3. Audit events chain
    ev1_dig = "0x" + "11" * 32
    ev2_dig = "0x" + "22" * 32
    ev3_dig = "0x" + "33" * 32
    genesis = "0x" + "0" * 64
    
    audit_events = [
        {"sequence_number": 1, "event_type": "CASE_CREATED", "event_digest": ev1_dig, "previous_event_digest": genesis},
        {"sequence_number": 2, "event_type": "EVIDENCE_BOUND", "event_digest": ev2_dig, "previous_event_digest": ev1_dig},
        {"sequence_number": 3, "event_type": "DECISION_SEALED", "event_digest": ev3_dig, "previous_event_digest": ev2_dig}
    ]
    
    computed_merkle_root = IndependentAuditVerifier.compute_local_merkle_root([ev1_dig, ev2_dig, ev3_dig])
    
    # 4. Decision record dictionary
    rec_dict = {
        "schema_version": "1.0.0",
        "decision_id": f"dec_{case_id}_v1",
        "case_id": case_id,
        "case_version": 1,
        "case_title": "GDPR Compliance Evaluation",
        "case_question": "Does training on voice data violate purpose limitation?",
        "jurisdiction": "EU",
        "assessment_date": "2026-10-28",
        "facts": {"data_categories": ["voice"], "processing_purpose": "training"},
        "provenance": "OPERATIONAL",
        "analysis_configuration": {"orchestration_version": "v1.0", "software_version": "1.0.0"},
        "analysis_timestamp": "2026-10-28T05:00:00Z",
        "evidence_sources": [
            {"document_id": doc_id, "title": "GDPR", "content_digest": doc_digest, "provenance": "OPERATIONAL"}
        ],
        "evidence_passages": [
            {
                "passage_id": passage_id,
                "document_id": doc_id,
                "passage_reference": "Art 5(1)(b)",
                "content_reference": "Purpose limitation",
                "text_excerpt": text,
                "passage_digest": p_digest,
                "char_start": 0,
                "char_end": len(text),
                "source_text": text,
                "provenance": "OPERATIONAL"
            }
        ],
        "claims": [
            {"claim_id": "c1", "claim_text": "Risk of incompatibility", "cited_passage_ids": [passage_id]}
        ],
        "forecast_markets": [
            {
                "market_id": market_id,
                "chain_id": chain_id,
                "commitments": [
                    {
                        "forecast_id": "fc_01",
                        "agent_id": agent_id,
                        "wallet_address": wallet_address,
                        "commitment_hash": commit_hash,
                        "reveal_status": "REVEALED",
                        "revealed_probability": prob,
                        "revealed_evidence_digest": p_digest,
                        "revealed_nonce": nonce
                    }
                ]
            }
        ],
        "settlements": [],
        "audit_events": audit_events,
        "record_digest": None
    }
    
    # Compute canonical digest
    rec_digest = compute_canonical_sha256(rec_dict)
    rec_dict["record_digest"] = rec_digest
    
    package = {
        "manifest": {
            "spec_version": "VERIDION_AUDIT_SPEC_V1",
            "package_id": f"pkg_{case_id}",
            "case_id": case_id,
            "export_timestamp": "2026-10-28T05:30:00Z",
            "generator": "VERIDION_CORE_DECISION_ENGINE",
            "provenance": "OPERATIONAL",
            "merkle_checkpoint_root": computed_merkle_root
        },
        "decision_record": rec_dict,
        "verification_instructions": "Verify canonically via IndependentAuditVerifier"
    }
    return package, computed_merkle_root

def run_14_attack_scenarios():
    base_pkg, merkle_root = create_valid_base_package()
    results = []

    # 1. An intact valid package
    pkg1 = copy.deepcopy(base_pkg)
    rep1 = IndependentAuditVerifier.verify_audit_package(pkg1, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 1,
        "name": "Intact valid package (externally anchored)",
        "expected_status": "EXTERNALLY_ANCHORED_VERIFIED",
        "actual_status": rep1["overall_status"],
        "is_valid": rep1["is_valid"],
        "is_anchored": rep1["is_anchored"],
        "pass": rep1["overall_status"] == "EXTERNALLY_ANCHORED_VERIFIED" and rep1["is_valid"] is True
    })

    # 2. A modified decision-record field
    pkg2 = copy.deepcopy(base_pkg)
    pkg2["decision_record"]["case_title"] = "TAMPERED CASE TITLE"
    rep2 = IndependentAuditVerifier.verify_audit_package(pkg2, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 2,
        "name": "Modified decision-record field (title changed)",
        "expected_status": "FAILED",
        "actual_status": rep2["overall_status"],
        "is_valid": rep2["is_valid"],
        "failed_check": "decision_record_digest",
        "pass": rep2["overall_status"] == "FAILED" and rep2["checks"]["decision_record_digest"]["status"] == "FAIL"
    })

    # 3. A modified passage body
    pkg3 = copy.deepcopy(base_pkg)
    pkg3["decision_record"]["evidence_passages"][0]["text_excerpt"] = "TAMPERED EXCERPT"
    rep3 = IndependentAuditVerifier.verify_audit_package(pkg3, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 3,
        "name": "Modified passage body (excerpt altered)",
        "expected_status": "FAILED",
        "actual_status": rep3["overall_status"],
        "is_valid": rep3["is_valid"],
        "failed_check": "decision_record_digest / passage_offsets",
        "pass": rep3["overall_status"] == "FAILED"
    })

    # 4. An incorrect evidence digest
    pkg4 = copy.deepcopy(base_pkg)
    pkg4["decision_record"]["evidence_passages"][0]["passage_digest"] = "0x" + "ee" * 32
    rep4 = IndependentAuditVerifier.verify_audit_package(pkg4, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 4,
        "name": "Incorrect evidence digest",
        "expected_status": "FAILED",
        "actual_status": rep4["overall_status"],
        "is_valid": rep4["is_valid"],
        "failed_check": "decision_record_digest",
        "pass": rep4["overall_status"] == "FAILED"
    })

    # 5. A reordered audit-event sequence
    pkg5 = copy.deepcopy(base_pkg)
    events = pkg5["decision_record"]["audit_events"]
    events[0], events[1] = events[1], events[0]
    rep5 = IndependentAuditVerifier.verify_audit_package(pkg5, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 5,
        "name": "Reordered audit-event sequence",
        "expected_status": "FAILED",
        "actual_status": rep5["overall_status"],
        "is_valid": rep5["is_valid"],
        "failed_check": "audit_event_chain_continuity",
        "pass": rep5["overall_status"] == "FAILED" and rep5["checks"]["audit_hash_chain"]["status"] == "FAIL"
    })

    # 6. A deleted audit event
    pkg6 = copy.deepcopy(base_pkg)
    del pkg6["decision_record"]["audit_events"][1]
    rep6 = IndependentAuditVerifier.verify_audit_package(pkg6, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 6,
        "name": "Deleted audit event (broken chain link)",
        "expected_status": "FAILED",
        "actual_status": rep6["overall_status"],
        "is_valid": rep6["is_valid"],
        "failed_check": "audit_event_chain_continuity",
        "pass": rep6["overall_status"] == "FAILED" and rep6["checks"]["audit_hash_chain"]["status"] == "FAIL"
    })

    # 7. A duplicate Merkle leaf
    pkg7 = copy.deepcopy(base_pkg)
    # duplicate leaf in audit events
    dup_event = copy.deepcopy(pkg7["decision_record"]["audit_events"][0])
    dup_event["sequence_number"] = 4
    pkg7["decision_record"]["audit_events"].append(dup_event)
    rep7 = IndependentAuditVerifier.verify_audit_package(pkg7, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 7,
        "name": "Duplicate Merkle leaf / sequence breach",
        "expected_status": "FAILED",
        "actual_status": rep7["overall_status"],
        "is_valid": rep7["is_valid"],
        "failed_check": "audit_event_chain_continuity",
        "pass": rep7["overall_status"] == "FAILED"
    })

    # 8. A modified Merkle root
    pkg8 = copy.deepcopy(base_pkg)
    pkg8["manifest"]["merkle_checkpoint_root"] = "0x" + "99" * 32
    rep8 = IndependentAuditVerifier.verify_audit_package(pkg8, trusted_checkpoint="0x" + "99" * 32)
    results.append({
        "scenario_num": 8,
        "name": "Modified Merkle root",
        "expected_status": "FAILED",
        "actual_status": rep8["overall_status"],
        "is_valid": rep8["is_valid"],
        "failed_check": "merkle_checkpoint_verification",
        "pass": rep8["overall_status"] == "FAILED" and rep8["checks"]["merkle_checkpoint_verification"]["status"] == "FAIL"
    })

    # 9. An absent trusted checkpoint
    pkg9 = copy.deepcopy(base_pkg)
    rep9 = IndependentAuditVerifier.verify_audit_package(pkg9, trusted_checkpoint=None)
    results.append({
        "scenario_num": 9,
        "name": "Absent trusted checkpoint (disclosed as unanchored)",
        "expected_status": "VERIFIED (unanchored)",
        "actual_status": rep9["overall_status"],
        "anchor_status": rep9["anchor_status"],
        "is_valid": rep9["is_valid"],
        "is_anchored": rep9["is_anchored"],
        "pass": rep9["is_anchored"] is False and rep9["anchor_status"] == "UNANCHORED_LOCAL_RECORD" and "UNANCHORED_LOCAL_RECORD" in rep9["checks"]["merkle_checkpoint_root"]["disclosure"]
    })

    # 10. A malformed commitment or reveal
    pkg10 = copy.deepcopy(base_pkg)
    # alter revealed probability from 0.75 to 0.70 without updating commitment
    pkg10["decision_record"]["forecast_markets"][0]["commitments"][0]["revealed_probability"] = 0.70
    rep10 = IndependentAuditVerifier.verify_audit_package(pkg10, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 10,
        "name": "Malformed commitment / reveal mismatch",
        "expected_status": "FAILED",
        "actual_status": rep10["overall_status"],
        "is_valid": rep10["is_valid"],
        "failed_check": "commit_reveal_cryptography",
        "pass": rep10["overall_status"] == "FAILED" and rep10["checks"]["commit_reveal_cryptography"]["status"] == "FAIL"
    })

    # 11. A mismatched chain ID or contract address
    pkg11 = copy.deepcopy(base_pkg)
    # Alter market chain_id from 11155111 to 1 (mainnet replay attempt)
    pkg11["decision_record"]["forecast_markets"][0]["chain_id"] = 1
    rep11 = IndependentAuditVerifier.verify_audit_package(pkg11, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 11,
        "name": "Mismatched chain ID (cross-chain replay attack)",
        "expected_status": "FAILED",
        "actual_status": rep11["overall_status"],
        "is_valid": rep11["is_valid"],
        "failed_check": "commit_reveal_cryptography",
        "pass": rep11["overall_status"] == "FAILED" and rep11["checks"]["commit_reveal_cryptography"]["status"] == "FAIL"
    })

    # 12. An incomplete package manifest
    pkg12 = copy.deepcopy(base_pkg)
    del pkg12["manifest"]["case_id"]
    rep12 = IndependentAuditVerifier.verify_audit_package(pkg12, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 12,
        "name": "Incomplete package manifest (missing case_id)",
        "expected_status": "FAILED",
        "actual_status": rep12["overall_status"],
        "is_valid": rep12["is_valid"],
        "failed_check": "manifest_specification",
        "pass": rep12["overall_status"] == "FAILED" and rep12["checks"]["manifest_specification"]["status"] == "FAIL"
    })

    # 13. A package with inconsistent provenance
    pkg13 = copy.deepcopy(base_pkg)
    # Manifest claims OPERATIONAL, but source is marked TEST
    pkg13["decision_record"]["evidence_sources"][0]["provenance"] = "TEST"
    rep13 = IndependentAuditVerifier.verify_audit_package(pkg13, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 13,
        "name": "Inconsistent provenance (TEST source in OPERATIONAL record)",
        "expected_status": "FAILED",
        "actual_status": rep13["overall_status"],
        "is_valid": rep13["is_valid"],
        "failed_check": "provenance_consistency",
        "pass": rep13["overall_status"] == "FAILED" and rep13["checks"]["provenance_consistency"]["status"] == "FAIL"
    })

    # 14. A package containing synthetic data mislabeled as operational
    pkg14 = copy.deepcopy(base_pkg)
    # Passage is marked SYNTHETIC_FIXTURE in OPERATIONAL record
    pkg14["decision_record"]["evidence_passages"][0]["provenance"] = "SYNTHETIC_FIXTURE"
    rep14 = IndependentAuditVerifier.verify_audit_package(pkg14, trusted_checkpoint=merkle_root)
    results.append({
        "scenario_num": 14,
        "name": "Synthetic data mislabeled as operational",
        "expected_status": "FAILED",
        "actual_status": rep14["overall_status"],
        "is_valid": rep14["is_valid"],
        "failed_check": "provenance_consistency",
        "pass": rep14["overall_status"] == "FAILED" and rep14["checks"]["provenance_consistency"]["status"] == "FAIL"
    })

    print(json.dumps(results, indent=2))
    all_passed = all(r["pass"] for r in results)
    print(f"\nTOTAL SCENARIOS TESTED: {len(results)}, ALL PASSED: {all_passed}")

if __name__ == "__main__":
    run_14_attack_scenarios()

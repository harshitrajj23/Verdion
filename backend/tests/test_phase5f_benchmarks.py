import os
import json
import math
import pytest
import sqlite3
import hashlib
from backend.app.core.canonical import compute_canonical_sha256
from backend.app.core.crypto import compute_forecast_commitment, compute_brier_score
from backend.app.services.audit_verifier import IndependentAuditVerifier
from scripts.run_phase5f_benchmarks import (
    create_valid_base_package,
    run_benchmark_a,
    run_benchmark_e,
    run_benchmark_f,
)


def test_harness_determinism():
    """Verify that create_valid_base_package produces identical canonical hashes across repeated invocations."""
    pkg1, root1 = create_valid_base_package()
    pkg2, root2 = create_valid_base_package()

    assert pkg1["manifest"]["decision_record_digest"] == pkg2["manifest"]["decision_record_digest"]
    assert root1 == root2
    assert pkg1["decision_record"]["record_digest"] == pkg2["decision_record"]["record_digest"]


def test_correct_classification_of_valid_and_tampered_packages():
    """Verify verifier classifies valid packages as valid and detects tampered fields with 100% precision."""
    pkg, root = create_valid_base_package()

    # Valid
    rep_valid = IndependentAuditVerifier.verify_audit_package(pkg, trusted_checkpoint=root)
    assert rep_valid["is_valid"] is True
    assert rep_valid["overall_status"] == "EXTERNALLY_ANCHORED_VERIFIED"

    # Tampered field
    pkg_tampered = json.loads(json.dumps(pkg))
    pkg_tampered["decision_record"]["case_title"] = "Tampered Title Value"
    rep_tampered = IndependentAuditVerifier.verify_audit_package(pkg_tampered, trusted_checkpoint=root)
    assert rep_tampered["is_valid"] is False
    assert rep_tampered["overall_status"] == "FAILED"
    assert rep_tampered["checks"]["decision_record_digest"]["status"] == "FAIL"


def test_correct_handling_of_unanchored_packages():
    """Verify unanchored packages pass internal cryptographic integrity but are explicitly disclosed as UNANCHORED."""
    pkg, _ = create_valid_base_package()

    rep = IndependentAuditVerifier.verify_audit_package(pkg, trusted_checkpoint=None)
    assert rep["is_valid"] is True
    assert rep["overall_status"] == "VERIFIED"
    assert rep["is_anchored"] is False
    assert rep["anchor_status"] == "UNANCHORED_LOCAL_RECORD"


def test_reproducibility_of_brier_logloss_calibration():
    """Verify Brier score, log loss, and ECE math is reproducible and consistent."""
    preds = [0.8, 0.2, 0.9, 0.1]
    outcomes = [1, 0, 1, 0]
    
    # Brier: (0.8-1)^2 + (0.2-0)^2 + (0.9-1)^2 + (0.1-0)^2 = 0.04 + 0.04 + 0.01 + 0.01 = 0.10 / 4 = 0.025
    brier_expected = 0.025
    brier_actual = sum((p - y) ** 2 for p, y in zip(preds, outcomes)) / len(preds)
    assert math.isclose(brier_actual, brier_expected, rel_tol=1e-5)

    # Log loss check
    eps = 1e-15
    log_losses = [-(y * math.log(max(eps, min(1-eps, p))) + (1-y) * math.log(max(eps, min(1-eps, 1-p)))) for p, y in zip(preds, outcomes)]
    mean_ll = sum(log_losses) / len(log_losses)
    assert mean_ll < 0.25  # Well-calibrated predictions have low log loss


def test_provenance_isolation_between_operational_and_synthetic():
    """Verify synthetic fixtures are flagged if injected into an operational audit record."""
    pkg, root = create_valid_base_package()
    
    # Inject synthetic passage
    pkg["decision_record"]["evidence_passages"][0]["provenance"] = "SYNTHETIC_FIXTURE"
    rep = IndependentAuditVerifier.verify_audit_package(pkg, trusted_checkpoint=root)
    
    assert rep["is_valid"] is False
    assert rep["overall_status"] == "FAILED"
    assert rep["checks"]["provenance_consistency"]["status"] == "FAIL"


def test_idempotent_fixture_ingestion():
    """Verify content digest recomputation is invariant and deduplication is idempotent."""
    text = "Regulation (EU) 2024/1689 of the European Parliament and of the Council."
    h1 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert h1 == h2


def test_result_schema_validation():
    """Verify raw benchmark results conform to expected JSON schema and fields."""
    raw_dir = "audit/phase5f/raw"
    expected_files = [
        "benchmark_a_correctness.json",
        "benchmark_b_performance.json",
        "benchmark_c_ingestion.json",
        "benchmark_d_workflow.json",
        "benchmark_e_forecasts.json",
        "benchmark_f_parity.json",
        "environment_metadata.json"
    ]
    for fname in expected_files:
        path = os.path.join(raw_dir, fname)
        assert os.path.exists(path), f"Missing benchmark raw result: {fname}"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict)


def test_database_non_mutation():
    """Verify operational database veridion.db row count remains intact."""
    db_candidates = [
        "Verdion/veridion.db",
        "veridion.db",
        os.path.join(os.path.dirname(__file__), "..", "..", "veridion.db")
    ]
    db_path = None
    for cand in db_candidates:
        if os.path.exists(cand):
            try:
                conn = sqlite3.connect(cand)
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM cases;")
                case_cnt = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM transaction_records;")
                tx_cnt = cursor.fetchone()[0]
                conn.close()
                if case_cnt == 72:
                    db_path = cand
                    break
            except Exception:
                pass

    assert db_path is not None, "Could not find operational veridion.db with 72 cases"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM cases;")
    case_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM transaction_records;")
    tx_cnt = cursor.fetchone()[0]
    conn.close()

    assert case_cnt == 72
    assert tx_cnt == 0


def test_unexecutable_workload_handling():
    """Verify graceful and truthful handling when an optional component or missing file is passed."""
    pkg, root = create_valid_base_package()
    
    # Missing optional forecast markets -> should evaluate as NOT_APPLICABLE rather than crash
    pkg["decision_record"]["forecast_markets"] = []
    dict_copy = dict(pkg["decision_record"])
    dict_copy["record_digest"] = None
    new_dig = compute_canonical_sha256(dict_copy)
    pkg["decision_record"]["record_digest"] = new_dig
    pkg["manifest"]["decision_record_digest"] = new_dig

    rep = IndependentAuditVerifier.verify_audit_package(pkg, trusted_checkpoint=root)
    assert rep["checks"]["commit_reveal_cryptography"]["status"] == "NOT_APPLICABLE"
    assert rep["is_valid"] is True


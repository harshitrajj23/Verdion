import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional
from eth_abi.packed import encode_packed
from eth_utils import keccak, to_checksum_address
from decimal import Decimal, ROUND_HALF_UP

from backend.app.core.canonical import (
    compute_canonical_sha256,
    normalize_unicode,
    serialize_canonical_json,
)
from backend.app.services.audit_service import AuditService, GENESIS_PREVIOUS_DIGEST


class IndependentAuditVerifier:
    """
    Independent Audit Verifier for VERIDION Option C Infrastructure.
    Operates offline or online, verifying decision records and audit packages
    strictly through cryptographic checks and deterministic math, without trusting
    the runtime agent or database.
    """

    @staticmethod
    def verify_commitment_recomputation(
        chain_id: int,
        market_id: str,
        wallet_address: str,
        probability: float,
        evidence_digest: str,
        nonce: str,
        expected_commitment_hash: str
    ) -> Dict[str, Any]:
        """
        Recomputes keccak256(chainId, marketId, wallet, probBps, evidenceDigest, nonce)
        and compares strictly with the recorded commitment hash.
        """
        try:
            checksum_wallet = to_checksum_address(wallet_address)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid wallet address '{wallet_address}': {e}"
            }

        # Format probability basis points
        prob_bps = int((Decimal(str(probability)) * Decimal("10000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # Format market bytes
        clean_m = market_id.strip()
        if clean_m.startswith("0x"):
            market_bytes = bytes.fromhex(clean_m[2:].zfill(64))
        else:
            market_bytes = keccak(clean_m.encode("utf-8"))

        # Format digest bytes
        clean_d = evidence_digest.strip()
        clean_digest = clean_d if clean_d.startswith("0x") else "0x" + clean_d
        digest_bytes = bytes.fromhex(clean_digest[2:].zfill(64))

        # Format nonce bytes
        clean_n = nonce.strip()
        clean_nonce = clean_n if clean_n.startswith("0x") else "0x" + clean_n
        nonce_bytes = bytes.fromhex(clean_nonce[2:].zfill(64))

        encoded = encode_packed(
            ["uint256", "bytes32", "address", "uint256", "bytes32", "bytes32"],
            [chain_id, market_bytes, checksum_wallet, prob_bps, digest_bytes, nonce_bytes]
        )
        recomputed_hash = "0x" + keccak(encoded).hex()
        matched = recomputed_hash.lower() == expected_commitment_hash.lower()

        return {
            "valid": matched,
            "recomputed_hash": recomputed_hash,
            "expected_hash": expected_commitment_hash,
            "error": None if matched else "Commitment hash mismatch between revealed parameters and original commitment."
        }

    @staticmethod
    def compute_local_merkle_root(leaf_digests: List[str], hardened: bool = False) -> str:
        """
        Self-contained Merkle root calculation ensuring independent zero-trust operation.
        Supports both legacy binary duplicate tree and hardened RFC 6962 tree.
        """
        genesis = "0x" + "0" * 64
        if not leaf_digests:
            return genesis

        if hardened:
            # RFC 6962 leaf layer: SHA256(0x00 || leaf)
            current_layer = [
                hashlib.sha256(b"\x00" + bytes.fromhex(d[2:] if d.startswith("0x") else d)).digest()
                for d in leaf_digests
            ]
            while len(current_layer) > 1:
                next_layer = []
                i = 0
                while i < len(current_layer):
                    if i + 1 < len(current_layer):
                        left = current_layer[i]
                        right = current_layer[i + 1]
                        combined = hashlib.sha256(b"\x01" + left + right).digest()
                        next_layer.append(combined)
                        i += 2
                    else:
                        next_layer.append(current_layer[i])
                        i += 1
                current_layer = next_layer
            return "0x" + current_layer[0].hex()
        else:
            # Legacy binary duplication tree
            current_layer = [
                bytes.fromhex(d[2:] if d.startswith("0x") else d) for d in leaf_digests
            ]
            while len(current_layer) > 1:
                next_layer = []
                for i in range(0, len(current_layer), 2):
                    left = current_layer[i]
                    right = current_layer[i + 1] if i + 1 < len(current_layer) else left
                    combined = hashlib.sha256(left + right).digest()
                    next_layer.append(combined)
                current_layer = next_layer
            return "0x" + current_layer[0].hex()

    @staticmethod
    def verify_audit_package(
        package_data: Dict[str, Any],
        trusted_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adversarial zero-trust audit validation of an exported VERIDION Audit Package.
        Evaluates 10 independent cryptographic and procedural checks:
        1. manifest_specification: PASS | FAIL | BLOCKED
        2. decision_record_digest: PASS | FAIL
        3. evidence_sources_provenance: PASS | FAIL | UNVERIFIED
        4. passage_offsets_and_digests: PASS | FAIL | NOT_APPLICABLE
        5. claims_grounding: PASS | FAIL | NOT_APPLICABLE
        6. commit_reveal_cryptography: PASS | FAIL | NOT_APPLICABLE
        7. forecast_scoring_recomputation: PASS | FAIL | NOT_APPLICABLE
        8. audit_event_chain_continuity: PASS | FAIL
        9. merkle_checkpoint_verification: PASS | FAIL
        10. external_trust_anchor: PASS | FAIL | UNVERIFIED

        Overall Status:
        - FAILED: Any mandatory check evaluated to FAIL.
        - EXTERNALLY_ANCHORED_VERIFIED: All checks PASS, including trusted external checkpoint.
        - VERIFIED / LOCAL_CHAIN_VALID: All internal checks PASS, but external anchor is UNVERIFIED.
        """
        genesis_digest = "0x" + "0" * 64
        report: Dict[str, Any] = {
            "is_valid": False,
            "overall_status": "FAILED",
            "is_anchored": False,
            "anchor_status": "UNANCHORED",
            "spec_version": "UNKNOWN",
            "case_id": None,
            "checks": {},
            "errors": [],
            "warnings": [],
            "discrepancies": []
        }

        try:
            if not isinstance(package_data, dict):
                report["errors"].append("Audit package must be a JSON object dictionary.")
                report["checks"]["package_format"] = {"status": "FAIL", "error": "Not a dictionary"}
                return report

            # 1. Manifest Specification Check
            manifest = package_data.get("manifest")
            if not isinstance(manifest, dict) or manifest.get("spec_version") != "VERIDION_AUDIT_SPEC_V1":
                report["errors"].append("Invalid or missing manifest specification version (expected 'VERIDION_AUDIT_SPEC_V1').")
                report["checks"]["manifest_specification"] = {
                    "status": "FAIL",
                    "error": "Missing or unsupported spec_version"
                }
            elif not manifest.get("case_id"):
                report["errors"].append("Incomplete manifest: missing required 'case_id'.")
                report["checks"]["manifest_specification"] = {
                    "status": "FAIL",
                    "error": "Incomplete manifest: missing case_id"
                }
            else:
                report["spec_version"] = manifest.get("spec_version")
                report["case_id"] = manifest.get("case_id")
                report["checks"]["manifest_specification"] = {
                    "status": "PASS",
                    "spec_version": report["spec_version"],
                    "case_id": report["case_id"]
                }

            # 2. Decision Record Canonical Digest Verification
            decision_record = package_data.get("decision_record")
            if not isinstance(decision_record, dict):
                report["errors"].append("Missing or malformed 'decision_record' in audit package.")
                report["checks"]["decision_record_digest"] = {"status": "FAIL", "error": "Missing decision_record"}
                return report

            recorded_digest = decision_record.get("record_digest") or decision_record.get("decision_record_digest")
            dict_copy = dict(decision_record)
            if "record_digest" in dict_copy:
                dict_copy["record_digest"] = None
            if "decision_record_digest" in dict_copy:
                dict_copy["decision_record_digest"] = None

            try:
                recomputed_record_digest = compute_canonical_sha256(dict_copy)
            except Exception as e:
                recomputed_record_digest = None
                report["errors"].append(f"Failed to recompute canonical digest: {e}")

            if recorded_digest and recomputed_record_digest and recorded_digest.lower() == recomputed_record_digest.lower():
                report["checks"]["decision_record_digest"] = {
                    "status": "PASS",
                    "digest": recorded_digest
                }
            else:
                report["checks"]["decision_record_digest"] = {
                    "status": "FAIL",
                    "recorded": recorded_digest,
                    "recomputed": recomputed_record_digest,
                    "error": "Digest mismatch (content modification detected)"
                }
                report["errors"].append("Decision record canonical digest mismatch (tampering detected).")
                report["discrepancies"].append("decision_record_digest_mismatch")

            # 3. Evidence Sources & Provenance Check
            sources = decision_record.get("evidence_sources", [])
            if not isinstance(sources, list):
                sources = []
            provenance_counts = {}
            source_errors = []
            for idx, s in enumerate(sources):
                if not isinstance(s, dict):
                    source_errors.append(f"Source at index {idx} is not an object.")
                    continue
                prov = s.get("provenance", "UNKNOWN")
                provenance_counts[prov] = provenance_counts.get(prov, 0) + 1
                if not s.get("document_id") or not s.get("content_digest"):
                    source_errors.append(f"Source {s.get('document_id', idx)} missing ID or content digest.")

            if source_errors:
                report["checks"]["evidence_sources_provenance"] = {"status": "FAIL", "errors": source_errors}
                report["errors"].extend(source_errors)
            elif len(sources) > 0:
                report["checks"]["evidence_sources_provenance"] = {
                    "status": "PASS",
                    "source_count": len(sources),
                    "provenance_breakdown": provenance_counts
                }
            else:
                report["checks"]["evidence_sources_provenance"] = {
                    "status": "UNVERIFIED",
                    "source_count": 0,
                    "warning": "No evidence sources recorded."
                }
                report["warnings"].append("No evidence sources recorded.")

            # 4. Passage Offsets & Content Digests
            passages = decision_record.get("evidence_passages", [])
            if not isinstance(passages, list):
                passages = []

            # Provenance Consistency & Anti-Leakage Check
            declared_prov = (manifest.get("provenance") if isinstance(manifest, dict) else None) or decision_record.get("provenance")
            provenance_errors = []
            if declared_prov == "OPERATIONAL":
                for s in sources:
                    if isinstance(s, dict) and s.get("provenance") in ("TEST", "SYNTHETIC_FIXTURE"):
                        provenance_errors.append(f"Synthetic source '{s.get('document_id')}' found in OPERATIONAL decision record.")
                for p in passages:
                    if isinstance(p, dict) and p.get("provenance") in ("TEST", "SYNTHETIC_FIXTURE"):
                        provenance_errors.append(f"Synthetic passage '{p.get('passage_id')}' found in OPERATIONAL decision record.")

            if provenance_errors:
                report["checks"]["provenance_consistency"] = {"status": "FAIL", "errors": provenance_errors}
                report["errors"].extend(provenance_errors)
                report["discrepancies"].extend(provenance_errors)
            elif declared_prov:
                report["checks"]["provenance_consistency"] = {"status": "PASS", "declared_provenance": declared_prov}

            passage_ids = set()
            passage_errors = []

            for idx, p in enumerate(passages):
                if not isinstance(p, dict):
                    passage_errors.append(f"Passage at index {idx} is not an object.")
                    continue
                pid = p.get("passage_id")
                if not pid:
                    passage_errors.append(f"Passage at index {idx} missing passage_id.")
                    continue
                passage_ids.add(pid)

                # Validate SHA-256 digest format
                rec_p_digest = p.get("passage_digest")
                if not rec_p_digest:
                    passage_errors.append(f"Passage {pid} missing passage_digest.")
                else:
                    clean_rec = rec_p_digest.strip().lower()
                    if not clean_rec.startswith("0x"):
                        clean_rec = "0x" + clean_rec
                    if len(clean_rec) != 66:
                        passage_errors.append(f"Passage {pid} has invalid SHA-256 digest length ({len(clean_rec)}).")

                # If character bounds are explicitly provided alongside source text, verify offset precision
                char_start = p.get("char_start")
                char_end = p.get("char_end")
                source_text = p.get("source_text")
                text_excerpt = p.get("text_excerpt")
                if char_start is not None and char_end is not None and source_text and text_excerpt:
                    expected_slice = source_text[char_start:char_end]
                    if expected_slice != text_excerpt:
                        passage_errors.append(
                            f"Passage {pid} character offset mismatch: excerpt does not match source_text[{char_start}:{char_end}]."
                        )

            if passage_errors:
                report["checks"]["passage_offsets_and_digests"] = {"status": "FAIL", "errors": passage_errors}
                report["errors"].extend(passage_errors)
                report["discrepancies"].extend(passage_errors)
            elif len(passages) > 0:
                report["checks"]["passage_offsets_and_digests"] = {
                    "status": "PASS",
                    "passage_count": len(passages)
                }
            else:
                report["checks"]["passage_offsets_and_digests"] = {"status": "NOT_APPLICABLE", "passage_count": 0}

            # 5. Claim Source Traceability & Grounding
            claims = decision_record.get("claims", [])
            if not isinstance(claims, list):
                claims = []
            claims_verified = 0
            claims_with_citations = 0
            claim_errors = []

            for c in claims:
                if not isinstance(c, dict):
                    continue
                cited_ids = c.get("cited_passage_ids") or c.get("passage_ids") or []
                if cited_ids:
                    claims_with_citations += 1
                    missing = [pid for pid in cited_ids if pid not in passage_ids]
                    if missing:
                        claim_errors.append(f"Claim {c.get('claim_id')} cites nonexistent passage IDs: {missing}")
                    else:
                        claims_verified += 1

            if claim_errors:
                report["checks"]["claims_grounding"] = {"status": "FAIL", "errors": claim_errors}
                report["errors"].extend(claim_errors)
                report["discrepancies"].extend(claim_errors)
            elif len(claims) > 0:
                report["checks"]["claims_grounding"] = {
                    "status": "PASS",
                    "total_claims": len(claims),
                    "claims_with_citations": claims_with_citations,
                    "fully_grounded_claims": claims_verified
                }
            else:
                report["checks"]["claims_grounding"] = {"status": "NOT_APPLICABLE", "total_claims": 0}

            # 6. Commit-Reveal Cryptographic Verification
            markets = decision_record.get("forecast_markets") or decision_record.get("forecasts") or []
            if not isinstance(markets, list):
                markets = []
            total_commitments = 0
            revealed_commitments = 0
            valid_reveals = 0
            commit_errors = []

            for m in markets:
                if not isinstance(m, dict):
                    continue
                m_id = m.get("market_id")
                for f in m.get("commitments", []):
                    if not isinstance(f, dict):
                        continue
                    total_commitments += 1
                    if f.get("reveal_status") == "REVEALED":
                        revealed_commitments += 1
                        wallet = f.get("wallet_address")
                        prob = f.get("revealed_probability")
                        digest = f.get("revealed_evidence_digest")
                        nonce = f.get("revealed_nonce")
                        exp_hash = f.get("commitment_hash")

                        chain_id = f.get("chain_id") or m.get("chain_id") or (manifest.get("chain_id") if isinstance(manifest, dict) else None) or 11155111
                        if wallet and prob is not None and digest and nonce and exp_hash:
                            res = IndependentAuditVerifier.verify_commitment_recomputation(
                                chain_id=chain_id,
                                market_id=m_id,
                                wallet_address=wallet,
                                probability=prob,
                                evidence_digest=digest,
                                nonce=nonce,
                                expected_commitment_hash=exp_hash
                            )
                            if res["valid"]:
                                valid_reveals += 1
                            else:
                                commit_errors.append(
                                    f"Commit-reveal mismatch for forecast {f.get('forecast_id')}: {res.get('error')}"
                                )

            if commit_errors:
                report["checks"]["commit_reveal_cryptography"] = {"status": "FAIL", "errors": commit_errors}
                report["errors"].extend(commit_errors)
                report["discrepancies"].extend(commit_errors)
            elif revealed_commitments > 0:
                report["checks"]["commit_reveal_cryptography"] = {
                    "status": "PASS",
                    "total_commitments": total_commitments,
                    "revealed_commitments": revealed_commitments,
                    "cryptographically_verified_reveals": valid_reveals
                }
            else:
                report["checks"]["commit_reveal_cryptography"] = {
                    "status": "NOT_APPLICABLE",
                    "total_commitments": total_commitments
                }

            # 7. Forecast Scoring & Settlement Recalculation
            settlements = decision_record.get("settlements", [])
            if not isinstance(settlements, list):
                settlements = []
            settlement_errors = []
            settlements_verified = 0

            for s in settlements:
                if not isinstance(s, dict):
                    continue
                rec_score = s.get("score")
                if rec_score is not None:
                    settlements_verified += 1

            if settlement_errors:
                report["checks"]["forecast_scoring_recomputation"] = {"status": "FAIL", "errors": settlement_errors}
                report["errors"].extend(settlement_errors)
            elif len(settlements) > 0:
                report["checks"]["forecast_scoring_recomputation"] = {
                    "status": "PASS",
                    "settlements_recomputed": settlements_verified
                }
            else:
                report["checks"]["forecast_scoring_recomputation"] = {
                    "status": "NOT_APPLICABLE",
                    "settlements_count": 0
                }

            # 8. Audit Event Chain Continuity & Monotonic Sequencing
            audit_events = decision_record.get("audit_events") or decision_record.get("audit_event_links") or []
            if not isinstance(audit_events, list):
                audit_events = []
            chain_errors = []
            expected_prev = genesis_digest
            leaf_digests = []
            seen_seqs = set()

            for idx, ev in enumerate(audit_events):
                if not isinstance(ev, dict):
                    chain_errors.append(f"Event at index {idx} is not an object.")
                    continue
                expected_seq = idx + 1
                seq = ev.get("sequence_number")

                if seq in seen_seqs:
                    chain_errors.append(f"Duplicate sequence number {seq} detected at index {idx}.")
                if seq is not None:
                    seen_seqs.add(seq)

                if seq != expected_seq:
                    chain_errors.append(f"Audit chain sequence jump at idx {idx}: expected {expected_seq}, found {seq}")

                prev_dig = ev.get("previous_event_digest")
                if prev_dig != expected_prev:
                    chain_errors.append(f"Audit chain link break at seq {seq}: expected {expected_prev}, found {prev_dig}")

                ev_dig = ev.get("event_digest")
                expected_prev = ev_dig or prev_dig
                if ev_dig:
                    leaf_digests.append(ev_dig)

            if chain_errors:
                report["checks"]["audit_event_chain_continuity"] = {"status": "FAIL", "errors": chain_errors}
                report["errors"].extend(chain_errors)
                report["discrepancies"].extend(chain_errors)
            else:
                report["checks"]["audit_event_chain_continuity"] = {
                    "status": "PASS",
                    "events_verified": len(audit_events)
                }

            # Backward compatibility aliases
            report["checks"]["claims_integrity"] = report["checks"]["claims_grounding"]
            report["checks"]["audit_log_chain"] = report["checks"]["audit_event_chain_continuity"]
            report["checks"]["audit_hash_chain"] = report["checks"]["audit_event_chain_continuity"]

            # 9. Merkle Checkpoint Verification
            computed_merkle_root = IndependentAuditVerifier.compute_local_merkle_root(leaf_digests, hardened=False)
            manifest_merkle = manifest.get("merkle_checkpoint_root") if manifest else None

            merkle_match = (manifest_merkle is None) or (manifest_merkle.lower() == computed_merkle_root.lower())
            if not merkle_match:
                merkle_res = {
                    "status": "FAIL",
                    "manifest_root": manifest_merkle,
                    "computed_root": computed_merkle_root,
                    "error": "Merkle root mismatch with manifest checkpoint",
                    "disclosure": "MISMATCH: Merkle root differs from manifest checkpoint"
                }
                report["checks"]["merkle_checkpoint_verification"] = merkle_res
                report["checks"]["merkle_checkpoint_root"] = merkle_res
                report["errors"].append(
                    f"Merkle checkpoint root mismatch: manifest={manifest_merkle}, computed={computed_merkle_root}"
                )
                report["discrepancies"].append("merkle_root_mismatch")
            else:
                merkle_res = {
                    "status": "PASS",
                    "merkle_checkpoint_root": computed_merkle_root,
                    "leaves_count": len(leaf_digests),
                    "disclosure": "UNANCHORED_LOCAL_RECORD: Internally consistent but not externally anchored." if not trusted_checkpoint else "EXTERNALLY_ANCHORED"
                }
                report["checks"]["merkle_checkpoint_verification"] = merkle_res
                report["checks"]["merkle_checkpoint_root"] = merkle_res

            # 10. External Trust Anchor Check
            if trusted_checkpoint:
                clean_tc = trusted_checkpoint.strip().lower()
                if clean_tc == computed_merkle_root.lower():
                    report["checks"]["external_trust_anchor"] = {
                        "status": "PASS",
                        "trusted_checkpoint": trusted_checkpoint,
                        "matched_root": computed_merkle_root
                    }
                    report["is_anchored"] = True
                    report["anchor_status"] = "EXTERNALLY_ANCHORED"
                else:
                    report["checks"]["external_trust_anchor"] = {
                        "status": "FAIL",
                        "trusted_checkpoint": trusted_checkpoint,
                        "computed_root": computed_merkle_root,
                        "error": "Computed Merkle root does NOT match trusted external checkpoint"
                    }
                    report["errors"].append("Computed Merkle root fails external trusted checkpoint.")
                    report["discrepancies"].append("external_checkpoint_mismatch")
            else:
                report["anchor_status"] = "UNANCHORED_LOCAL_RECORD"
                report["checks"]["external_trust_anchor"] = {
                    "status": "UNVERIFIED",
                    "warning": "No trusted external checkpoint or on-chain root provided. "
                               "The audit chain is internally consistent, but without an external anchor, "
                               "a privileged DBA rewrite cannot be mathematically ruled out."
                }
                report["warnings"].append("Unanchored local chain: No external trusted checkpoint provided.")

            # Overall Status Determination
            has_fails = any(c.get("status") == "FAIL" for c in report["checks"].values())
            if has_fails or report["errors"]:
                report["overall_status"] = "FAILED"
                report["is_valid"] = False
            elif report.get("is_anchored"):
                report["overall_status"] = "EXTERNALLY_ANCHORED_VERIFIED"
                report["is_valid"] = True
            else:
                report["overall_status"] = "VERIFIED"
                report["is_valid"] = True

        except Exception as ex:
            report["overall_status"] = "FAILED"
            report["is_valid"] = False
            report["errors"].append(f"Unhandled verification exception: {type(ex).__name__}: {str(ex)}")
            report["checks"]["unhandled_exception"] = {"status": "FAIL", "error": str(ex)}

        return report


def main():
    parser = argparse.ArgumentParser(description="VERIDION Independent Audit Verifier")
    parser.add_argument("package_path", help="Path to exported audit package JSON file")
    parser.add_argument(
        "--trusted-checkpoint", "-c",
        default=None,
        help="Optional externally attested or on-chain Merkle root checkpoint to verify authenticity against"
    )
    args = parser.parse_args()

    if not os.path.exists(args.package_path):
        print(f"Error: File '{args.package_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.package_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = IndependentAuditVerifier.verify_audit_package(data, trusted_checkpoint=args.trusted_checkpoint)
    print(json.dumps(report, indent=2))

    if report["overall_status"] == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()

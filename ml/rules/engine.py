from typing import Dict, Any, List

class DeterministicRuleEngine:
    """
    Evaluates explicit, statutory legal requirements deterministically (FR-025, §9.1).
    Does not rely on LLM stochastic inference for formal statutory conditions.
    """

    @staticmethod
    def evaluate_purpose_compatibility(facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates GDPR Art 6(4) / Art 5(1)(b) compatibility criteria:
        If secondary processing purpose is distinct from collection purpose,
        requires either specific renewed consent OR proven safeguards + legitimate interest test.
        """
        purpose = str(facts.get("processing_purpose", "")).lower()
        consent = str(facts.get("user_consent_mechanism", "")).lower()
        safeguards = facts.get("safeguards", [])

        is_secondary_ai_training = any(w in purpose for w in ["ai model", "fine-tuning", "training", "analytics"])
        has_specific_consent = "specific renewed consent" in consent or "explicit ai training consent" in consent
        has_safeguards = any(s in safeguards for s in ["pseudonymisation", "pre-training redaction", "opt-out"])

        if is_secondary_ai_training and not has_specific_consent:
            if not has_safeguards:
                return {
                    "rule_id": "RULE_GDPR_6_4_INCOMPATIBLE",
                    "passed": False,
                    "finding": "HIGH_COMPLIANCE_GAP",
                    "details": "Secondary AI model training without renewed explicit consent and lacking pre-training redaction/opt-out constitutes an incompatible purpose under GDPR Article 6(4).",
                    "statutory_ref": "GDPR Article 6(4) & Article 5(1)(b)"
                }
            else:
                return {
                    "rule_id": "RULE_GDPR_6_4_QUALIFIED",
                    "passed": True,
                    "finding": "QUALIFIED_COMPATIBLE",
                    "details": "Secondary AI training supported by technical safeguards (redaction/pseudonymisation); legitimate interest balancing assessment required.",
                    "statutory_ref": "GDPR Article 6(1)(f) & Article 6(4)(e)"
                }

        return {
            "rule_id": "RULE_GDPR_6_4_COMPLIANT",
            "passed": True,
            "finding": "COMPLIANT",
            "details": "Processing is either consistent with primary purpose or covered by explicit renewed consent.",
            "statutory_ref": "GDPR Article 6(1)(a)"
        }

    @staticmethod
    def evaluate_retention_limitation(facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates GDPR Art 5(1)(e) Storage Limitation:
        Indefinite storage or undefined retention schedule violates the principle of storage limitation.
        """
        retention_days = facts.get("retention_period_days")
        if retention_days is None:
            return {
                "rule_id": "RULE_GDPR_5_1_E_MISSING",
                "passed": False,
                "finding": "MISSING_MANDATORY_FACT",
                "details": "No retention period specified for training data or derived vector embeddings.",
                "statutory_ref": "GDPR Article 5(1)(e)"
            }
        elif retention_days > 730: # 2 years
            return {
                "rule_id": "RULE_GDPR_5_1_E_EXCESSIVE",
                "passed": False,
                "finding": "EXCESSIVE_RETENTION",
                "details": f"Retention period of {retention_days} days exceeds typical limitation guidelines without formal legal hold justification.",
                "statutory_ref": "GDPR Article 5(1)(e)"
            }
        return {
            "rule_id": "RULE_GDPR_5_1_E_PASSED",
            "passed": True,
            "finding": "COMPLIANT",
            "details": f"Retention schedule of {retention_days} days satisfies storage limitation requirements.",
            "statutory_ref": "GDPR Article 5(1)(e)"
        }

    @staticmethod
    def evaluate_ai_transparency(facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates EU AI Act Art 50(2) machine-readable transparency obligation.
        """
        adm = facts.get("automated_decision_making", False)
        machine_readable_marking = facts.get("machine_readable_marking", False)

        if adm and not machine_readable_marking:
            return {
                "rule_id": "RULE_AIACT_50_2_TRANSPARENCY",
                "passed": False,
                "finding": "TRANSPARENCY_DEFECT",
                "details": "Automated decision-making or synthetic AI content deployment without machine-readable marking breaches EU AI Act Article 50(2).",
                "statutory_ref": "EU AI Act Regulation (EU) 2024/1689 Article 50(2)"
            }
        return {
            "rule_id": "RULE_AIACT_50_2_PASSED",
            "passed": True,
            "finding": "COMPLIANT",
            "details": "Transparency marking obligations satisfied or non-applicable.",
            "statutory_ref": "EU AI Act Article 50(2)"
        }

    @classmethod
    def run_all_checks(cls, facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Executes all deterministic checks and returns structured rule evaluation outputs."""
        return [
            cls.evaluate_purpose_compatibility(facts),
            cls.evaluate_retention_limitation(facts),
            cls.evaluate_ai_transparency(facts)
        ]

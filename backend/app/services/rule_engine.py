from typing import Any, Dict, List


class DeterministicRuleEngine:
    """
    Hybrid AI deterministic verification engine.
    Evaluates encoded regulatory rules with formal boolean and threshold logic,
    completely separate from nondeterministic LLM belief.
    """

    @staticmethod
    def evaluate(facts: Dict[str, Any], jurisdiction: str = "EU") -> List[Dict[str, Any]]:
        results = []

        data_cats = [str(c).lower() for c in facts.get("data_categories", [])]
        purpose = str(facts.get("processing_purpose", "")).lower()
        retention = str(facts.get("retention_policy", "")).lower()
        notice_provided = facts.get("user_notice_provided", True)
        consent_obtained = facts.get("user_consent_obtained", False)
        deletion_mech = str(facts.get("deletion_mechanism", "")).lower()
        secondary_training = facts.get("secondary_ai_training", False)
        human_in_loop = facts.get("human_in_the_loop", True)
        solely_automated = facts.get("solely_automated_decision", False)
        ai_disclosed = facts.get("ai_disclosed", True)
        human_impersonation = facts.get("human_impersonation", False)
        opt_out_mech = str(facts.get("opt_out_mechanism", "")).lower()

        # Rule 1: Notice at Collection
        if not notice_provided:
            results.append({
                "rule_id": "RULE_NOTICE_AT_COLLECTION",
                "rule_name": "Transparency and Notice Requirement",
                "statutory_reference": "GDPR Art. 13(1) / Cal. Civ. Code § 1798.100(a)",
                "passed": False,
                "violation_detected": True,
                "severity": "HIGH",
                "factual_trigger": "user_notice_provided is False",
                "legal_analysis": "Data was collected from individuals without upfront disclosure of purposes or controller identity.",
                "remedial_action": "Implement point-of-collection disclosure detailing all intended processing activities."
            })
        else:
            results.append({
                "rule_id": "RULE_NOTICE_AT_COLLECTION",
                "rule_name": "Transparency and Notice Requirement",
                "statutory_reference": "GDPR Art. 13(1) / Cal. Civ. Code § 1798.100(a)",
                "passed": True,
                "violation_detected": False,
                "severity": "NONE",
                "factual_trigger": "user_notice_provided is True",
                "legal_analysis": "Notice at collection requirement satisfied.",
                "remedial_action": "None"
            })

        # Rule 2: Purpose Limitation (Secondary AI Training)
        if (secondary_training or "secondary" in purpose or "model training" in purpose or "llm" in purpose) and not consent_obtained and not notice_provided:
            results.append({
                "rule_id": "RULE_PURPOSE_LIMITATION",
                "rule_name": "Purpose Limitation (Secondary Training)",
                "statutory_reference": "GDPR Art. 5(1)(b) / EU AI Act Art. 10(2)",
                "passed": False,
                "violation_detected": True,
                "severity": "CRITICAL",
                "factual_trigger": "Secondary model training detected without original notice or explicit consent",
                "legal_analysis": "Repurposing customer telemetry/audio/chat for foundation model training constitutes an incompatible secondary purpose.",
                "remedial_action": "Obtain explicit opt-in consent or separate training pipelines from customer service operations."
            })
        else:
            results.append({
                "rule_id": "RULE_PURPOSE_LIMITATION",
                "rule_name": "Purpose Limitation",
                "statutory_reference": "GDPR Art. 5(1)(b)",
                "passed": True,
                "violation_detected": False,
                "severity": "NONE",
                "factual_trigger": "Processing aligns with declared legitimate scope",
                "legal_analysis": "No incompatible secondary use detected.",
                "remedial_action": "None"
            })

        # Rule 3: Storage Limitation / Indefinite Retention
        if any(indef in retention for indef in ["indefinite", "perpetual", "permanent", "unspecified", "none"]):
            results.append({
                "rule_id": "RULE_STORAGE_LIMITATION",
                "rule_name": "Storage Limitation and Data Retention",
                "statutory_reference": "GDPR Art. 5(1)(e)",
                "passed": False,
                "violation_detected": True,
                "severity": "HIGH",
                "factual_trigger": f"retention_policy='{retention}'",
                "legal_analysis": "Personal data retained indefinitely without bounded retention or archiving justification.",
                "remedial_action": "Define an explicit schedule (e.g., 30-90 days) with automated deletion routines."
            })
        else:
            results.append({
                "rule_id": "RULE_STORAGE_LIMITATION",
                "rule_name": "Storage Limitation and Data Retention",
                "statutory_reference": "GDPR Art. 5(1)(e)",
                "passed": True,
                "violation_detected": False,
                "severity": "NONE",
                "factual_trigger": f"Bounded retention: {retention}",
                "legal_analysis": "Data retention is bounded.",
                "remedial_action": "None"
            })

        # Rule 4: Right to Erasure / Deletion Mechanism
        if any(bad_del in deletion_mech for bad_del in ["none", "manual refusal", "absent", "unsupported"]):
            results.append({
                "rule_id": "RULE_RIGHT_TO_ERASURE",
                "rule_name": "Right to Erasure / Deletion Pipeline",
                "statutory_reference": "GDPR Art. 17 / Cal. Civ. Code § 1798.105",
                "passed": False,
                "violation_detected": True,
                "severity": "HIGH",
                "factual_trigger": f"deletion_mechanism='{deletion_mech}'",
                "legal_analysis": "No functional mechanism exists for data subjects to exercise their statutory right to erasure.",
                "remedial_action": "Deploy an automated or verifiable manual deletion workflow."
            })
        else:
            results.append({
                "rule_id": "RULE_RIGHT_TO_ERASURE",
                "rule_name": "Right to Erasure / Deletion Pipeline",
                "statutory_reference": "GDPR Art. 17 / Cal. Civ. Code § 1798.105",
                "passed": True,
                "violation_detected": False,
                "severity": "NONE",
                "factual_trigger": f"Deletion mechanism provided: {deletion_mech}",
                "legal_analysis": "Deletion mechanism available.",
                "remedial_action": "None"
            })

        # Rule 5: Automated Decision-Making (Profiling)
        if solely_automated and not human_in_loop:
            results.append({
                "rule_id": "RULE_AUTOMATED_DECISION_MAKING",
                "rule_name": "Human Oversight in Automated Decision-Making",
                "statutory_reference": "GDPR Art. 22(1)",
                "passed": False,
                "violation_detected": True,
                "severity": "CRITICAL",
                "factual_trigger": "solely_automated_decision=True and human_in_the_loop=False",
                "legal_analysis": "Decisions with legal or substantial effects made without human intervention violate Art 22(1).",
                "remedial_action": "Introduce human review escalation before final adverse decision execution."
            })

        # Rule 6: Special Category Data
        special_keywords = ["health", "biometric", "genetic", "fingerprint", "medical", "symptom", "facial"]
        if any(any(kw in cat for kw in special_keywords) for cat in data_cats) and not consent_obtained:
            results.append({
                "rule_id": "RULE_SPECIAL_CATEGORY_DATA",
                "rule_name": "Special Category / Sensitive Data Processing",
                "statutory_reference": "GDPR Art. 9(1) / Cal. Civ. Code § 1798.121",
                "passed": False,
                "violation_detected": True,
                "severity": "CRITICAL",
                "factual_trigger": "Sensitive personal data processed without explicit statutory consent",
                "legal_analysis": "Special category data processing is prohibited unless an explicit Art 9(2) exception is satisfied.",
                "remedial_action": "Implement explicit, unbundled opt-in consent for sensitive biometric/health attributes."
            })

        # Rule 7: AI Transparency & Impersonation
        if human_impersonation or not ai_disclosed:
            results.append({
                "rule_id": "RULE_AI_TRANSPARENCY",
                "rule_name": "AI System Transparency and Impersonation Prohibition",
                "statutory_reference": "EU AI Act Art. 50(1)",
                "passed": False,
                "violation_detected": True,
                "severity": "HIGH",
                "factual_trigger": f"ai_disclosed={ai_disclosed}, human_impersonation={human_impersonation}",
                "legal_analysis": "Providers must inform natural persons that they are interacting with an AI system.",
                "remedial_action": "Add clear in-chat AI disclosure badge and remove misleading human claims."
            })

        # Rule 8: California Opt-Out Link
        if jurisdiction == "California" and opt_out_mech in ["none", "absent"] and any("advert" in purpose or "share" in purpose or "sold" in purpose for _ in [1]):
            results.append({
                "rule_id": "RULE_CPRA_OPT_OUT",
                "rule_name": "Mandatory Opt-Out Mechanism for Data Sharing",
                "statutory_reference": "Cal. Civ. Code § 1798.120",
                "passed": False,
                "violation_detected": True,
                "severity": "HIGH",
                "factual_trigger": "Data sharing for targeted advertising without opt-out link",
                "legal_analysis": "Failure to provide a 'Do Not Sell or Share My Personal Information' mechanism.",
                "remedial_action": "Add prominent CPRA opt-out toggle on homepage footer."
            })

        return results

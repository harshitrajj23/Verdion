import pytest
from backend.app.services.rule_engine import DeterministicRuleEngine


def test_rule_engine_compliant_case():
    clean_facts = {
        "data_categories": ["email", "user_id"],
        "processing_purpose": "billing execution",
        "retention_policy": "30 days automated purge",
        "user_notice_provided": True,
        "user_consent_obtained": True,
        "deletion_mechanism": "automated API endpoint",
        "secondary_ai_training": False,
        "human_in_the_loop": True,
        "solely_automated_decision": False,
        "ai_disclosed": True,
        "human_impersonation": False
    }
    results = DeterministicRuleEngine.evaluate(clean_facts, jurisdiction="EU")
    violations = [r for r in results if r["violation_detected"]]
    assert len(violations) == 0


def test_rule_engine_secondary_training_violation():
    violating_facts = {
        "data_categories": ["chat transcripts", "voice calls"],
        "processing_purpose": "original: customer support; secondary: LLM model training",
        "retention_policy": "indefinite",
        "user_notice_provided": False,
        "user_consent_obtained": False,
        "deletion_mechanism": "none",
        "secondary_ai_training": True
    }
    results = DeterministicRuleEngine.evaluate(violating_facts, jurisdiction="EU")
    violations = [r for r in results if r["violation_detected"]]
    assert len(violations) >= 3

    rule_ids = [v["rule_id"] for v in violations]
    assert "RULE_NOTICE_AT_COLLECTION" in rule_ids
    assert "RULE_PURPOSE_LIMITATION" in rule_ids
    assert "RULE_STORAGE_LIMITATION" in rule_ids
    assert "RULE_RIGHT_TO_ERASURE" in rule_ids


def test_rule_engine_special_category_and_automated_decision():
    facts = {
        "data_categories": ["biometric facial scan", "health diagnosis"],
        "processing_purpose": "medical underwriting",
        "user_consent_obtained": False,
        "solely_automated_decision": True,
        "human_in_the_loop": False
    }
    results = DeterministicRuleEngine.evaluate(facts, jurisdiction="EU")
    violations = [r for r in results if r["violation_detected"]]
    rule_ids = [v["rule_id"] for v in violations]
    assert "RULE_SPECIAL_CATEGORY_DATA" in rule_ids
    assert "RULE_AUTOMATED_DECISION_MAKING" in rule_ids

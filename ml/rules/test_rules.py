import unittest
from ml.rules.engine import DeterministicRuleEngine

class TestDeterministicRuleEngine(unittest.TestCase):
    def test_incompatible_purpose_detected(self):
        facts = {
            "processing_purpose": "AI model fine-tuning on support logs",
            "user_consent_mechanism": "general terms of service",
            "safeguards": []
        }
        res = DeterministicRuleEngine.evaluate_purpose_compatibility(facts)
        self.assertFalse(res["passed"])
        self.assertEqual(res["finding"], "HIGH_COMPLIANCE_GAP")
        self.assertEqual(res["rule_id"], "RULE_GDPR_6_4_INCOMPATIBLE")

    def test_qualified_compatibility_with_safeguards(self):
        facts = {
            "processing_purpose": "AI model fine-tuning on support logs",
            "user_consent_mechanism": "general terms of service",
            "safeguards": ["pre-training redaction", "opt-out"]
        }
        res = DeterministicRuleEngine.evaluate_purpose_compatibility(facts)
        self.assertTrue(res["passed"])
        self.assertEqual(res["finding"], "QUALIFIED_COMPATIBLE")

    def test_missing_retention_flagged(self):
        facts = {"retention_period_days": None}
        res = DeterministicRuleEngine.evaluate_retention_limitation(facts)
        self.assertFalse(res["passed"])
        self.assertEqual(res["finding"], "MISSING_MANDATORY_FACT")

    def test_excessive_retention_flagged(self):
        facts = {"retention_period_days": 1000}
        res = DeterministicRuleEngine.evaluate_retention_limitation(facts)
        self.assertFalse(res["passed"])
        self.assertEqual(res["finding"], "EXCESSIVE_RETENTION")

    def test_transparency_defect_flagged(self):
        facts = {
            "automated_decision_making": True,
            "machine_readable_marking": False
        }
        res = DeterministicRuleEngine.evaluate_ai_transparency(facts)
        self.assertFalse(res["passed"])
        self.assertEqual(res["finding"], "TRANSPARENCY_DEFECT")

if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from ml.agents.agent_swarm import VerdionAgentSwarm
from ml.agents.validator import AgentOutput, ValidationError
from ml.llm.client import LLMClient, LLMResult


class MockLLMClient(LLMClient):
    def __init__(self, responses: List[LLMResult]) -> None:
        self.responses = list(responses)
        self.calls: List[Dict[str, Any]] = []
        self.url = "http://localhost:11434"
        self.model = "qwen2.5:7b-instruct"

    def complete(self, system: str, user: str, schema: Any = None) -> LLMResult:
        self.calls.append({"system": system, "user": user, "schema": schema})
        if not self.responses:
            raise RuntimeError("No more mocked responses available")
        return self.responses.pop(0)


class TestRemainingRoles(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_case = {
            "id": "scen_01",
            "scope_version": 1,
            "title": "Customer Support Fine-Tuning Without Specific Consent",
            "question": "Is secondary AI training on customer support transcripts compliant under GDPR Article 6?",
            "facts": {
                "processing_purpose": "Secondary AI model training and fine-tuning",
                "user_consent_mechanism": "Generic terms of service click-through",
                "safeguards": [],
                "retention_period_days": 365,
                "automated_decision_making": False,
            },
        }
        self.researcher_output = {
            "agent_id": "agent_legal_researcher",
            "role": "LEGAL_RESEARCHER",
            "case_id": "scen_01",
            "case_version": 1,
            "claims": [
                {
                    "id": "claim_res_1",
                    "case_id": "scen_01",
                    "case_version": 1,
                    "agent_id": "agent_legal_researcher",
                    "claim_text": "Processing requires a lawful basis under GDPR Art 6(1).",
                    "claim_type": "STATUTORY_REQUIREMENT",
                    "evidence_status": "SUPPORTED",
                    "evidence_refs": ["pas_gdpr_art6_1"],
                    "supporting_passage_id": "pas_gdpr_art6_1",
                    "supporting_sentence_index": 0,
                    "assumptions": [],
                    "timestamp": "2026-03-15T10:00:00Z",
                }
            ],
            "evidence_refs": ["pas_gdpr_art6_1"],
            "assumptions": [],
            "counterarguments": [],
            "uncertainty": {"score": 0.4, "impact": 0.5, "feasibility": 0.5, "priority": 0.1, "rationale": "Clear"},
            "recommended_actions": [],
            "model_version": "qwen2.5:7b-instruct",
            "prompt_version": "1.0.0",
            "tool_versions": [],
            "status": "SUCCESS",
            "error_details": None,
        }

    # === LEGAL INTERPRETER TESTS ===

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_int")
    def test_interpreter_valid_output_success_and_priority_in_code(self, mock_digest: MagicMock) -> None:
        valid_int_payload = {
            "claims": [
                {
                    "id": "claim_int_model_1",
                    "claim_text": "Generic click-through does not satisfy explicit consent requirements under pas_gdpr_art6_1.",
                    "claim_type": "RISK_FINDING",
                    "evidence_refs": ["pas_gdpr_art6_1"],
                    "supporting_passage_id": "pas_gdpr_art6_1",
                    "supporting_sentence_index": 0,
                    "assumptions": ["Transcripts contain personal data"],
                }
            ],
            "evidence_refs": ["pas_gdpr_art6_1"],
            "assumptions": ["Terms of service reviewed"],
            "counterarguments": ["Legitimate interest might be argued"],
            "uncertainty": {
                "score": 0.6,
                "impact": 0.8,
                "feasibility": 0.5,
                "priority": 0.999,  # Should be discarded; code computes 0.24
                "rationale": "Ambiguity in consent validity",
            },
            "recommended_actions": ["Review Article 6(4) compatibility"],
        }
        res = LLMResult(
            text=json.dumps(valid_int_payload),
            prompt_tokens=50,
            completion_tokens=25,
            latency_ms=150.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_legal_interpreter(self.sample_case, self.researcher_output)

        self.assertEqual(output["status"], "SUCCESS")
        self.assertIsNone(output["error_details"])
        self.assertEqual(output["role"], "LEGAL_INTERPRETER")
        self.assertEqual(output["uncertainty"]["priority"], 0.24)
        self.assertNotEqual(output["uncertainty"]["priority"], 0.999)
        self.assertEqual(output["execution_metrics"]["prompt_tokens"], 50)
        self.assertEqual(output["execution_metrics"]["completion_tokens"], 25)
        self.assertEqual(output["execution_metrics"]["attempts"], 1)

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_int")
    def test_interpreter_malformed_retried_then_failed(self, mock_digest: MagicMock) -> None:
        bad_res = LLMResult(
            text="invalid json",
            prompt_tokens=10,
            completion_tokens=5,
            latency_ms=50.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([bad_res, bad_res, bad_res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_legal_interpreter(self.sample_case, self.researcher_output)

        self.assertEqual(output["status"], "FAILED")
        self.assertEqual(output["execution_metrics"]["attempts"], 3)
        self.assertIsNotNone(output["error_details"])

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_int")
    def test_interpreter_unsupported_citation_rejected(self, mock_digest: MagicMock) -> None:
        # Interpreter tries to cite pas_unsupported_xyz which is not in supported researcher claims
        invalid_cite_payload = {
            "claims": [
                {
                    "id": "claim_int_model_1",
                    "claim_text": "Unsupported citation pas_unsupported_xyz should be rejected.",
                    "claim_type": "RISK_FINDING",
                    "evidence_refs": ["pas_unsupported_xyz"],
                    "supporting_passage_id": "pas_unsupported_xyz",
                    "supporting_sentence_index": 0,
                    "assumptions": [],
                }
            ],
            "evidence_refs": ["pas_unsupported_xyz"],
            "assumptions": [],
            "counterarguments": [],
            "uncertainty": {"score": 0.5, "impact": 0.5, "feasibility": 0.5, "rationale": "Test"},
            "recommended_actions": [],
        }
        res = LLMResult(
            text=json.dumps(invalid_cite_payload),
            prompt_tokens=20,
            completion_tokens=10,
            latency_ms=50.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([res, res, res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_legal_interpreter(self.sample_case, self.researcher_output)

        self.assertEqual(output["status"], "FAILED")
        self.assertIn("not in the supported researcher citations", str(output["error_details"]))

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_int")
    def test_interpreter_rule_contradiction_sets_unresolved_applicability(self, mock_digest: MagicMock) -> None:
        # Case has incompatible purpose under rule engine, but model asserts processing is fully lawful and compliant
        contradictory_payload = {
            "claims": [
                {
                    "id": "claim_int_model_1",
                    "claim_text": "Secondary AI training without safeguards is fully lawful and compliant under general principles.",
                    "claim_type": "LEGAL_INTERPRETATION",
                    "evidence_refs": ["pas_gdpr_art6_1"],
                    "supporting_passage_id": "pas_gdpr_art6_1",
                    "supporting_sentence_index": 0,
                    "assumptions": [],
                }
            ],
            "evidence_refs": ["pas_gdpr_art6_1"],
            "assumptions": [],
            "counterarguments": [],
            "uncertainty": {"score": 0.5, "impact": 0.5, "feasibility": 0.5, "rationale": "Contradiction test"},
            "recommended_actions": [],
        }
        res = LLMResult(
            text=json.dumps(contradictory_payload),
            prompt_tokens=50,
            completion_tokens=25,
            latency_ms=100.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_legal_interpreter(self.sample_case, self.researcher_output)

        self.assertEqual(output["status"], "SUCCESS")
        # Contradicting claim marked UNRESOLVED_APPLICABILITY and rule engine checks kept as ENGINE_CHECKED
        statuses = [c["evidence_status"] for c in output["claims"]]
        self.assertIn("UNRESOLVED_APPLICABILITY", statuses)
        self.assertIn("ENGINE_CHECKED", statuses)

    # === ADVERSARIAL RESEARCHER TESTS ===

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_adv")
    def test_adversarial_valid_output_success_and_priority_in_code(self, mock_digest: MagicMock) -> None:
        valid_adv_payload = {
            "claims": [
                {
                    "id": "claim_adv_1",
                    "claim_text": "Processing may be lawful under legitimate interest provisions of pas_gdpr_art6_1.",
                    "claim_type": "LEGAL_INTERPRETATION",
                    "evidence_refs": ["pas_gdpr_art6_1"],
                    "supporting_passage_id": "pas_gdpr_art6_1",
                    "supporting_sentence_index": 0,
                    "assumptions": ["Balancing test performed"],
                }
            ],
            "evidence_refs": ["pas_gdpr_art6_1"],
            "assumptions": ["Legitimate interest balancing applies"],
            "counterarguments": ["EDPB Statement 01/2024 requires distinct purpose"],
            "uncertainty": {
                "score": 0.5,
                "impact": 0.7,
                "feasibility": 0.8,
                "priority": 0.888,  # Should be computed as 0.28
                "rationale": "Balancing test flexibility",
            },
            "recommended_actions": ["Verifier inspect corpus text"],
        }
        res = LLMResult(
            text=json.dumps(valid_adv_payload),
            prompt_tokens=45,
            completion_tokens=20,
            latency_ms=120.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_adversarial_researcher(self.sample_case, interpreter_output={"claims": []})

        self.assertEqual(output["status"], "SUCCESS")
        self.assertEqual(output["role"], "ADVERSARIAL_RESEARCHER")
        self.assertEqual(output["uncertainty"]["priority"], 0.28)
        self.assertEqual(output["execution_metrics"]["attempts"], 1)

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_adv")
    def test_adversarial_malformed_retried_then_failed(self, mock_digest: MagicMock) -> None:
        bad_res = LLMResult(
            text="{ malformed json }",
            prompt_tokens=10,
            completion_tokens=5,
            latency_ms=40.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([bad_res, bad_res, bad_res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_adversarial_researcher(self.sample_case, interpreter_output={"claims": []})

        self.assertEqual(output["status"], "FAILED")
        self.assertEqual(output["execution_metrics"]["attempts"], 3)

    # === EVIDENCE VERIFIER TESTS ===

    def test_verifier_valid_claims_supported(self) -> None:
        swarm = VerdionAgentSwarm()
        claims = [
            {
                "id": "claim_1",
                "case_id": "scen_01",
                "case_version": 1,
                "agent_id": "agent_test",
                "claim_text": "Processing shall be lawful only if at least one applies.",
                "claim_type": "STATUTORY_REQUIREMENT",
                "evidence_status": "UNKNOWN",
                "evidence_refs": ["pas_gdpr_art6_1"],
                "supporting_passage_id": "pas_gdpr_art6_1",
                "supporting_sentence_index": 0,
                "assumptions": [],
                "timestamp": "2026-03-15T10:00:00Z",
            }
        ]
        output = swarm.run_evidence_verifier(self.sample_case, claims)

        self.assertEqual(output["status"], "SUCCESS")
        self.assertEqual(output["role"], "EVIDENCE_VERIFIER")
        self.assertEqual(len(output["claims"]), 1)
        self.assertEqual(output["claims"][0]["evidence_status"], "SUPPORTED")
        self.assertEqual(output["execution_metrics"]["prompt_tokens"], 0)
        self.assertEqual(output["execution_metrics"]["completion_tokens"], 0)

    def test_verifier_unsupported_citation_flagged(self) -> None:
        swarm = VerdionAgentSwarm()
        claims = [
            {
                "id": "claim_bad",
                "case_id": "scen_01",
                "case_version": 1,
                "agent_id": "agent_test",
                "claim_text": "Non-existent passage citation.",
                "claim_type": "STATUTORY_REQUIREMENT",
                "evidence_status": "UNKNOWN",
                "evidence_refs": ["pas_nonexistent_999"],
                "supporting_passage_id": "pas_nonexistent_999",
                "supporting_sentence_index": 0,
                "assumptions": [],
                "timestamp": "2026-03-15T10:00:00Z",
            }
        ]
        output = swarm.run_evidence_verifier(self.sample_case, claims)

        self.assertEqual(output["claims"][0]["evidence_status"], "UNSUPPORTED")
        self.assertIn("not found in corpus", str(output["claims"][0]["verifier_notes"]))

    def test_verifier_does_not_mutate_input(self) -> None:
        swarm = VerdionAgentSwarm()
        orig_claim = {
            "id": "claim_orig",
            "case_id": "scen_01",
            "case_version": 1,
            "agent_id": "agent_test",
            "claim_text": "Test statement",
            "claim_type": "STATUTORY_REQUIREMENT",
            "evidence_status": "ORIGINAL_STATUS",
            "evidence_refs": ["pas_gdpr_art6_1"],
            "supporting_passage_id": "pas_gdpr_art6_1",
            "supporting_sentence_index": 0,
            "assumptions": [],
            "timestamp": "2026-03-15T10:00:00Z",
        }
        claims = [orig_claim]
        output = swarm.run_evidence_verifier(self.sample_case, claims)

        # Original dict unchanged
        self.assertEqual(orig_claim["evidence_status"], "ORIGINAL_STATUS")
        # Output dict modified
        self.assertEqual(output["claims"][0]["evidence_status"], "SUPPORTED")

    # === QUANTITATIVE FORECASTER TESTS ===

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_fc")
    def test_forecaster_valid_output_measured_probability_and_priority_in_code(self, mock_digest: MagicMock) -> None:
        fc_payload = {
            "forecast": {
                "probability": 0.725,
                "event_definition": "Evaluator finds Article 6(4) compliance gap in AI fine-tuning.",
                "confidence_interval": [0.65, 0.80],
            },
            "uncertainty": {
                "score": 0.7,
                "impact": 0.85,
                "feasibility": 0.9,
                "priority": 0.999,  # Code computes: 0.85 * 0.7 * 0.9 = 0.5355 -> 0.536
                "rationale": "High compliance uncertainty",
            },
            "recommended_actions": ["Submit prediction market commitment"],
        }
        res = LLMResult(
            text=json.dumps(fc_payload),
            prompt_tokens=60,
            completion_tokens=30,
            latency_ms=180.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_quantitative_forecaster(self.sample_case)

        self.assertEqual(output["status"], "SUCCESS")
        self.assertEqual(output["role"], "QUANTITATIVE_FORECASTER")
        self.assertEqual(output["forecast"]["probability"], 0.725)
        self.assertEqual(output["uncertainty"]["priority"], 0.535)
        self.assertEqual(len(output["claims"]), 1)
        self.assertIn("0.7250", output["claims"][0]["claim_text"])

    @patch("ml.agents.agent_swarm.get_model_digest", return_value="mock_digest_fc")
    def test_forecaster_abstention_returns_abstained(self, mock_digest: MagicMock) -> None:
        abstain_payload = {
            "forecast": {
                "abstain": True,
                "reason": "Insufficient factual clarity on consent documentation.",
            },
            "uncertainty": {
                "score": 1.0,
                "impact": 0.8,
                "feasibility": 0.2,
                "rationale": "Facts insufficient to determine probability.",
            },
            "recommended_actions": ["Seek additional evidence via bounty"],
        }
        res = LLMResult(
            text=json.dumps(abstain_payload),
            prompt_tokens=40,
            completion_tokens=20,
            latency_ms=100.0,
            model="qwen2.5:7b-instruct",
            quantization="Q4_K_M",
        )
        mock_client = MockLLMClient([res])
        swarm = VerdionAgentSwarm(llm_client=mock_client)

        output = swarm.run_quantitative_forecaster(self.sample_case)

        self.assertEqual(output["status"], "ABSTAINED")
        self.assertIn("Insufficient factual clarity", str(output["error_details"]))

    # === COORDINATOR TESTS ===

    def test_coordinator_synthesizes_questions_without_inventing_and_ranks_priority(self) -> None:
        swarm = VerdionAgentSwarm()
        upstream_outputs = [
            {
                "role": "LEGAL_INTERPRETER",
                "uncertainty": {"score": 0.8, "impact": 0.9, "feasibility": 0.8, "rationale": "Is consent distinct for AI training?"},
                "counterarguments": ["Controller has legitimate interest under Article 6(1)(f)"],
                "claims": [
                    {
                        "claim_text": "Processing without safeguards may violate Art 6(4)",
                        "evidence_status": "UNRESOLVED_APPLICABILITY",
                    }
                ],
                "evidence_refs": ["pas_gdpr_art6_1"],
            },
            {
                "role": "ADVERSARIAL_RESEARCHER",
                "uncertainty": {"score": 0.4, "impact": 0.5, "feasibility": 0.5, "rationale": "Secondary purpose exceptions under Art 89"},
                "counterarguments": [],
                "claims": [],
                "evidence_refs": ["pas_gdpr_art89"],
            },
        ]

        output = swarm.run_coordinator(self.sample_case, upstream_outputs)

        self.assertEqual(output["status"], "SUCCESS")
        self.assertEqual(output["role"], "COORDINATOR")
        self.assertGreater(len(output["ranked_questions"]), 0)
        # Verify questions are sorted descending by priority
        priorities = [q["priority"] for q in output["ranked_questions"]]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        # Top priority corresponds to highest impact * uncertainty * feasibility
        self.assertEqual(output["uncertainty"]["priority"], priorities[0])
        # Verify evidence_refs aggregated
        self.assertIn("pas_gdpr_art6_1", output["evidence_refs"])
        self.assertIn("pas_gdpr_art89", output["evidence_refs"])


if __name__ == "__main__":
    unittest.main()

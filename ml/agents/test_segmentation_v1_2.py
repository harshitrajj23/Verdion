import unittest
from ml.agents.validator import (
    ClaimOutput,
    SentenceList,
    split_passage_into_sentences,
    verify_claim_quote,
)


class TestSegmentationV12(unittest.TestCase):
    def test_enumerated_subclause_splitting(self):
        # Statutory clause with enumerations (a), (b), (c)
        text = (
            "The controller shall implement appropriate technical and organisational measures: "
            "(a) the pseudonymisation and encryption of personal data; "
            "(b) the ability to ensure the ongoing confidentiality, integrity, availability and resilience of processing systems; "
            "(c) a process for regularly testing, assessing and evaluating the effectiveness of technical measures."
        )
        self.assertGreater(len(text.split()), 40)
        sents = split_passage_into_sentences(text, version="1.2.0")
        self.assertEqual(sents.splitter_version, "1.2.0")
        self.assertGreaterEqual(len(sents), 3)
        self.assertTrue(any("(a)" in s for s in sents))
        self.assertTrue(any("(b)" in s for s in sents))

    def test_statutory_proviso_splitting(self):
        # Long statutory clause > 60 words containing a proviso
        clause1 = "Personal data may be processed for archiving purposes in the public interest, scientific or historical research purposes or statistical purposes " * 3
        proviso = ", provided that technical and organisational measures are in place to safeguard the rights and freedoms of the data subject."
        full_text = clause1 + proviso
        self.assertGreater(len(full_text.split()), 60)

        sents = split_passage_into_sentences(full_text, version="1.2.0")
        self.assertGreater(len(sents), 1)
        self.assertTrue(any("provided that" in s for s in sents))

    def test_unverifiable_status_when_no_evidence_provided(self):
        passage_lookup = {
            "pas_gdpr_art6_1": {
                "passage_id": "pas_gdpr_art6_1",
                "content": "Processing shall be lawful only if and to the extent that at least one lawful basis applies.",
            }
        }
        status, notes = verify_claim_quote(
            evidence_refs=[],
            supporting_quote=None,
            supporting_passage_id=None,
            passage_lookup=passage_lookup,
        )
        self.assertEqual(status, "UNVERIFIABLE")
        self.assertIn("No source evidence provided", notes)

    def test_claim_output_accepts_unverifiable_status(self):
        claim_data = {
            "id": "claim_unverifiable_1",
            "case_id": "case_test",
            "case_version": 1,
            "agent_id": "agent_test",
            "claim_text": "High risk is suspected based on market rumors.",
            "claim_type": "HYPOTHESIS",
            "evidence_status": "UNVERIFIABLE",
            "timestamp": "2026-10-27T00:00:00Z",
            "evidence_refs": [],
            "assumptions": ["Unsubstantiated public reports"],
        }
        claim = ClaimOutput.from_dict(claim_data)
        self.assertEqual(claim.evidence_status, "UNVERIFIABLE")

    def test_verbatim_statutory_quote_up_to_100_words_supported(self):
        long_passage_text = " ".join(["statutory_word"] * 85) + "."
        passage_lookup = {
            "pas_long": {
                "passage_id": "pas_long",
                "content": long_passage_text,
            }
        }
        # In v1.1.0 with 60 words max, this would fail with SENTENCE_TOO_LONG
        status_v11, notes_v11 = verify_claim_quote(
            evidence_refs=["pas_long"],
            supporting_quote=long_passage_text,
            supporting_passage_id="pas_long",
            passage_lookup=passage_lookup,
            max_words=60,
        )
        self.assertEqual(status_v11, "UNSUPPORTED")
        self.assertIn("reason=SENTENCE_TOO_LONG", notes_v11)

        # In v1.2.0 with max_words=100, verbatim long clause is safely SUPPORTED
        status_v12, notes_v12 = verify_claim_quote(
            evidence_refs=["pas_long"],
            supporting_quote=long_passage_text,
            supporting_passage_id="pas_long",
            passage_lookup=passage_lookup,
            max_words=100,
            splitter_version="1.2.0",
        )
        self.assertEqual(status_v12, "SUPPORTED")
        self.assertIsNone(notes_v12)


if __name__ == "__main__":
    unittest.main()

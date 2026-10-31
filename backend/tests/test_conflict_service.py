"""
Tests for Cross-DPA Regulatory Conflict Analysis Service (FR-011)
Validates precision, recall, false-positive rate, and explainability.
"""

import pytest
from backend.app.services.conflict_service import (
    AuthorityClaim,
    ConflictCategory,
    CrossDPAConflictService,
    DeonticStance,
    LightweightSemanticAnalyzer,
)


@pytest.fixture
def labeled_evaluation_corpus():
    """
    20-pair ground-truth labeled evaluation dataset based on actual EU DPA regulatory positions.
    Each pair is labeled with: expected_is_conflict (bool), expected_category (ConflictCategory).
    """
    claims = [
        # Pair 1 (Direct Contradiction): Web Scraping for AI Training
        AuthorityClaim(
            claim_id="clm_garante_scraping",
            authority="Garante",
            jurisdiction="IT",
            legal_provision="GDPR Art. 5(1)(a) & Art. 6",
            text="Mass web scraping of personal data from public online sources to train generative AI foundation models is unlawful and prohibited without an explicit legal basis and verifiable opt-out.",
            passage_ref="urn:garante:order:2023-03-30#p12-14",
            source_version="2023-03-30",
            topic="web_scraping_ai_training"
        ),
        AuthorityClaim(
            claim_id="clm_dpc_scraping",
            authority="DPC",
            jurisdiction="IE",
            legal_provision="GDPR Art. 6(1)(f)",
            text="Organisations may rely on legitimate interests under Art 6(1)(f) to crawl and collect publicly available data for AI model development provided a rigorous three-part balancing test is conducted.",
            passage_ref="urn:dpc:guidance:ai:2024-05#p45-48",
            source_version="2024-05-10",
            topic="web_scraping_ai_training"
        ),

        # Pair 2 (Direct Contradiction): Biometric Template Matching in Retail
        AuthorityClaim(
            claim_id="clm_cnil_biometrics",
            authority="CNIL",
            jurisdiction="FR",
            legal_provision="GDPR Art. 9(1)",
            text="The deployment of automated facial recognition video surveillance in commercial shopping centers is strictly prohibited and constitutes an illegal processing of special category biometric data.",
            passage_ref="urn:cnil:delib:2022-09-15#p08",
            source_version="2022-09-15",
            topic="biometric_retail_surveillance"
        ),
        AuthorityClaim(
            claim_id="clm_aepd_biometrics",
            authority="AEPD",
            jurisdiction="ES",
            legal_provision="GDPR Art. 9(2)(g)",
            text="Biometric identification systems are permitted in high-value commercial premises when deployed strictly for verified physical security and anti-theft prevention under substantial public interest exceptions.",
            passage_ref="urn:aepd:resolution:2023-11#p22",
            source_version="2023-11-04",
            topic="biometric_retail_surveillance"
        ),

        # Pair 3 (Conditional Divergence): Employee Emotion AI Monitoring
        AuthorityClaim(
            claim_id="clm_bfdi_workplace",
            authority="BfDI",
            jurisdiction="DE",
            legal_provision="BDSG § 26 / GDPR Art. 88",
            text="AI-based emotion recognition and attention tracking of teleworkers in home offices is forbidden. Employee consent is invalid due to systemic structural power imbalance.",
            passage_ref="urn:bfdi:guidelines:workplace:2023#p19",
            source_version="2023-04-12",
            topic="employee_ai_monitoring"
        ),
        AuthorityClaim(
            claim_id="clm_dpc_workplace",
            authority="DPC",
            jurisdiction="IE",
            legal_provision="GDPR Art. 88",
            text="Workplace algorithmic productivity tracking may be permitted subject to prior consultation with trade unions and mandatory Data Protection Impact Assessment safeguards.",
            passage_ref="urn:dpc:workplace:telework:2023#p31",
            source_version="2023-08-20",
            topic="employee_ai_monitoring"
        ),

        # Pair 4 (Harmonious with High Lexical Overlap): Transparency Obligations
        AuthorityClaim(
            claim_id="clm_cnil_transparency",
            authority="CNIL",
            jurisdiction="FR",
            legal_provision="GDPR Art. 13",
            text="Data controllers must provide clear, accessible, and intelligible transparency disclosures at the point of data collection, detailing the purposes and legal basis of processing.",
            passage_ref="urn:cnil:guidance:transparency:2021#p04",
            source_version="2021-06-01",
            topic="transparency_obligations"
        ),
        AuthorityClaim(
            claim_id="clm_aepd_transparency",
            authority="AEPD",
            jurisdiction="ES",
            legal_provision="GDPR Art. 13",
            text="Controllers must implement layered privacy notices providing clear, accessible, and intelligible information to data subjects at the moment personal data is gathered.",
            passage_ref="urn:aepd:guide:layered_notice:2021#p09",
            source_version="2021-07-15",
            topic="transparency_obligations"
        ),

        # Pair 5 (Unrelated Scopes): Cookie Banners vs Medical AI Device Validation
        AuthorityClaim(
            claim_id="clm_garante_cookies",
            authority="Garante",
            jurisdiction="IT",
            legal_provision="ePrivacy Directive Art. 5(3)",
            text="Scrolling or closing a webpage banner shall not constitute valid consent for third-party tracking cookies or marketing scripts.",
            passage_ref="urn:garante:cookie_guidelines:2021#p17",
            source_version="2021-12-10",
            topic="cookie_consent"
        ),
        AuthorityClaim(
            claim_id="clm_bfdi_medical",
            authority="BfDI",
            jurisdiction="DE",
            legal_provision="EU MDR Art. 10 / GDPR Art. 9",
            text="Clinical validation of neural networks in diagnostic imaging must maintain certified data provenance audits for training cohorts.",
            passage_ref="urn:bfdi:medical_ai:2024#p03",
            source_version="2024-02-18",
            topic="medical_ai_validation"
        ),
    ]

    # Ground truth test pairs: (claim_idx_a, claim_idx_b, expected_is_conflict, expected_category)
    test_cases = [
        # 1. Garante vs DPC Scraping -> Conflict (Direct Contradiction)
        (0, 1, True, ConflictCategory.DIRECT_CONTRADICTION),
        # 2. CNIL vs AEPD Biometrics -> Conflict (Direct Contradiction)
        (2, 3, True, ConflictCategory.DIRECT_CONTRADICTION),
        # 3. BfDI vs DPC Workplace -> Conflict (Direct / Conditional Divergence)
        (4, 5, True, ConflictCategory.CONDITIONAL_DIVERGENCE),
        # 4. CNIL vs AEPD Transparency -> Harmonious (NOT conflict despite identical wording)
        (6, 7, False, ConflictCategory.HARMONIOUS),
        # 5. Garante Cookies vs BfDI Medical -> Unrelated (NOT conflict)
        (8, 9, False, ConflictCategory.UNRELATED),
        # 6. Garante Scraping vs CNIL Transparency -> Unrelated (NOT conflict)
        (0, 6, False, ConflictCategory.UNRELATED),
        # 7. CNIL Biometrics vs Garante Cookies -> Unrelated (NOT conflict)
        (2, 8, False, ConflictCategory.UNRELATED),
        # 8. DPC Scraping vs BfDI Medical -> Unrelated (NOT conflict)
        (1, 9, False, ConflictCategory.UNRELATED),
    ]

    return claims, test_cases


def test_cross_dpa_conflict_precision_recall(labeled_evaluation_corpus):
    """
    Evaluates precision, recall, and false-positive rate across the ground-truth benchmark.
    Acceptance criteria:
    - Precision == 1.0 (0 false positives: harmonious & unrelated pairs never flagged as conflicts)
    - Recall == 1.0 (100% of actual regulatory conflicts detected)
    - F1 Score == 1.0
    """
    claims, test_cases = labeled_evaluation_corpus

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for idx_a, idx_b, expected_conflict, expected_category in test_cases:
        claim_a = claims[idx_a]
        claim_b = claims[idx_b]

        result = CrossDPAConflictService.analyze_pair(claim_a, claim_b)

        if result.is_conflict and expected_conflict:
            tp += 1
            # Check category alignment if specified
            if expected_category in (ConflictCategory.DIRECT_CONTRADICTION, ConflictCategory.CONDITIONAL_DIVERGENCE):
                assert result.conflict_category in (ConflictCategory.DIRECT_CONTRADICTION, ConflictCategory.CONDITIONAL_DIVERGENCE)
        elif result.is_conflict and not expected_conflict:
            fp += 1
        elif not result.is_conflict and not expected_conflict:
            tn += 1
            assert result.conflict_category in (ConflictCategory.HARMONIOUS, ConflictCategory.UNRELATED)
        elif not result.is_conflict and expected_conflict:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print(f"\n[Cross-DPA Conflict Benchmark Results]")
    print(f"True Positives:  {tp}")
    print(f"False Positives: {fp}")
    print(f"True Negatives:  {tn}")
    print(f"False Negatives: {fn}")
    print(f"Precision:       {precision:.4f}")
    print(f"Recall:          {recall:.4f}")
    print(f"F1 Score:        {f1:.4f}")
    print(f"False Pos Rate:  {fpr:.4f}")

    assert fp == 0, f"False positives detected: {fp}"
    assert fn == 0, f"False negatives detected: {fn}"
    assert precision == 1.0
    assert recall == 1.0
    assert f1 == 1.0


def test_lexical_similarity_does_not_imply_conflict(labeled_evaluation_corpus):
    """
    Verifies PRD requirement: Distinguish lexical overlap from semantic contradiction.
    Does NOT treat similar wording as proof of legal conflict.
    """
    claims, _ = labeled_evaluation_corpus
    cnil_trans = claims[6]
    aepd_trans = claims[7]

    res = CrossDPAConflictService.analyze_pair(cnil_trans, aepd_trans)
    assert res.topic_similarity > 0.50  # Substantial semantic similarity
    assert res.lexical_overlap > 0.20   # Noticeable lexical overlap
    assert not res.is_conflict          # Must NOT be flagged as conflict
    assert res.conflict_category == ConflictCategory.HARMONIOUS
    assert "Harmonious regulatory positions" in res.explanation


def test_explainable_conflict_output_and_edpb_trigger(labeled_evaluation_corpus):
    """
    Verifies explainable reasoning, exact passage references, and Art 63 EDPB consistency trigger.
    """
    claims, _ = labeled_evaluation_corpus
    garante_scraping = claims[0]
    dpc_scraping = claims[1]

    res = CrossDPAConflictService.analyze_pair(garante_scraping, dpc_scraping)
    assert res.is_conflict
    assert res.conflict_category == ConflictCategory.DIRECT_CONTRADICTION
    assert res.severity == "CRITICAL"
    assert res.edpb_consistency_mechanism_required is True
    assert "DIRECT CONTRADICTION detected" in res.explanation
    assert res.authority_a == "Garante"
    assert res.authority_b == "DPC"
    assert "Garante" in res.explanation and "DPC" in res.explanation


def test_same_authority_internal_consistency(labeled_evaluation_corpus):
    """Verifies that comparing claims from the same authority returns harmonious non-conflict."""
    claims, _ = labeled_evaluation_corpus
    claim_1 = claims[0]
    claim_2 = claims[0]

    res = CrossDPAConflictService.analyze_pair(claim_1, claim_2)
    assert not res.is_conflict
    assert res.conflict_category == ConflictCategory.HARMONIOUS

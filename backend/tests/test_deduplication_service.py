"""
Tests for Hybrid Cryptographic & Semantic Deduplication Engine (PRD-SEC-006)
Validates exact SHA-256 matching, semantic duplicate filtering, human review flagging,
and preservation of distinct cross-jurisdictional analogues.
"""

import pytest
from backend.app.services.deduplication_service import (
    ActionRecommendation,
    DocumentPassage,
    DuplicateStatus,
    HybridDeduplicationService,
)


@pytest.fixture
def existing_corpus():
    return [
        DocumentPassage(
            passage_id="pass_gdpr_art13",
            text="Where personal data relating to a data subject are collected from the data subject, the controller shall, at the time when personal data are obtained, provide the data subject with all of the following information.",
            jurisdiction="EU",
            authority="EU Parliament / Council",
            source_uri="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
            version_or_date="2016-04-27"
        ),
        DocumentPassage(
            passage_id="pass_ai_act_art5",
            text="The following artificial intelligence practices shall be prohibited: the placing on the market, the putting into service or the use of an AI system that deploys subliminal techniques beyond a person's consciousness.",
            jurisdiction="EU",
            authority="EU Council",
            source_uri="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
            version_or_date="2024-06-13"
        )
    ]


def test_exact_sha256_duplicate_detection(existing_corpus):
    """Verifies that identical legal text triggers immediate SHA-256 idempotent skip."""
    service = HybridDeduplicationService(existing_corpus)

    identical_candidate = DocumentPassage(
        passage_id="pass_gdpr_art13_copy",
        text="Where personal data relating to a data subject are collected from the data subject, the controller shall, at the time when personal data are obtained, provide the data subject with all of the following information.",
        jurisdiction="EU",
        authority="EU Parliament / Council",
        source_uri="https://eur-lex.europa.eu/copy",
        version_or_date="2016-04-27"
    )

    res = service.evaluate_passage(identical_candidate)
    assert res.status == DuplicateStatus.EXACT_DUPLICATE
    assert res.action == ActionRecommendation.IDEMPOTENT_SKIP
    assert res.exact_hash_match is True
    assert res.similarity_score == 1.0
    assert res.matched_passage_id == "pass_gdpr_art13"


def test_semantic_duplicate_rejection(existing_corpus):
    """Verifies that minor whitespace and formatting differences trigger semantic duplicate rejection."""
    service = HybridDeduplicationService(existing_corpus)

    # Minor formatting and spacing variant
    paraphrased_candidate = DocumentPassage(
        passage_id="pass_gdpr_art13_reformatted",
        text="Where personal data relating to a data subject are collected from the data subject the controller shall at the time when personal data are obtained provide the data subject with all of the following information.",
        jurisdiction="EU",
        authority="EU DPA Mirror",
        source_uri="https://mirror.example.org/gdpr",
        version_or_date="2016-04-27"
    )

    res = service.evaluate_passage(paraphrased_candidate)
    assert res.status == DuplicateStatus.SEMANTIC_DUPLICATE
    assert res.action == ActionRecommendation.REJECT_REDUNDANT
    assert res.exact_hash_match is False
    assert res.similarity_score >= 0.92
    assert res.matched_passage_id == "pass_gdpr_art13"


def test_near_duplicate_uncertainty_flags_human_review(existing_corpus):
    """Verifies that an amended passage with substantial additions queues for human review without auto-deletion."""
    service = HybridDeduplicationService(existing_corpus)

    amended_candidate = DocumentPassage(
        passage_id="pass_ai_act_amended",
        text="The following artificial intelligence practices shall be prohibited: the placing on the market, putting into service or use of an AI system deploying subliminal techniques or purposeful biometric categorization.",
        jurisdiction="EU",
        authority="EU Commission Revision",
        source_uri="https://eur-lex.europa.eu/draft_amendment",
        version_or_date="2024-09-01"
    )

    res = service.evaluate_passage(amended_candidate)
    assert res.status == DuplicateStatus.NEAR_DUPLICATE_UNCERTAIN
    assert res.action == ActionRecommendation.FLAG_FOR_HUMAN_REVIEW
    assert res.requires_human_review is True
    assert 0.75 <= res.similarity_score < 0.92


def test_cross_jurisdiction_preserves_distinct_legal_analogue(existing_corpus):
    """
    Verifies PRD requirement: Avoid automatically deleting legally distinct documents across jurisdictions.
    California CCPA disclosure rule is similar in wording to GDPR Art 13, but must be accepted as distinct!
    """
    service = HybridDeduplicationService(existing_corpus)

    ccpa_candidate = DocumentPassage(
        passage_id="pass_ccpa_1798_100",
        text="A business that collects a consumer's personal information shall, at or before the point of collection, inform consumers as to the categories of personal information to be collected.",
        jurisdiction="US-CA",  # Distinct jurisdiction!
        authority="California Privacy Protection Agency",
        source_uri="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.100",
        version_or_date="2023-01-01"
    )

    res = service.evaluate_passage(ccpa_candidate)
    # Must NOT be deleted as a duplicate
    assert res.action != ActionRecommendation.REJECT_REDUNDANT
    assert res.action != ActionRecommendation.IDEMPOTENT_SKIP


def test_completely_distinct_passage_accepted(existing_corpus):
    """Verifies that unrelated legal provisions are accepted without review."""
    service = HybridDeduplicationService(existing_corpus)

    unrelated_candidate = DocumentPassage(
        passage_id="pass_trademark_rule",
        text="An applicant may file an application for registration of a trademark with the European Union Intellectual Property Office upon payment of the official fee.",
        jurisdiction="EU",
        authority="EUIPO",
        source_uri="https://euipo.europa.eu/rules",
        version_or_date="2022-01-01"
    )

    res = service.evaluate_passage(unrelated_candidate)
    assert res.status == DuplicateStatus.DISTINCT_CONTENT
    assert res.action == ActionRecommendation.ACCEPT
    assert res.similarity_score < 0.75
    assert res.requires_human_review is False


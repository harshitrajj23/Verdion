# VERIDION Phase 5K — Deliverable 03: 9-Dimensional Evidence Grounding Audit

## 1. Architecture Overview

Under **Option C**, mechanical citation and cryptographic hash matching are recognized as passage identity, not legal entailment proof. The `EvidenceGroundingService` evaluates claims across nine discrete, independent dimensions:

1. `PASSAGE_INTEGRITY`: SHA-256 digest match against statutory text.
2. `SOURCE_AUTHENTICITY`: Provenance verified against official gazettes (EUR-Lex, CJEU, EDPB).
3. `CITATION_VALIDITY`: Adherence to standardized statutory numbering syntax.
4. `QUOTATION_ACCURACY`: Exactness of direct quotation marks.
5. `SEMANTIC_SUPPORT`: Substantive lexical token overlap between proposition and legal passage.
6. `LEGAL_ENTAILMENT`: Deontic rule entailment structure (prohibition vs permission vs exception).
7. `FACT_TO_LAW_APPLICABILITY`: Substantive binding of declared case facts to statutory provisions.
8. `JURISDICTIONAL_VALIDITY`: Alignment between case jurisdiction and legal instrument authority.
9. `TEMPORAL_VALIDITY`: Statutory effective date vs assessment date.

## 2. Empirical Grounding Test Results

```json
{
  "valid_grounded_claim": {
    "overall_status": "VERIFIED",
    "is_fully_grounded": true,
    "dimension_scores": {
      "PASSAGE_INTEGRITY": 1.0,
      "SOURCE_AUTHENTICITY": 1.0,
      "CITATION_VALIDITY": 1.0,
      "QUOTATION_ACCURACY": 1.0,
      "SEMANTIC_SUPPORT": 0.652,
      "LEGAL_ENTAILMENT": 0.9,
      "FACT_TO_LAW_APPLICABILITY": 0.6,
      "JURISDICTIONAL_VALIDITY": 1.0,
      "TEMPORAL_VALIDITY": 1.0
    },
    "passed": true
  },
  "tampered_digest_attack": {
    "passage_integrity_status": "UNSUPPORTED",
    "is_fully_grounded": false,
    "defended": true
  },
  "jurisdiction_mismatch_attack": {
    "jurisdictional_validity_status": "CONTRADICTED",
    "is_fully_grounded": false,
    "defended": true
  },
  "temporal_effective_date_attack": {
    "temporal_validity_status": "CONTRADICTED",
    "is_fully_grounded": false,
    "defended": true
  }
}
```

## 3. Fail-Closed Security Properties

- **Tampered Hash Attack:** Modifying a single character of the SHA-256 passage digest caused immediate status `UNSUPPORTED`, `is_fully_grounded: False`.
- **Jurisdictional Mismatch Attack:** Citing California Civil Code in an EU GDPR assessment produced status `CONTRADICTED`, `is_fully_grounded: False`.
- **Temporal Future Law Attack:** Citing a statute with an effective date in 2030 produced status `CONTRADICTED`, `is_fully_grounded: False`.
- **Unverified Provenance Attack:** Providing unauthenticated web text produced status `UNVERIFIED`, triggering overall failure (`is_fully_grounded: False`).

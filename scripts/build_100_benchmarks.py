"""
Generates the versioned 100-scenario benchmark dataset for VERIDION Phase 5J
Splits:
- DEV: 30 scenarios
- VAL: 30 scenarios
- TEST: 40 scenarios (Held-out)
"""

import json
from pathlib import Path

scenarios = []

# Base templates covering GDPR, EU AI Act, CPRA
templates = [
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 5(1)(b)",
        "jur": "EU",
        "facts_base": {"data_categories": ["customer chat transcripts"], "processing_purpose": "secondary AI model improvement", "user_consent_obtained": False, "secondary_ai_training": True},
        "issues": ["PURPOSE_LIMITATION_BREACH"],
        "gap": 1,
        "defense": "LEGITIMATE_INTEREST_DEFENSE"
    },
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 5(1)(e)",
        "jur": "EU",
        "facts_base": {"data_categories": ["server access logs"], "processing_purpose": "security telemetry", "retention_policy": "indefinite", "deletion_mechanism": "none"},
        "issues": ["STORAGE_LIMITATION_VIOLATION"],
        "gap": 1,
        "defense": "LEGAL_OBLIGATION_DEFENSE"
    },
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 9(1)",
        "jur": "EU",
        "facts_base": {"data_categories": ["biometric face embeddings", "health survey records"], "processing_purpose": "wellness classification", "special_category_data": True, "explicit_consent_obtained": False},
        "issues": ["SPECIAL_CATEGORY_CONSENT_MISSING"],
        "gap": 1,
        "defense": "PUBLIC_HEALTH_EXEMPTION"
    },
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 22",
        "jur": "EU",
        "facts_base": {"data_categories": ["loan repayment history"], "processing_purpose": "credit scoring", "solely_automated_decision": True, "human_in_the_loop": False},
        "issues": ["AUTOMATED_DECISION_MAKING_VIOLATION"],
        "gap": 1,
        "defense": "CONTRACT_NECESSITY_DEFENSE"
    },
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 13",
        "jur": "EU",
        "facts_base": {"data_categories": ["support audio clips"], "processing_purpose": "quality assurance", "user_notice_provided": False},
        "issues": ["INADEQUATE_NOTICE_FOR_AI_TRAINING"],
        "gap": 1,
        "defense": "PROPORTIONALITY_DEFENSE"
    },
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 17",
        "jur": "EU",
        "facts_base": {"data_categories": ["user profile records"], "processing_purpose": "account management", "erasure_pipeline_implemented": False, "deletion_mechanism": "manual_ticket"},
        "issues": ["ABSENT_ERASURE_PIPELINE"],
        "gap": 1,
        "defense": "FREEDOM_OF_EXPRESSION_EXEMPTION"
    },
    {
        "inst": "EU_AI_ACT",
        "prov": "EU AI Act Art. 50",
        "jur": "EU",
        "facts_base": {"data_categories": ["synthetic conversational audio"], "processing_purpose": "customer avatar synthesis", "ai_watermark_present": False, "ai_transparency_notice": False},
        "issues": ["AI_ACT_TRANSPARENCY_BREACH"],
        "gap": 1,
        "defense": "ARTISTIC_FREEDOM_EXEMPTION"
    },
    {
        "inst": "CPRA",
        "prov": "CPRA §1798.120",
        "jur": "California",
        "facts_base": {"data_categories": ["browsing telemetry", "device identifiers"], "processing_purpose": "targeted ad bidding", "opt_out_link_present": False, "sale_of_data": True},
        "issues": ["MISSING_OPT_OUT_MECHANISM"],
        "gap": 1,
        "defense": "SERVICE_PROVIDER_SAFE_HARBOR"
    },
    # Compliant scenarios (Gap = 0)
    {
        "inst": "GDPR",
        "prov": "GDPR Art. 6(1)(a)",
        "jur": "EU",
        "facts_base": {"data_categories": ["user feedback"], "processing_purpose": "feature enhancement", "user_consent_obtained": True, "user_notice_provided": True, "retention_policy": "90 days", "deletion_mechanism": "automated_ttl"},
        "issues": [],
        "gap": 0,
        "defense": "NONE_REQUIRED"
    },
    {
        "inst": "CPRA",
        "prov": "CPRA §1798.100",
        "jur": "California",
        "facts_base": {"data_categories": ["order history"], "processing_purpose": "fulfillment", "opt_out_link_present": True, "user_notice_provided": True, "retention_policy": "1 year"},
        "issues": [],
        "gap": 0,
        "defense": "NONE_REQUIRED"
    }
]

# Generate 100 variations across sectors and domains
domains = ["fintech", "healthcare", "e-commerce", "telecom", "automotive", "gaming", "edtech", "recruiting", "hospitality", "logistics"]

idx = 1
for d_idx, domain in enumerate(domains):
    for t_idx, t in enumerate(templates):
        # Determine split: 1-30 DEV, 31-60 VAL, 61-100 TEST
        if idx <= 30:
            split = "DEV"
        elif idx <= 60:
            split = "VAL"
        else:
            split = "TEST"

        facts = dict(t["facts_base"])
        facts["industry_domain"] = domain
        facts["system_name"] = f"{domain.capitalize()}Core_v{d_idx+1}"
        facts["assessment_date"] = "2026-10-31"

        # Varied uncertainty
        unc = 0.20 if t["gap"] == 0 else (0.35 if "AI" in t["inst"] else 0.45)

        scen = {
            "id": f"scen_100_{idx:03d}",
            "split": split,
            "title": f"{domain.capitalize()} {t['inst']} Compliance Assessment {t_idx+1}",
            "jurisdiction": t["jur"],
            "legal_instrument": t["inst"],
            "legal_provision": t["prov"],
            "question": f"Does the {domain} system comply with {t['prov']} regarding {facts['processing_purpose']}?",
            "facts": facts,
            "ground_truth_issues": t["issues"],
            "expected_counterarguments": [t["defense"]] if t["defense"] != "NONE_REQUIRED" else [],
            "expected_uncertainty": unc,
            "ground_truth_gap_outcome": t["gap"],
            "provenance": "EXPERT_CURATED_SYNTHETIC",
            "dataset_version": "benchmark_100_v1.0", "rubric": f"Evaluation of {t['inst']} {t['prov']} compliance for {domain} processing operations."
        }
        scenarios.append(scen)
        idx += 1

print(f"Generated {len(scenarios)} scenarios.")
dev_count = sum(1 for s in scenarios if s["split"] == "DEV")
val_count = sum(1 for s in scenarios if s["split"] == "VAL")
test_count = sum(1 for s in scenarios if s["split"] == "TEST")
print(f"Splits: DEV={dev_count}, VAL={val_count}, TEST={test_count}")

# Save to backend/data/
p1 = Path("Verdion/backend/data/benchmark_100_scenarios.json")
p2 = Path("backend/data/benchmark_100_scenarios.json")
p1.parent.mkdir(parents=True, exist_ok=True)
p2.parent.mkdir(parents=True, exist_ok=True)

with open(p1, "w", encoding="utf-8") as f:
    json.dump(scenarios, f, indent=2)
with open(p2, "w", encoding="utf-8") as f:
    json.dump(scenarios, f, indent=2)

print("Saved benchmark_100_scenarios.json successfully.")

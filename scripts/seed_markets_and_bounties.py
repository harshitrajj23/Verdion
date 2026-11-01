import asyncio
import sys
from datetime import datetime, timezone, timedelta

# Project setup
sys.path.insert(0, '.')
from backend.app.core.database import configure_database
from backend.app.models.entities import Base, Case, PredictionMarket, EvidenceBounty, EvidenceSubmission
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

raw_url = 'postgresql://neondb_owner:npg_Buj7CH1kvREP@ep-red-sunset-a1nfpyki-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
db_url, engine_args = configure_database(raw_url)

async def seed_data():
    engine = create_async_engine(db_url, **engine_args)
    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        # Check existing cases
        cases_res = await session.execute(select(Case))
        cases = cases_res.scalars().all()
        if not cases:
            print("No cases found in DB to link markets/bounties to!")
            return
            
        case_map = {c.id: c for c in cases}
        now = datetime.now(timezone.utc)
        print(f"Found {len(cases)} cases in Neon DB.")

        # Seed 3 Prediction Markets
        markets_data = [
            {
                "id": "market_biometric_article9",
                "case_id": "case_80e48a90c5" if "case_80e48a90c5" in case_map else cases[0].id,
                "case_version": 1,
                "question": "Will EDPB issue binding guidance that facial templates for workplace access violate Article 9 without explicit consent?",
                "outcome_definition": "Resolves YES (1) if EDPB or CJEU holds facial template storage unlawful under Article 9(1) absent Article 9(2)(a) explicit consent.",
                "resolution_method": "AUTHORITATIVE_REGULATORY_DECISION",
                "rubric_version": "1.0",
                "commit_deadline": now + timedelta(days=7),
                "reveal_deadline": now + timedelta(days=9),
                "resolution_deadline": now + timedelta(days=30),
                "challenge_window_seconds": 86400,
                "scoring_version": "brier_v1",
                "void_criteria": "Case settled without published reasoning or regulatory statute repealed.",
                "status": "PUBLISHED",
                "contract_address": "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
                "evaluator_address": "0x1234567890123456789012345678901234567890",
                "aggregate_probability": 0.78,
                "disagreement_variance": 0.024,
                "sample_size": 6,
                "created_at": now
            },
            {
                "id": "market_llm_purpose_limitation",
                "case_id": "case_cb9c731ab2" if "case_cb9c731ab2" in case_map else cases[0].id,
                "case_version": 1,
                "question": "Will training commercial foundation models on customer support transcripts be ruled a secondary purpose violation under Article 5(1)(b)?",
                "outcome_definition": "Resolves YES (1) if DPA or CJEU holds foundation model pre-training incompatible with primary support ticketing purpose.",
                "resolution_method": "AUTHORITATIVE_REGULATORY_DECISION",
                "rubric_version": "1.0",
                "commit_deadline": now + timedelta(days=5),
                "reveal_deadline": now + timedelta(days=7),
                "resolution_deadline": now + timedelta(days=45),
                "challenge_window_seconds": 86400,
                "scoring_version": "brier_v1",
                "void_criteria": "Commercial use case altered or exempted under EU AI Act grandfathering.",
                "status": "REVEAL",
                "contract_address": "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
                "evaluator_address": "0x1234567890123456789012345678901234567890",
                "aggregate_probability": 0.65,
                "disagreement_variance": 0.038,
                "sample_size": 6,
                "created_at": now
            },
            {
                "id": "market_telemetry_third_country",
                "case_id": "case_36fa5853bc" if "case_36fa5853bc" in case_map else cases[0].id,
                "case_version": 1,
                "question": "Will unencrypted telemetry cloud transfers to third countries without adequacy decision violate Article 44 GDPR?",
                "outcome_definition": "Resolves YES (1) if supervisory authority imposes fine or corrective order under Article 58(2).",
                "resolution_method": "AUTHORITATIVE_REGULATORY_DECISION",
                "rubric_version": "1.0",
                "commit_deadline": now - timedelta(days=10),
                "reveal_deadline": now - timedelta(days=8),
                "resolution_deadline": now - timedelta(days=1),
                "challenge_window_seconds": 86400,
                "scoring_version": "brier_v1",
                "void_criteria": "Adequacy decision granted retroactively.",
                "status": "SETTLED",
                "proposed_outcome": 1,
                "resolution_reference": "EDPB Binding Decision 02/2026",
                "contract_address": "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
                "evaluator_address": "0x1234567890123456789012345678901234567890",
                "aggregate_probability": 0.85,
                "disagreement_variance": 0.015,
                "sample_size": 6,
                "created_at": now - timedelta(days=14)
            }
        ]

        for m_data in markets_data:
            existing_m = await session.get(PredictionMarket, m_data["id"])
            if not existing_m:
                session.add(PredictionMarket(**m_data))
                print(f"Added Prediction Market: {m_data['id']}")
            else:
                print(f"Prediction Market already exists: {m_data['id']}")

        # Seed 3 Evidence Bounties
        bounties_data = [
            {
                "id": "bounty_biometric_proportionality",
                "case_id": "case_80e48a90c5" if "case_80e48a90c5" in case_map else cases[0].id,
                "question": "Provide verified National DPA enforcement decision regarding biometric workplace access proportionality.",
                "acceptance_criteria": "Must include official regulatory case citation, verified publication date, and deterministic SHA-256 passage hash.",
                "reward_amount": 250.0,
                "deadline": now + timedelta(days=14),
                "challenge_window_seconds": 86400,
                "status": "OPEN",
                "contract_reference": "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
                "creator_address": "0x0987654321098765432109876543210987654321",
                "created_at": now
            },
            {
                "id": "bounty_llm_unlearning_audit",
                "case_id": "case_cb9c731ab2" if "case_cb9c731ab2" in case_map else cases[0].id,
                "question": "Submit technical implementation proof of exact user consent revocation in LLM fine-tuning weights.",
                "acceptance_criteria": "Verified technical architecture paper or audited enterprise implementation proving Article 17 erasure compliance.",
                "reward_amount": 500.0,
                "deadline": now + timedelta(days=21),
                "challenge_window_seconds": 86400,
                "status": "OPEN",
                "contract_reference": "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
                "creator_address": "0x0987654321098765432109876543210987654321",
                "created_at": now
            },
            {
                "id": "bounty_telemetry_encryption_proof",
                "case_id": "case_36fa5853bc" if "case_36fa5853bc" in case_map else cases[0].id,
                "question": "Submit cryptographically verifiable cipher suite specification for cross-border telemetry transit.",
                "acceptance_criteria": "NIST post-quantum cryptographic cipher implementation with independent third-party audit verification.",
                "reward_amount": 150.0,
                "deadline": now - timedelta(days=2),
                "challenge_window_seconds": 86400,
                "status": "AWARDED",
                "contract_reference": "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
                "winning_submission_id": "sub_quantum_safe_audit_01",
                "creator_address": "0x0987654321098765432109876543210987654321",
                "created_at": now - timedelta(days=12)
            }
        ]

        for b_data in bounties_data:
            existing_b = await session.get(EvidenceBounty, b_data["id"])
            if not existing_b:
                session.add(EvidenceBounty(**b_data))
                print(f"Added Evidence Bounty: {b_data['id']}")
            else:
                print(f"Evidence Bounty already exists: {b_data['id']}")

        await session.commit()
        print("Successfully committed all Prediction Markets and Evidence Bounties to Neon PostgreSQL!")

    await engine.dispose()

asyncio.run(seed_data())


import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.crypto import compute_uncertainty_priority
from backend.app.models.entities import ArgumentEdge, Claim, ClaimEvidenceLink, utcnow


class ArgumentService:
    """Manages the structured Argument Graph, edge dependencies, and conflict detection."""

    @staticmethod
    async def create_claim(
        db: AsyncSession,
        case_id: str,
        case_version: int,
        agent_id: str,
        claim_text: str,
        claim_type: str,
        assumptions: List[str],
        confidence: float,
        confidence_rationale: str,
        status: str = "SUPPORTED"
    ) -> Claim:
        claim_id = f"clm_{uuid.uuid4().hex[:10]}"
        claim = Claim(
            id=claim_id,
            case_id=case_id,
            case_version=case_version,
            agent_id=agent_id,
            claim_text=claim_text,
            claim_type=claim_type,
            assumptions=assumptions,
            confidence_metadata={
                "score": confidence,
                "rationale": confidence_rationale
            },
            status=status,
            timestamp=utcnow()
        )
        db.add(claim)
        await db.flush()
        return claim

    @staticmethod
    async def link_evidence(
        db: AsyncSession,
        claim_id: str,
        evidence_id: str,
        relationship_type: str = "SUPPORTS",
        verification_status: str = "VERIFIED",
        relationship: Optional[str] = None
    ) -> ClaimEvidenceLink:
        rel = relationship or relationship_type
        link_id = f"link_{uuid.uuid4().hex[:10]}"
        link = ClaimEvidenceLink(
            id=link_id,
            claim_id=claim_id,
            evidence_id=evidence_id,
            relationship_type=rel,
            verification_status=verification_status
        )
        db.add(link)
        await db.flush()
        return link

    @staticmethod
    async def create_edge(
        db: AsyncSession,
        case_id: str,
        source_claim_id: str,
        target_claim_id: str,
        relationship_type: str = "SUPPORTS",
        reason: str = "Dialectic argument relationship",
        edge_type: Optional[str] = None,
        weight: Optional[float] = None
    ) -> ArgumentEdge:
        rel = edge_type or relationship_type
        edge_reason = reason or (f"Relationship weight: {weight}" if weight is not None else "Dialectic argument relationship")
        edge_id = f"edge_{uuid.uuid4().hex[:10]}"
        edge = ArgumentEdge(
            id=edge_id,
            case_id=case_id,
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            relationship_type=rel,
            reason=edge_reason,
            timestamp=utcnow()
        )
        db.add(edge)
        await db.flush()
        return edge

    @staticmethod
    async def get_argument_graph(db: AsyncSession, case_id: str) -> Dict[str, Any]:
        """Returns the full argument graph (claims, evidence links, edges, conflicts)."""
        # Fetch claims
        claims_stmt = select(Claim).where(Claim.case_id == case_id)
        claims_res = await db.execute(claims_stmt)
        claims = claims_res.scalars().all()

        claim_ids = [c.id for c in claims]

        # Fetch evidence links
        links_stmt = select(ClaimEvidenceLink).where(ClaimEvidenceLink.claim_id.in_(claim_ids)) if claim_ids else None
        links = []
        if links_stmt is not None:
            links_res = await db.execute(links_stmt)
            links = links_res.scalars().all()

        # Fetch edges
        edges_stmt = select(ArgumentEdge).where(ArgumentEdge.case_id == case_id)
        edges_res = await db.execute(edges_stmt)
        edges = edges_res.scalars().all()

        # Identify conflicts (edges of type CONTRADICTS)
        conflicts = [
            {
                "edge_id": e.id,
                "source_claim_id": e.source_claim_id,
                "target_claim_id": e.target_claim_id,
                "reason": e.reason,
                "timestamp": e.timestamp.isoformat()
            }
            for e in edges if e.relationship_type == "CONTRADICTS"
        ]

        return {
            "case_id": case_id,
            "claims": [
                {
                    "id": c.id,
                    "agent_id": c.agent_id,
                    "claim_text": c.claim_text,
                    "claim_type": c.claim_type,
                    "assumptions": c.assumptions,
                    "confidence": c.confidence_metadata.get("score", 0.0),
                    "status": c.status,
                    "timestamp": c.timestamp.isoformat()
                }
                for c in claims
            ],
            "evidence_links": [
                {
                    "id": l.id,
                    "claim_id": l.claim_id,
                    "evidence_id": l.evidence_id,
                    "relationship_type": l.relationship_type,
                    "verification_status": l.verification_status
                }
                for l in links
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_claim_id": e.source_claim_id,
                    "target_claim_id": e.target_claim_id,
                    "relationship_type": e.relationship_type,
                    "reason": e.reason,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in edges
            ],
            "conflicts": conflicts
        }

    @staticmethod
    def rank_uncertainties(uncertainties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ranks uncertainties using Priority(q) = Impact(q) * Uncertainty(q) * ResearchFeasibility(q)."""
        ranked = []
        for u in uncertainties:
            priority = compute_uncertainty_priority(
                impact=u.get("impact", 0.5),
                uncertainty=u.get("uncertainty", 0.5),
                research_feasibility=u.get("research_feasibility", 0.5)
            )
            item = dict(u)
            item["priority_score"] = priority
            item["recommended_bounty"] = priority >= 0.25
            ranked.append(item)

        ranked.sort(key=lambda x: x["priority_score"], reverse=True)
        return ranked

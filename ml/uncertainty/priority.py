from typing import Dict, Any, List

class UncertaintyPrioritizer:
    """
    Ranks unresolved legal questions using the PRD §9.4 heuristic:
    Priority(q) = Impact(q) * Uncertainty(q) * ResearchFeasibility(q)
    with factors bounded in [0, 1] (FR-023).
    """

    @staticmethod
    def calculate_priority(impact: float, uncertainty: float, feasibility: float) -> float:
        """Computes normalized priority score in [0.0, 1.0]."""
        # Clamp inputs between 0 and 1
        i = max(0.0, min(1.0, float(impact)))
        u = max(0.0, min(1.0, float(uncertainty)))
        f = max(0.0, min(1.0, float(feasibility)))
        return round(i * u * f, 4)

    @classmethod
    def rank_questions(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates priority for each question and returns them sorted in descending priority order.
        """
        ranked = []
        for q in questions:
            impact = q.get("impact", 0.5)
            uncertainty = q.get("uncertainty", 0.5)
            feasibility = q.get("feasibility", 0.5)
            priority = cls.calculate_priority(impact, uncertainty, feasibility)

            ranked.append({
                "id": q.get("id"),
                "question": q.get("question"),
                "impact": impact,
                "uncertainty": uncertainty,
                "feasibility": feasibility,
                "priority": priority,
                "suggests_bounty": priority >= 0.35, # Bounty recommended if high-impact uncertainty is resolvable
                "recommended_bounty_credits": int(priority * 200)
            })

        ranked.sort(key=lambda x: x["priority"], reverse=True)
        return ranked

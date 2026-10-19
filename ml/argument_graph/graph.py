from typing import List, Dict, Any, Optional
from enum import Enum

class EdgeType(str, Enum):
    SUPPORT = "SUPPORT"
    CONTRADICTION = "CONTRADICTION"
    QUALIFY = "QUALIFY"
    DEPEND_ON = "DEPEND_ON"
    SUPERSEDE = "SUPERSEDE"

class ArgumentGraph:
    """
    Structured argument graph engine tracking claims, evidence, assumptions,
    and typed relationship edges (FR-019..FR-022, §16.4).
    """

    def __init__(self, case_id: str, case_version: int = 1):
        self.case_id = case_id
        self.case_version = case_version
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def add_claim_node(
        self,
        claim_id: str,
        claim_text: str,
        claim_type: str,
        agent_id: str,
        evidence_status: str = "SUPPORTED",
        evidence_refs: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Adds a claim node to the argument graph (FR-019)."""
        node = {
            "id": claim_id,
            "type": "CLAIM",
            "claim_type": claim_type,
            "text": claim_text,
            "agent_id": agent_id,
            "evidence_status": evidence_status,
            "evidence_refs": evidence_refs or [],
            "assumptions": assumptions or [],
            "case_id": self.case_id,
            "case_version": self.case_version
        }
        self.nodes[claim_id] = node
        return node

    def add_evidence_node(
        self,
        evidence_id: str,
        document_id: str,
        passage_reference: str,
        content: str,
        digest: str,
        authority: str,
        effective_date: str
    ) -> Dict[str, Any]:
        """Adds an evidence node with cryptographic digest and authority metadata."""
        node = {
            "id": evidence_id,
            "type": "EVIDENCE",
            "document_id": document_id,
            "passage_reference": passage_reference,
            "text": content,
            "digest": digest,
            "authority": authority,
            "effective_date": effective_date,
            "case_id": self.case_id,
            "case_version": self.case_version
        }
        self.nodes[evidence_id] = node
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: EdgeType,
        reason: str
    ) -> Dict[str, Any]:
        """Adds a directed typed edge between nodes (FR-020)."""
        if source_id not in self.nodes:
            raise ValueError(f"Source node {source_id} not found in graph")
        if target_id not in self.nodes:
            raise ValueError(f"Target node {target_id} not found in graph")

        edge = {
            "id": f"edge_{source_id}_{target_id}_{relationship.value}",
            "source": source_id,
            "target": target_id,
            "relationship": relationship.value,
            "reason": reason
        }
        self.edges.append(edge)
        return edge

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Surfaces contradictory edges and incompatible claim pairs (FR-022)."""
        conflicts = []
        for edge in self.edges:
            if edge["relationship"] == EdgeType.CONTRADICTION.value:
                conflicts.append({
                    "edge_id": edge["id"],
                    "source_claim": self.nodes[edge["source"]],
                    "target_claim": self.nodes[edge["target"]],
                    "reason": edge["reason"]
                })
        return conflicts

    def to_dict(self) -> Dict[str, Any]:
        """Serializes graph to JSON-compatible dictionary."""
        return {
            "case_id": self.case_id,
            "case_version": self.case_version,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "conflicts": self.detect_conflicts()
        }

    def to_accessible_table(self) -> List[Dict[str, Any]]:
        """
        Produces an accessible text/table representation for screen-readers
        and accessibility fallbacks (§16.4).
        """
        table_rows = []
        for edge in self.edges:
            src = self.nodes.get(edge["source"], {})
            tgt = self.nodes.get(edge["target"], {})
            table_rows.append({
                "source_id": edge["source"],
                "source_label": src.get("text", "")[:80] + ("..." if len(src.get("text", "")) > 80 else ""),
                "relationship": edge["relationship"],
                "target_id": edge["target"],
                "target_label": tgt.get("text", "")[:80] + ("..." if len(tgt.get("text", "")) > 80 else ""),
                "rationale": edge["reason"]
            })
        return table_rows

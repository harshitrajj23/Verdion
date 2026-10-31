"use client";

import React, { useState } from "react";
import { GraphNode, GraphEdge } from "@/lib/types";
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  Table as TableIcon,
  Network,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  Info
} from "lucide-react";

interface ArgumentGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const ArgumentGraph: React.FC<ArgumentGraphProps> = ({ nodes, edges }) => {
  const [viewMode, setViewMode] = useState<"visual" | "table">("visual");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("n_claim_purpose");
  const [searchQuery, setSearchQuery] = useState("");

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];

  const filteredNodes = nodes.filter(
    (n) =>
      n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (n.details && n.details.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Layout node positions in an interactive 2D layout
  const nodePositions: Record<string, { x: number; y: number }> = {
    n_claim_purpose: { x: 380, y: 160 },
    n_claim_legit_interest: { x: 140, y: 320 },
    n_claim_retention_gap: { x: 620, y: 320 },
    n_evi_art6_4: { x: 220, y: 55 },
    n_evi_edpb_stmt: { x: 540, y: 55 },
    n_assumption_unredacted: { x: 380, y: 385 }
  };

  const edgeColors: Record<string, { stroke: string; label: string; badge: string }> = {
    SUPPORT: { stroke: "#10b981", label: "Supports", badge: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    CONTRADICTION: { stroke: "#e11d48", label: "Contradicts", badge: "bg-rose-50 text-rose-700 border-rose-200" },
    QUALIFY: { stroke: "#d97706", label: "Qualifies", badge: "bg-amber-50 text-amber-700 border-amber-200" },
    DEPEND_ON: { stroke: "#FF8FB1", label: "Depends On", badge: "bg-bubblegum-soft text-bubblegum-deep border border-hairline" },
    SUPERSEDE: { stroke: "#8b5cf6", label: "Supersedes", badge: "bg-purple-50 text-purple-700 border-purple-200" }
  };

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-[16px] bg-white border border-hairline shadow-soft">
        {/* Segmented Control */}
        <div className="inline-flex p-1 rounded-full bg-cloud border border-hairline">
          <button
            onClick={() => setViewMode("visual")}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs transition-all ${
              viewMode === "visual"
                ? "bg-bubblegum text-white shadow-soft font-semibold"
                : "text-muted hover:text-ink font-medium"
            }`}
          >
            <Network className={`w-3.5 h-3.5 ${viewMode === "visual" ? "text-white" : "text-bubblegum"}`} />
            <span>Visual Graph</span>
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs transition-all ${
              viewMode === "table"
                ? "bg-bubblegum text-white shadow-soft font-semibold"
                : "text-muted hover:text-ink font-medium"
            }`}
            title="Full screen-reader accessible text & table fallback (§16.4)"
          >
            <TableIcon className={`w-3.5 h-3.5 ${viewMode === "table" ? "text-white" : "text-bubblegum"}`} />
            <span>Accessible Table Fallback (§16.4)</span>
          </button>
        </div>

        {/* Legend Chips */}
        <div className="hidden md:flex items-center gap-3 text-xs text-ink-secondary font-medium">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Support
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Contradiction
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Qualify
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-lavender-600"></span> Depend-On
          </span>
        </div>
      </div>

      {viewMode === "visual" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* SVG Canvas (2 cols) */}
          <div className="lg:col-span-2 relative h-[520px] rounded-[18px] border border-cream-300 bg-[#FDFCF9] overflow-hidden shadow-apple-card">
            <svg className="w-full h-full" viewBox="0 0 760 460">
              <defs>
                <marker
                  id="arrow-SUPPORT"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                </marker>
                <marker
                  id="arrow-CONTRADICTION"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#e11d48" />
                </marker>
                <marker
                  id="arrow-QUALIFY"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#d97706" />
                </marker>
                <marker
                  id="arrow-DEPEND_ON"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#6e50bd" />
                </marker>
              </defs>

              {/* Draw Edges */}
              {edges.map((edge) => {
                const src = nodePositions[edge.source] || { x: 100, y: 100 };
                const tgt = nodePositions[edge.target] || { x: 300, y: 300 };
                const color = edgeColors[edge.relationship]?.stroke || "#94a3b8";

                return (
                  <g key={edge.id} className="cursor-pointer group">
                    <line
                      x1={src.x}
                      y1={src.y}
                      x2={tgt.x}
                      y2={tgt.y}
                      stroke={color}
                      strokeWidth="2.5"
                      strokeDasharray={edge.relationship === "QUALIFY" ? "5,5" : "none"}
                      markerEnd={`url(#arrow-${edge.relationship})`}
                      className="opacity-75 group-hover:opacity-100 transition-opacity"
                    />
                  </g>
                );
              })}

              {/* Draw Nodes */}
              {nodes.map((node) => {
                const pos = nodePositions[node.id] || { x: 200, y: 200 };
                const isSelected = selectedNodeId === node.id;

                const nodeBg =
                  node.type === "EVIDENCE"
                    ? "#ECFDF5" // soft emerald
                    : node.type === "ASSUMPTION"
                    ? "#FEF3C7" // soft amber
                    : "#F1ECFB"; // soft lavender

                const nodeStroke =
                  isSelected
                    ? "#6E50BD"
                    : node.type === "EVIDENCE"
                    ? "#10B981"
                    : node.type === "ASSUMPTION"
                    ? "#F59E0B"
                    : "#A78BFA";

                const textFill =
                  node.type === "EVIDENCE"
                    ? "#065F46"
                    : node.type === "ASSUMPTION"
                    ? "#92400E"
                    : "#5A3EA2";

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="cursor-pointer transition-transform hover:scale-105"
                  >
                    {isSelected && (
                      <circle
                        r="32"
                        fill="none"
                        stroke="#6E50BD"
                        strokeWidth="1.5"
                        strokeDasharray="3 3"
                        className="animate-spin-slow opacity-60"
                      />
                    )}
                    <circle
                      r={isSelected ? "26" : "22"}
                      fill={nodeBg}
                      stroke={nodeStroke}
                      strokeWidth={isSelected ? "3" : "2"}
                      className="transition-all drop-shadow-sm"
                    />
                    <text
                      textAnchor="middle"
                      dy="4"
                      fill={textFill}
                      fontSize="10"
                      fontWeight="bold"
                      className="pointer-events-none select-none"
                    >
                      {node.type === "EVIDENCE" ? "EVI" : node.type === "ASSUMPTION" ? "ASM" : "CLM"}
                    </text>
                    <text
                      textAnchor="middle"
                      dy="38"
                      fill="#635E6B"
                      fontSize="10"
                      fontWeight="600"
                      className="pointer-events-none select-none max-w-[130px]"
                    >
                      {node.label.slice(0, 22)}...
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Inspector Panel */}
          <div className="p-6 rounded-[18px] border border-cream-300 bg-white shadow-apple-card space-y-4">
            <div className="flex items-start justify-between gap-2 border-b border-cream-200 pb-3.5">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-cream-200 text-ink-secondary font-semibold">
                  {selectedNode.type}
                </span>
                <h3 className="text-sm font-bold text-ink mt-1.5 leading-snug">
                  {selectedNode.label}
                </h3>
              </div>
              {selectedNode.evidence_status && (
                <span
                  className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${
                    selectedNode.evidence_status === "SUPPORTED"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : selectedNode.evidence_status === "CONTRADICTED"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : "bg-amber-50 text-amber-700 border-amber-200"
                  }`}
                >
                  {selectedNode.evidence_status}
                </span>
              )}
            </div>

            <div className="space-y-3.5 text-xs">
              {selectedNode.details && (
                <div>
                  <span className="text-ink-secondary font-semibold block mb-1">Details & Rationale</span>
                  <p className="text-ink leading-relaxed bg-cream-50 p-3 rounded-[12px] border border-cream-200">
                    {selectedNode.details}
                  </p>
                </div>
              )}

              {selectedNode.agent && (
                <div className="flex items-center justify-between text-ink-secondary py-0.5">
                  <span>Asserting Agent:</span>
                  <span className="font-semibold text-ink">{selectedNode.agent}</span>
                </div>
              )}

              {selectedNode.authority && (
                <div className="flex items-center justify-between text-ink-secondary py-0.5">
                  <span>Authoritative Body:</span>
                  <span className="font-semibold text-emerald-700">{selectedNode.authority}</span>
                </div>
              )}

              {selectedNode.effective_date && (
                <div className="flex items-center justify-between text-ink-secondary py-0.5">
                  <span>Effective Date:</span>
                  <span className="font-mono text-ink">{selectedNode.effective_date}</span>
                </div>
              )}

              {selectedNode.digest && (
                <div>
                  <span className="text-ink-secondary font-semibold block mb-1">Cryptographic Digest</span>
                  <div className="p-2.5 rounded-[12px] bg-cream-100 border border-cream-200 font-mono text-[11px] text-lavender-700 break-all">
                    {selectedNode.digest}
                  </div>
                </div>
              )}

              {/* Connected Relationships */}
              <div className="pt-3 border-t border-cream-200">
                <span className="text-ink-secondary font-semibold block mb-2">Connected Relationships:</span>
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e) => {
                      const rel = edgeColors[e.relationship];
                      const isOutgoing = e.source === selectedNode.id;
                      const otherId = isOutgoing ? e.target : e.source;
                      const otherNode = nodes.find((n) => n.id === otherId);

                      return (
                        <div
                          key={e.id}
                          onClick={() => setSelectedNodeId(otherId)}
                          className="p-2.5 rounded-[12px] bg-cream-50 hover:bg-lavender-50 border border-cream-200 hover:border-lavender-200 cursor-pointer flex items-center justify-between text-xs group transition-colors"
                        >
                          <div className="space-y-0.5">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${rel?.badge}`}>
                              {rel?.label}
                            </span>
                            <p className="text-ink font-medium line-clamp-1 group-hover:text-lavender-700">
                              {otherNode?.label}
                            </p>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-ink-tertiary group-hover:text-lavender-700 shrink-0" />
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Accessible Table Fallback View (§16.4) */
        <div className="rounded-[18px] border border-cream-300 bg-white overflow-hidden shadow-apple-card">
          <div className="p-4 sm:p-5 border-b border-cream-200 bg-cream-50 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-ink">Argument Claims & Evidence Register</h3>
              <p className="text-xs text-ink-secondary">Structured tabular breakdown of all graph entities and dependencies.</p>
            </div>
            <input
              type="text"
              placeholder="Filter claims or evidence..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-4 py-2 rounded-full bg-white border border-cream-300 text-xs text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-lavender-600 w-64 shadow-apple-sm"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-cream-200 bg-cream-100 text-ink-secondary font-semibold uppercase tracking-wider text-[10px]">
                  <th className="p-3.5">Node ID</th>
                  <th className="p-3.5">Type</th>
                  <th className="p-3.5">Claim / Evidence Text</th>
                  <th className="p-3.5">Asserted By</th>
                  <th className="p-3.5">Verification State</th>
                  <th className="p-3.5">Digest / Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cream-200">
                {filteredNodes.map((node) => (
                  <tr
                    key={node.id}
                    onClick={() => {
                      setSelectedNodeId(node.id);
                      setViewMode("visual");
                    }}
                    className="hover:bg-cream-50 transition-colors cursor-pointer"
                  >
                    <td className="p-3.5 font-mono text-[11px] text-lavender-700 font-semibold">{node.id}</td>
                    <td className="p-3.5">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-cream-200 text-ink-secondary border border-cream-300">
                        {node.type}
                      </span>
                    </td>
                    <td className="p-3.5 font-medium text-ink max-w-md">{node.label}</td>
                    <td className="p-3.5 text-ink-secondary">{node.agent || node.authority || "Protocol Core"}</td>
                    <td className="p-3.5">
                      {node.evidence_status ? (
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                            node.evidence_status === "SUPPORTED"
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : node.evidence_status === "CONTRADICTED"
                              ? "bg-rose-50 text-rose-700 border-rose-200"
                              : "bg-amber-50 text-amber-700 border-amber-200"
                          }`}
                        >
                          {node.evidence_status}
                        </span>
                      ) : (
                        <span className="text-ink-tertiary">N/A</span>
                      )}
                    </td>
                    <td className="p-3.5 font-mono text-[11px] text-ink-secondary">
                      {node.digest ? `${node.digest.slice(0, 10)}...` : "Off-chain reference"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

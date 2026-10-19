"use client";

import React, { useState } from "react";
import { GraphNode, GraphEdge } from "@/lib/mockData";
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
    n_evi_art6_4: { x: 220, y: 50 },
    n_evi_edpb_stmt: { x: 540, y: 50 },
    n_assumption_unredacted: { x: 380, y: 380 }
  };

  const edgeColors: Record<string, { stroke: string; label: string; badge: string }> = {
    SUPPORT: { stroke: "#10b981", label: "Supports", badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" },
    CONTRADICTION: { stroke: "#f43f5e", label: "Contradicts", badge: "bg-rose-500/20 text-rose-300 border-rose-500/40" },
    QUALIFY: { stroke: "#f59e0b", label: "Qualifies", badge: "bg-amber-500/20 text-amber-300 border-amber-500/40" },
    DEPEND_ON: { stroke: "#6366f1", label: "Depends On", badge: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40" },
    SUPERSEDE: { stroke: "#a855f7", label: "Supersedes", badge: "bg-purple-500/20 text-purple-300 border-purple-500/40" }
  };

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode("visual")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === "visual"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-glow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Visual Graph</span>
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === "table"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-glow"
                : "text-slate-400 hover:text-white"
            }`}
            title="Full screen-reader accessible text & table fallback (§16.4)"
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>Accessible Table Fallback (§16.4)</span>
          </button>
        </div>

        {/* Legend */}
        <div className="hidden md:flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Support
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Contradiction
          </span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Qualify
          </span>
          <span className="flex items-center gap-1.5 text-indigo-400">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Depend-On
          </span>
        </div>
      </div>

      {viewMode === "visual" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* SVG Canvas (2 cols) */}
          <div className="lg:col-span-2 relative h-[500px] rounded-2xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-inner">
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
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
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
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
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
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />
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
                      className="opacity-70 group-hover:opacity-100 transition-opacity"
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
                    ? "#064e3b" // Dark emerald
                    : node.type === "ASSUMPTION"
                    ? "#451a03" // Dark amber
                    : "#0f172a"; // Slate

                const nodeStroke =
                  isSelected
                    ? "#38bdf8"
                    : node.type === "EVIDENCE"
                    ? "#10b981"
                    : node.type === "ASSUMPTION"
                    ? "#f59e0b"
                    : "#6366f1";

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="cursor-pointer transition-transform hover:scale-105"
                  >
                    <circle
                      r={isSelected ? "26" : "22"}
                      fill={nodeBg}
                      stroke={nodeStroke}
                      strokeWidth={isSelected ? "3.5" : "2"}
                      className="transition-all drop-shadow-md"
                    />
                    <text
                      textAnchor="middle"
                      dy="4"
                      fill="#f8fafc"
                      fontSize="10"
                      fontWeight="bold"
                      className="pointer-events-none select-none"
                    >
                      {node.type === "EVIDENCE" ? "EVI" : node.type === "ASSUMPTION" ? "ASM" : "CLM"}
                    </text>
                    <text
                      textAnchor="middle"
                      dy="38"
                      fill="#94a3b8"
                      fontSize="9"
                      fontWeight="500"
                      className="pointer-events-none select-none max-w-[120px]"
                    >
                      {node.label.slice(0, 22)}...
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Inspector Panel */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md space-y-4">
            <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {selectedNode.type}
                </span>
                <h3 className="text-sm font-bold text-white mt-1.5 leading-snug">
                  {selectedNode.label}
                </h3>
              </div>
              {selectedNode.evidence_status && (
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    selectedNode.evidence_status === "SUPPORTED"
                      ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                      : selectedNode.evidence_status === "CONTRADICTED"
                      ? "bg-rose-950 text-rose-300 border-rose-500/40"
                      : "bg-amber-950 text-amber-300 border-amber-500/40"
                  }`}
                >
                  {selectedNode.evidence_status}
                </span>
              )}
            </div>

            <div className="space-y-3 text-xs">
              {selectedNode.details && (
                <div>
                  <span className="text-slate-400 font-semibold block mb-1">Details & Rationale</span>
                  <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                    {selectedNode.details}
                  </p>
                </div>
              )}

              {selectedNode.agent && (
                <div className="flex items-center justify-between text-slate-400">
                  <span>Asserting Agent:</span>
                  <span className="font-semibold text-slate-200">{selectedNode.agent}</span>
                </div>
              )}

              {selectedNode.authority && (
                <div className="flex items-center justify-between text-slate-400">
                  <span>Authoritative Body:</span>
                  <span className="font-semibold text-emerald-400">{selectedNode.authority}</span>
                </div>
              )}

              {selectedNode.effective_date && (
                <div className="flex items-center justify-between text-slate-400">
                  <span>Effective Date:</span>
                  <span className="font-mono text-slate-200">{selectedNode.effective_date}</span>
                </div>
              )}

              {selectedNode.digest && (
                <div>
                  <span className="text-slate-400 font-semibold block mb-1">Cryptographic Digest</span>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800 font-mono text-[10px] text-cyan-400 break-all">
                    {selectedNode.digest}
                  </div>
                </div>
              )}

              {/* Connected Relationships */}
              <div className="pt-2 border-t border-slate-800">
                <span className="text-slate-400 font-semibold block mb-2">Connected Relationships:</span>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
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
                          className="p-2 rounded-lg bg-slate-950/50 hover:bg-slate-800/50 border border-slate-800 cursor-pointer flex items-center justify-between text-[11px] group transition-colors"
                        >
                          <div className="space-y-0.5">
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${rel?.badge}`}>
                              {rel?.label}
                            </span>
                            <p className="text-slate-300 line-clamp-1 group-hover:text-white">
                              {otherNode?.label}
                            </p>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-200 shrink-0" />
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
        <div className="rounded-2xl border border-slate-800 bg-slate-950/90 overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Argument Claims & Evidence Register</h3>
              <p className="text-xs text-slate-400">Structured tabular breakdown of all graph entities and dependencies.</p>
            </div>
            <input
              type="text"
              placeholder="Filter claims or evidence..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 w-64"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="p-3">Node ID</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Claim / Evidence Text</th>
                  <th className="p-3">Asserted By</th>
                  <th className="p-3">Verification State</th>
                  <th className="p-3">Digest / Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredNodes.map((node) => (
                  <tr
                    key={node.id}
                    onClick={() => {
                      setSelectedNodeId(node.id);
                      setViewMode("visual");
                    }}
                    className="hover:bg-slate-900/40 transition-colors cursor-pointer"
                  >
                    <td className="p-3 font-mono text-[11px] text-cyan-400">{node.id}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                        {node.type}
                      </span>
                    </td>
                    <td className="p-3 font-medium text-slate-200 max-w-md">{node.label}</td>
                    <td className="p-3 text-slate-400">{node.agent || node.authority || "Protocol Core"}</td>
                    <td className="p-3">
                      {node.evidence_status ? (
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                            node.evidence_status === "SUPPORTED"
                              ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                              : node.evidence_status === "CONTRADICTED"
                              ? "bg-rose-950 text-rose-300 border-rose-500/40"
                              : "bg-amber-950 text-amber-300 border-amber-500/40"
                          }`}
                        >
                          {node.evidence_status}
                        </span>
                      ) : (
                        <span className="text-slate-500">N/A</span>
                      )}
                    </td>
                    <td className="p-3 font-mono text-[10px] text-slate-500">
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

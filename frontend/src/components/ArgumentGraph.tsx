"use client";

import React, { useState, useMemo } from "react";
import { GraphNode, GraphEdge } from "@/lib/types";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Table as TableIcon,
  Network,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Copy,
  Check,
  Search,
  Filter,
  Sparkles,
  Layers,
  ArrowRight
} from "lucide-react";

interface ArgumentGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const ArgumentGraph: React.FC<ArgumentGraphProps> = ({ nodes, edges }) => {
  const [viewMode, setViewMode] = useState<"visual" | "table">("visual");
  const [selectedNodeId, setSelectedNodeId] = useState<string>(
    nodes[0]?.id || "n_claim_purpose"
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<"ALL" | "CLAIM" | "EVIDENCE" | "ASSUMPTION" | "CONTRADICTIONS">("ALL");
  const [zoom, setZoom] = useState<number>(1.0);
  const [copiedDigest, setCopiedDigest] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Selected node reference
  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || nodes[0] || {
      id: "none",
      type: "CLAIM",
      label: "No node selected"
    };
  }, [nodes, selectedNodeId]);

  // Layout node coordinates: fixed canonical positions for primary nodes + organic radial distribution for dynamic nodes
  const nodePositions = useMemo(() => {
    const posMap: Record<string, { x: number; y: number }> = {
      n_claim_purpose: { x: 420, y: 250 },
      n_claim_legit_interest: { x: 200, y: 390 },
      n_claim_retention_gap: { x: 640, y: 380 },
      n_evi_art6_4: { x: 230, y: 105 },
      n_evi_edpb_stmt: { x: 420, y: 75 },
      n_evi_cjeu_c300: { x: 650, y: 120 },
      n_claim_research_exemption: { x: 130, y: 240 },
      n_assumption_unredacted: { x: 420, y: 440 }
    };

    // Calculate dynamic layout for any nodes that don't have hardcoded coordinates
    nodes.forEach((node, index) => {
      if (!posMap[node.id]) {
        const angle = (index / Math.max(1, nodes.length)) * 2 * Math.PI - Math.PI / 2;
        const radius = node.type === "CLAIM" ? 180 : node.type === "EVIDENCE" ? 270 : 330;
        posMap[node.id] = {
          x: Math.round(420 + Math.cos(angle) * radius),
          y: Math.round(260 + Math.sin(angle) * radius * 0.72)
        };
      }
    });

    return posMap;
  }, [nodes]);

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      const matchesSearch =
        n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (n.details && n.details.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (n.authority && n.authority.toLowerCase().includes(searchQuery.toLowerCase()));

      if (!matchesSearch) return false;

      if (typeFilter === "ALL") return true;
      if (typeFilter === "CONTRADICTIONS") return n.evidence_status === "CONTRADICTED";
      return n.type === typeFilter;
    });
  }, [nodes, searchQuery, typeFilter]);

  // Contradiction count
  const contradictionCount = useMemo(() => {
    return edges.filter((e) => e.relationship === "CONTRADICTION").length;
  }, [edges]);

  // Edge theme definitions
  const edgeColors: Record<string, { stroke: string; label: string; badge: string; bg: string }> = {
    SUPPORT: {
      stroke: "#10b981",
      label: "Supports",
      badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
      bg: "#10b981"
    },
    CONTRADICTION: {
      stroke: "#f43f5e",
      label: "Contradicts",
      badge: "bg-rose-50 text-rose-700 border-rose-200",
      bg: "#f43f5e"
    },
    QUALIFY: {
      stroke: "#f59e0b",
      label: "Qualifies",
      badge: "bg-amber-50 text-amber-700 border-amber-200",
      bg: "#f59e0b"
    },
    DEPEND_ON: {
      stroke: "#FF8FB1",
      label: "Depends On",
      badge: "bg-bubblegum-soft text-bubblegum-deep border border-hairline",
      bg: "#FF8FB1"
    },
    SUPERSEDE: {
      stroke: "#8b5cf6",
      label: "Supersedes",
      badge: "bg-purple-50 text-purple-700 border-purple-200",
      bg: "#8b5cf6"
    }
  };

  const copyDigestToClipboard = (digest: string) => {
    navigator.clipboard.writeText(digest);
    setCopiedDigest(true);
    setTimeout(() => setCopiedDigest(false), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-[20px] bg-white border border-hairline shadow-soft">
        {/* Left: View Mode Toggle & Search */}
        <div className="flex flex-wrap items-center gap-3">
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

          {/* Quick Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search claims, evidence, authority..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-full bg-cloud border border-hairline text-ink placeholder:text-muted focus:outline-none focus:border-bubblegum w-56 transition-all"
            />
          </div>
        </div>

        {/* Right: Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <button
            onClick={() => setTypeFilter("ALL")}
            className={`px-3 py-1 rounded-full font-medium transition-all ${
              typeFilter === "ALL"
                ? "bg-ink text-white shadow-sm"
                : "bg-cloud text-muted hover:text-ink border border-hairline"
            }`}
          >
            All ({nodes.length})
          </button>
          <button
            onClick={() => setTypeFilter("CLAIM")}
            className={`px-3 py-1 rounded-full font-medium transition-all ${
              typeFilter === "CLAIM"
                ? "bg-bubblegum text-white shadow-sm"
                : "bg-bubblegum-soft text-bubblegum-deep border border-hairline hover:bg-bubblegum-hover hover:text-white"
            }`}
          >
            Claims ({nodes.filter((n) => n.type === "CLAIM").length})
          </button>
          <button
            onClick={() => setTypeFilter("EVIDENCE")}
            className={`px-3 py-1 rounded-full font-medium transition-all ${
              typeFilter === "EVIDENCE"
                ? "bg-emerald-600 text-white shadow-sm"
                : "bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
            }`}
          >
            Evidence ({nodes.filter((n) => n.type === "EVIDENCE").length})
          </button>
          <button
            onClick={() => setTypeFilter("ASSUMPTION")}
            className={`px-3 py-1 rounded-full font-medium transition-all ${
              typeFilter === "ASSUMPTION"
                ? "bg-amber-500 text-white shadow-sm"
                : "bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100"
            }`}
          >
            Assumptions ({nodes.filter((n) => n.type === "ASSUMPTION").length})
          </button>
          {contradictionCount > 0 && (
            <button
              onClick={() => setTypeFilter("CONTRADICTIONS")}
              className={`px-3 py-1 rounded-full font-medium transition-all flex items-center gap-1 ${
                typeFilter === "CONTRADICTIONS"
                  ? "bg-rose-600 text-white shadow-sm"
                  : "bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
              Contradictions ({contradictionCount})
            </button>
          )}
        </div>
      </div>

      {viewMode === "visual" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Main Visual SVG Canvas (8 cols) */}
          <div className="lg:col-span-8 relative rounded-[22px] border border-hairline bg-gradient-to-b from-[#FFFDFB] to-[#FFF6F9] overflow-hidden shadow-soft">
            {/* Canvas Action Bar */}
            <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-white/90 backdrop-blur-md p-1.5 rounded-full border border-hairline shadow-soft">
              <button
                onClick={() => setZoom((z) => Math.min(1.8, z + 0.15))}
                title="Zoom In"
                className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-cloud text-ink transition-colors"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoom((z) => Math.max(0.65, z - 0.15))}
                title="Zoom Out"
                className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-cloud text-ink transition-colors"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <div className="w-[1px] h-4 bg-hairline"></div>
              <button
                onClick={() => setZoom(1.0)}
                title="Reset View"
                className="px-2.5 h-7 flex items-center gap-1 rounded-full hover:bg-cloud text-[11px] font-medium text-ink transition-colors"
              >
                <RotateCcw className="w-3 h-3 text-muted" />
                <span>Fit</span>
              </button>
            </div>

            {/* Bottom Status & Legend Overlay */}
            <div className="absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-2 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-full border border-hairline shadow-soft text-[11px] text-muted">
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Support
              </span>
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Contradiction
              </span>
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Qualify
              </span>
              <span className="flex items-center gap-1.5 font-medium text-ink">
                <span className="w-2.5 h-2.5 rounded-full bg-bubblegum"></span> Depends-On
              </span>
            </div>

            {/* Interactive SVG Canvas */}
            <div className="w-full h-[540px] flex items-center justify-center select-none overflow-hidden cursor-grab active:cursor-grabbing">
              <svg
                className="w-full h-full transition-transform duration-300"
                viewBox="0 0 840 540"
                style={{ transform: `scale(${zoom})` }}
              >
                <defs>
                  {/* Subtle Blueprint Dot Grid */}
                  <pattern id="dot-grid" width="24" height="24" patternUnits="userSpaceOnUse">
                    <circle cx="12" cy="12" r="1.1" fill="#E8D7DF" opacity="0.6" />
                  </pattern>

                  {/* Edge Arrow Markers */}
                  <marker
                    id="arrow-SUPPORT"
                    viewBox="0 0 10 10"
                    refX="24"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="#10b981" />
                  </marker>
                  <marker
                    id="arrow-CONTRADICTION"
                    viewBox="0 0 10 10"
                    refX="24"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="#f43f5e" />
                  </marker>
                  <marker
                    id="arrow-QUALIFY"
                    viewBox="0 0 10 10"
                    refX="24"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="#f59e0b" />
                  </marker>
                  <marker
                    id="arrow-DEPEND_ON"
                    viewBox="0 0 10 10"
                    refX="24"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="#FF8FB1" />
                  </marker>
                  <marker
                    id="arrow-SUPERSEDE"
                    viewBox="0 0 10 10"
                    refX="24"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="#8b5cf6" />
                  </marker>

                  {/* Gradient Node Fills */}
                  <linearGradient id="grad-claim" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FFF1F5" />
                    <stop offset="100%" stopColor="#FFE4EE" />
                  </linearGradient>
                  <linearGradient id="grad-evidence" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#F0FDF4" />
                    <stop offset="100%" stopColor="#DCFCE7" />
                  </linearGradient>
                  <linearGradient id="grad-assumption" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FFFBEB" />
                    <stop offset="100%" stopColor="#FEF3C7" />
                  </linearGradient>
                </defs>

                {/* Background Grid */}
                <rect width="840" height="540" fill="url(#dot-grid)" />

                {/* Central Protocol Shield Watermark */}
                <circle cx="420" cy="270" r="160" fill="none" stroke="#F5DCE6" strokeWidth="1" strokeDasharray="4 6" opacity="0.4" />
                <circle cx="420" cy="270" r="280" fill="none" stroke="#F5DCE6" strokeWidth="1" strokeDasharray="4 6" opacity="0.25" />

                {/* Draw Edges */}
                {edges.map((edge) => {
                  const src = nodePositions[edge.source] || { x: 200, y: 200 };
                  const tgt = nodePositions[edge.target] || { x: 420, y: 260 };
                  const isHighlighted =
                    selectedNodeId === edge.source ||
                    selectedNodeId === edge.target ||
                    hoveredNodeId === edge.source ||
                    hoveredNodeId === edge.target;

                  const colorInfo = edgeColors[edge.relationship] || {
                    stroke: "#94a3b8",
                    label: edge.relationship,
                    badge: "bg-slate-50 text-slate-700",
                    bg: "#94a3b8"
                  };

                  // Calculate smooth curved cubic bezier
                  const dx = tgt.x - src.x;
                  const dy = tgt.y - src.y;
                  const midX = (src.x + tgt.x) / 2;
                  const midY = (src.y + tgt.y) / 2;
                  // Curvature offset perpendicular to slope
                  const curvature = 0.12;
                  const ctrlX = midX - dy * curvature;
                  const ctrlY = midY + dx * curvature;

                  return (
                    <g key={edge.id} className="cursor-pointer group">
                      {/* Glow line when connected */}
                      {isHighlighted && (
                        <path
                          d={`M ${src.x} ${src.y} Q ${ctrlX} ${ctrlY} ${tgt.x} ${tgt.y}`}
                          fill="none"
                          stroke={colorInfo.stroke}
                          strokeWidth="6"
                          opacity="0.3"
                          className="transition-all"
                        />
                      )}
                      {/* Base edge line */}
                      <path
                        d={`M ${src.x} ${src.y} Q ${ctrlX} ${ctrlY} ${tgt.x} ${tgt.y}`}
                        fill="none"
                        stroke={colorInfo.stroke}
                        strokeWidth={isHighlighted ? "2.75" : "2.0"}
                        strokeDasharray={
                          edge.relationship === "CONTRADICTION"
                            ? "4 4"
                            : edge.relationship === "QUALIFY"
                            ? "6 4"
                            : "none"
                        }
                        markerEnd={`url(#arrow-${edge.relationship})`}
                        opacity={isHighlighted ? 1 : 0.65}
                        className="transition-all group-hover:opacity-100"
                      />

                      {/* Edge Midpoint Relationship Label Badge */}
                      <g transform={`translate(${ctrlX}, ${ctrlY})`}>
                        <rect
                          x="-32"
                          y="-9"
                          width="64"
                          height="18"
                          rx="9"
                          fill="#FFFFFF"
                          stroke={colorInfo.stroke}
                          strokeWidth="1.2"
                          className="drop-shadow-xs"
                        />
                        <text
                          textAnchor="middle"
                          dy="3.5"
                          fill={colorInfo.stroke}
                          fontSize="8.5"
                          fontWeight="700"
                          className="select-none pointer-events-none uppercase tracking-wider"
                        >
                          {edge.relationship === "CONTRADICTION" ? "CONTRADICTS" : colorInfo.label}
                        </text>
                      </g>
                    </g>
                  );
                })}

                {/* Draw Nodes */}
                {nodes.map((node) => {
                  const pos = nodePositions[node.id] || { x: 420, y: 260 };
                  const isSelected = selectedNodeId === node.id;
                  const isHovered = hoveredNodeId === node.id;

                  // Visual stylings based on node type
                  const isEvidence = node.type === "EVIDENCE";
                  const isAssumption = node.type === "ASSUMPTION";

                  const fillGrad = isEvidence
                    ? "url(#grad-evidence)"
                    : isAssumption
                    ? "url(#grad-assumption)"
                    : "url(#grad-claim)";

                  const strokeColor = isSelected
                    ? "#E8567F"
                    : isEvidence
                    ? "#10B981"
                    : isAssumption
                    ? "#F59E0B"
                    : "#FF8FB1";

                  const badgeText = isEvidence ? "EVI" : isAssumption ? "ASM" : "CLM";
                  const textFill = isEvidence ? "#047857" : isAssumption ? "#B45309" : "#BE185D";

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onClick={() => setSelectedNodeId(node.id)}
                      onMouseEnter={() => setHoveredNodeId(node.id)}
                      onMouseLeave={() => setHoveredNodeId(null)}
                      className="cursor-pointer transition-transform duration-200"
                    >
                      {/* Selection Aura */}
                      {isSelected && (
                        <circle
                          r="36"
                          fill="none"
                          stroke="#FF8FB1"
                          strokeWidth="2"
                          strokeDasharray="4 4"
                          className="animate-spin"
                          style={{ animationDuration: "14s" }}
                          opacity="0.8"
                        />
                      )}

                      {/* Main Node Bubble */}
                      <circle
                        r={isSelected ? "26" : "23"}
                        fill={fillGrad}
                        stroke={strokeColor}
                        strokeWidth={isSelected ? "3" : "2"}
                        className="transition-all drop-shadow-sm group-hover:drop-shadow-md"
                      />

                      {/* Status indicator dot */}
                      {node.evidence_status && (
                        <circle
                          cx="16"
                          cy="-16"
                          r="5"
                          fill={
                            node.evidence_status === "SUPPORTED"
                              ? "#10B981"
                              : node.evidence_status === "CONTRADICTED"
                              ? "#F43F5E"
                              : "#F59E0B"
                          }
                          stroke="#FFFFFF"
                          strokeWidth="1.5"
                        />
                      )}

                      {/* Type Acronym Icon */}
                      <text
                        textAnchor="middle"
                        dy="4"
                        fill={textFill}
                        fontSize="10"
                        fontWeight="800"
                        className="pointer-events-none select-none tracking-tight font-mono"
                      >
                        {badgeText}
                      </text>

                      {/* Node Label Card */}
                      <g transform="translate(0, 36)">
                        <rect
                          x="-65"
                          y="-8"
                          width="130"
                          height="20"
                          rx="10"
                          fill={isSelected ? "#2A1F26" : "#FFFFFF"}
                          stroke={isSelected ? "#E8567F" : "#F5DCE6"}
                          strokeWidth="1"
                          className="drop-shadow-xs"
                        />
                        <text
                          textAnchor="middle"
                          dy="5"
                          fill={isSelected ? "#FFFFFF" : "#2A1F26"}
                          fontSize="9.5"
                          fontWeight="600"
                          className="pointer-events-none select-none"
                        >
                          {node.label.length > 22 ? `${node.label.slice(0, 20)}...` : node.label}
                        </text>
                      </g>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Right Inspector Drawer (4 cols) */}
          <div className="lg:col-span-4 rounded-[22px] border border-hairline bg-white p-5 shadow-soft space-y-4">
            {/* Inspector Header */}
            <div className="border-b border-hairline pb-4">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-cloud text-ink border border-hairline">
                  {selectedNode.type}
                </span>

                {selectedNode.evidence_status && (
                  <span
                    className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${
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

              <h3 className="text-base font-bold text-ink leading-snug">
                {selectedNode.label}
              </h3>
            </div>

            {/* Inspector Body Details */}
            <div className="space-y-3.5 text-xs">
              {/* Rationale Box */}
              {selectedNode.details && (
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-muted uppercase tracking-wider">
                    Statutory Analysis & Rationale
                  </span>
                  <p className="text-ink text-xs leading-relaxed bg-cloud p-3 rounded-[14px] border border-hairline">
                    {selectedNode.details}
                  </p>
                </div>
              )}

              {/* Agent Attribution */}
              {selectedNode.agent && (
                <div className="flex items-center justify-between p-2.5 rounded-[12px] bg-cloud/50 border border-hairline text-xs">
                  <span className="text-muted">Asserting Agent:</span>
                  <span className="font-semibold text-ink font-mono">{selectedNode.agent}</span>
                </div>
              )}

              {/* Legal Authority Source */}
              {selectedNode.authority && (
                <div className="flex items-center justify-between p-2.5 rounded-[12px] bg-emerald-50/60 border border-emerald-200/60 text-xs">
                  <span className="text-emerald-800 font-medium">Authoritative Reference:</span>
                  <span className="font-bold text-emerald-900">{selectedNode.authority}</span>
                </div>
              )}

              {/* Effective Statutory Date */}
              {selectedNode.effective_date && (
                <div className="flex items-center justify-between p-2.5 rounded-[12px] bg-cloud/50 border border-hairline text-xs">
                  <span className="text-muted">Temporal Horizon:</span>
                  <span className="font-semibold text-ink">{selectedNode.effective_date}</span>
                </div>
              )}

              {/* Cryptographic SHA-256 Digest */}
              {selectedNode.digest && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-muted uppercase tracking-wider">
                      Canonical Digest (SHA-256)
                    </span>
                    <button
                      onClick={() => copyDigestToClipboard(selectedNode.digest!)}
                      className="flex items-center gap-1 text-bubblegum-deep hover:text-bubblegum font-medium transition-colors"
                    >
                      {copiedDigest ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-600" />
                          <span className="text-emerald-600">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy Digest</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-2.5 rounded-[12px] bg-cloud border border-hairline font-mono text-[11px] text-bubblegum-deep break-all select-all">
                    {selectedNode.digest}
                  </div>
                </div>
              )}

              {/* Connected Relationships List */}
              <div className="pt-3 border-t border-hairline space-y-2">
                <span className="text-[11px] font-semibold text-muted uppercase tracking-wider block">
                  Connected Dialectic Edges ({edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).length})
                </span>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e) => {
                      const rel = edgeColors[e.relationship] || {
                        label: e.relationship,
                        badge: "bg-slate-50 text-slate-700 border-slate-200"
                      };
                      const isOutgoing = e.source === selectedNode.id;
                      const otherId = isOutgoing ? e.target : e.source;
                      const otherNode = nodes.find((n) => n.id === otherId);

                      return (
                        <div
                          key={e.id}
                          onClick={() => setSelectedNodeId(otherId)}
                          className="p-2.5 rounded-[14px] bg-cloud/60 hover:bg-bubblegum-soft/50 border border-hairline hover:border-bubblegum cursor-pointer transition-all group"
                        >
                          <div className="flex items-center justify-between gap-1.5 mb-1">
                            <span className={`px-2 py-0.5 rounded-full text-[9.5px] font-bold border uppercase tracking-wider ${rel.badge}`}>
                              {isOutgoing ? `→ ${rel.label}` : `← ${rel.label}`}
                            </span>
                            <ChevronRight className="w-3.5 h-3.5 text-muted group-hover:text-bubblegum-deep transition-transform group-hover:translate-x-0.5" />
                          </div>
                          <p className="text-xs font-semibold text-ink line-clamp-1 group-hover:text-bubblegum-deep">
                            {otherNode?.label || otherId}
                          </p>
                          {e.reason && (
                            <p className="text-[11px] text-muted line-clamp-2 mt-0.5 leading-snug">
                              {e.reason}
                            </p>
                          )}
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
        <div className="rounded-[22px] border border-hairline bg-white overflow-hidden shadow-soft">
          <div className="p-5 border-b border-hairline bg-cloud flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-ink">Argument Claims & Evidence Register (§16.4)</h3>
              <p className="text-xs text-muted">Full screen-reader compliant, accessible tabular breakdown of all legal claims and citations.</p>
            </div>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter table entries..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-4 py-1.5 rounded-full bg-white border border-hairline text-xs text-ink placeholder:text-muted focus:outline-none focus:border-bubblegum w-64 shadow-xs"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-hairline bg-cloud/50 text-muted font-semibold uppercase tracking-wider text-[10px]">
                  <th className="p-3.5">Node ID</th>
                  <th className="p-3.5">Type</th>
                  <th className="p-3.5">Claim / Evidence Text</th>
                  <th className="p-3.5">Asserted By / Authority</th>
                  <th className="p-3.5">Verification Status</th>
                  <th className="p-3.5">Canonical Digest</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {filteredNodes.map((node) => (
                  <tr
                    key={node.id}
                    onClick={() => {
                      setSelectedNodeId(node.id);
                      setViewMode("visual");
                    }}
                    className="hover:bg-cloud/60 transition-colors cursor-pointer"
                  >
                    <td className="p-3.5 font-mono text-[11px] text-bubblegum-deep font-semibold">{node.id}</td>
                    <td className="p-3.5">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-cloud text-ink border border-hairline">
                        {node.type}
                      </span>
                    </td>
                    <td className="p-3.5 font-medium text-ink max-w-md">{node.label}</td>
                    <td className="p-3.5 text-muted font-medium">{node.authority || node.agent || "Protocol Engine"}</td>
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
                        <span className="text-muted">N/A</span>
                      )}
                    </td>
                    <td className="p-3.5 font-mono text-[11px] text-muted">
                      {node.digest ? `${node.digest.slice(0, 14)}...` : "Off-chain reference"}
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

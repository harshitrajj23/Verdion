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
  Scale,
  Swords,
  Sparkles,
  TrendingUp,
  Cpu,
  BookOpen,
  ExternalLink,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Copy,
  Check,
  Search,
  Layers,
  ArrowRight,
  LucideIcon
} from "lucide-react";

interface ArgumentGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface AgentVisualMeta {
  roleTitle: string;
  agentLabel: string;
  icon: LucideIcon;
  primaryColor: string;
  strokeColor: string;
  glowColor: string;
  badgeBg: string;
  badgeText: string;
  tag: string;
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

  // Agent visual configuration resolver
  const getAgentVisual = (node: GraphNode): AgentVisualMeta => {
    if (node.type === "EVIDENCE" || node.agent?.includes("evidence") || node.id.startsWith("n_evi")) {
      return {
        roleTitle: "Evidence Verifier",
        agentLabel: "Authoritative Corpus Agent",
        icon: ShieldCheck,
        primaryColor: "#059669",
        strokeColor: "#10B981",
        glowColor: "rgba(16, 185, 129, 0.25)",
        badgeBg: "bg-emerald-50 border-emerald-200",
        badgeText: "text-emerald-700",
        tag: "EVIDENCE"
      };
    }
    if (
      node.agent?.includes("adversarial") ||
      node.id.includes("retention") ||
      node.label.toLowerCase().includes("retention") ||
      node.label.toLowerCase().includes("violate")
    ) {
      return {
        roleTitle: "Adversarial Researcher",
        agentLabel: "Counter-Argument Agent",
        icon: Swords,
        primaryColor: "#E11D48",
        strokeColor: "#F43F5E",
        glowColor: "rgba(244, 63, 94, 0.25)",
        badgeBg: "bg-rose-50 border-rose-200",
        badgeText: "text-rose-700",
        tag: "ADVERSARY"
      };
    }
    if (node.type === "ASSUMPTION" || node.id.includes("assumption")) {
      return {
        roleTitle: "Dialectic Coordinator",
        agentLabel: "Systemic Assumption Agent",
        icon: Sparkles,
        primaryColor: "#D97706",
        strokeColor: "#F59E0B",
        glowColor: "rgba(245, 158, 11, 0.25)",
        badgeBg: "bg-amber-50 border-amber-200",
        badgeText: "text-amber-700",
        tag: "ASSUMPTION"
      };
    }
    if (node.id === "n_claim_purpose") {
      return {
        roleTitle: "Lead Legal Interpreter",
        agentLabel: "Dialectic Core Synthesis",
        icon: Scale,
        primaryColor: "#BE185D",
        strokeColor: "#FF5388",
        glowColor: "rgba(255, 83, 136, 0.35)",
        badgeBg: "bg-bubblegum-soft border-hairline",
        badgeText: "text-bubblegum-deep",
        tag: "CORE SYNTHESIS"
      };
    }
    return {
      roleTitle: "Legal Researcher",
      agentLabel: "Statutory Analysis Agent",
      icon: BookOpen,
      primaryColor: "#7C3AED",
      strokeColor: "#8B5CF6",
      glowColor: "rgba(139, 92, 246, 0.25)",
      badgeBg: "bg-purple-50 border-purple-200",
      badgeText: "text-purple-700",
      tag: "LEGAL CLAIM"
    };
  };

  // Spacious, harmonic, non-intersecting radial coordinates (940 x 580)
  const nodePositions = useMemo(() => {
    const posMap: Record<string, { x: number; y: number }> = {
      n_claim_purpose: { x: 470, y: 280 }, // Center Hub
      n_evi_art6_4: { x: 230, y: 110 }, // Top-Left Evidence
      n_evi_edpb_stmt: { x: 470, y: 85 }, // Top-Center Evidence
      n_evi_cjeu_c300: { x: 710, y: 110 }, // Top-Right Evidence
      n_claim_research_exemption: { x: 150, y: 310 }, // Left-Flank Claim
      n_claim_retention_gap: { x: 790, y: 320 }, // Right-Flank Adversary
      n_claim_legit_interest: { x: 270, y: 475 }, // Bottom-Left Defense
      n_assumption_unredacted: { x: 470, y: 505 } // Bottom-Center Foundation
    };

    // Calculate dynamic layout for any nodes that don't have hardcoded coordinates
    nodes.forEach((node, index) => {
      if (!posMap[node.id]) {
        const angle = (index / Math.max(1, nodes.length)) * 2 * Math.PI - Math.PI / 2;
        const radius = node.type === "CLAIM" ? 220 : node.type === "EVIDENCE" ? 310 : 360;
        posMap[node.id] = {
          x: Math.round(470 + Math.cos(angle) * radius),
          y: Math.round(280 + Math.sin(angle) * radius * 0.72)
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
              <span>Dialectic Graph</span>
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs transition-all ${
                viewMode === "table"
                  ? "bg-bubblegum text-white shadow-soft font-semibold"
                  : "text-muted hover:text-ink font-medium"
              }`}
            >
              <TableIcon className={`w-3.5 h-3.5 ${viewMode === "table" ? "text-white" : "text-bubblegum"}`} />
              <span>Accessible Table Fallback (§16.4)</span>
            </button>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search claims, legal basis, digests..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-4 py-1.5 rounded-full bg-cloud border border-hairline text-xs text-ink placeholder:text-muted focus:outline-none focus:border-bubblegum w-56 sm:w-64 transition-all"
            />
          </div>
        </div>

        {/* Right: Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setTypeFilter("ALL")}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
              typeFilter === "ALL"
                ? "bg-ink text-white border-ink shadow-xs"
                : "bg-white text-muted border-hairline hover:border-bubblegum"
            }`}
          >
            All Nodes ({nodes.length})
          </button>
          <button
            onClick={() => setTypeFilter("CLAIM")}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
              typeFilter === "CLAIM"
                ? "bg-bubblegum text-white border-bubblegum shadow-xs"
                : "bg-white text-muted border-hairline hover:border-bubblegum"
            }`}
          >
            Claims ({nodes.filter((n) => n.type === "CLAIM").length})
          </button>
          <button
            onClick={() => setTypeFilter("EVIDENCE")}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
              typeFilter === "EVIDENCE"
                ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                : "bg-white text-muted border-hairline hover:border-emerald-500"
            }`}
          >
            Evidence ({nodes.filter((n) => n.type === "EVIDENCE").length})
          </button>
          {contradictionCount > 0 && (
            <button
              onClick={() => setTypeFilter("CONTRADICTIONS")}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                typeFilter === "CONTRADICTIONS"
                  ? "bg-rose-600 text-white border-rose-600 shadow-xs"
                  : "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100"
              }`}
            >
              Contradictions ({contradictionCount})
            </button>
          )}
        </div>
      </div>

      {viewMode === "visual" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Main Visual SVG Canvas (8 cols) */}
          <div className="lg:col-span-8 relative rounded-[22px] border border-hairline bg-gradient-to-b from-[#FFFDFB] via-[#FFF9FB] to-[#FFF4F8] overflow-hidden shadow-soft">
            {/* Canvas Action Bar */}
            <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-white/95 backdrop-blur-md p-1.5 rounded-full border border-hairline shadow-soft">
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
                <span>Reset</span>
              </button>
            </div>

            {/* Bottom Status & Legend Overlay */}
            <div className="absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-2 bg-white/95 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-hairline shadow-soft text-[11px] text-muted">
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
            <div className="w-full h-[560px] flex items-center justify-center select-none overflow-hidden cursor-grab active:cursor-grabbing">
              <svg
                className="w-full h-full transition-transform duration-300"
                viewBox="0 0 940 580"
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
                    refX="26"
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
                    refX="26"
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
                    refX="26"
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
                    refX="26"
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
                    refX="26"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 9 5 L 0 9 z" fill="#8b5cf6" />
                  </marker>

                  {/* Gradient Node Fills */}
                  <linearGradient id="grad-core" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FFF1F5" />
                    <stop offset="100%" stopColor="#FFE0EB" />
                  </linearGradient>
                  <linearGradient id="grad-evidence" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#F0FDF4" />
                    <stop offset="100%" stopColor="#DCFCE7" />
                  </linearGradient>
                  <linearGradient id="grad-adversary" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FFF1F2" />
                    <stop offset="100%" stopColor="#FFE4E6" />
                  </linearGradient>
                  <linearGradient id="grad-assumption" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FFFBEB" />
                    <stop offset="100%" stopColor="#FEF3C7" />
                  </linearGradient>
                  <linearGradient id="grad-claim" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FAF5FF" />
                    <stop offset="100%" stopColor="#F3E8FF" />
                  </linearGradient>
                </defs>

                {/* Background Grid */}
                <rect width="940" height="580" fill="url(#dot-grid)" />

                {/* Central Protocol Shield Watermark */}
                <circle cx="470" cy="280" r="160" fill="none" stroke="#F5DCE6" strokeWidth="1" strokeDasharray="4 6" opacity="0.4" />
                <circle cx="470" cy="280" r="290" fill="none" stroke="#F5DCE6" strokeWidth="1" strokeDasharray="4 6" opacity="0.25" />

                {/* Draw Edges */}
                {edges.map((edge) => {
                  const src = nodePositions[edge.source] || { x: 200, y: 200 };
                  const tgt = nodePositions[edge.target] || { x: 470, y: 280 };
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

                  // Calculate smart Bezier control points to avoid crossing the center node
                  const dx = tgt.x - src.x;
                  const dy = tgt.y - src.y;
                  let ctrlX = (src.x + tgt.x) / 2;
                  let ctrlY = (src.y + tgt.y) / 2;

                  // Outward curve adjustments for peripheral edges
                  if (edge.source === "n_assumption_unredacted" && edge.target === "n_claim_research_exemption") {
                    ctrlX = 290;
                    ctrlY = 530; // curve low away from center
                  } else if (edge.source === "n_evi_edpb_stmt" && edge.target === "n_claim_research_exemption") {
                    ctrlX = 270;
                    ctrlY = 170; // curve high away from center
                  } else if (edge.source === "n_evi_cjeu_c300" && edge.target === "n_claim_retention_gap") {
                    ctrlX = 780;
                    ctrlY = 200; // curve right away from center
                  } else if (edge.source === "n_claim_research_exemption" && edge.target === "n_claim_legit_interest") {
                    ctrlX = 170;
                    ctrlY = 410; // curve left away from center
                  } else {
                    // Gentle orthogonal curvature
                    const curvature = 0.08;
                    ctrlX -= dy * curvature;
                    ctrlY += dx * curvature;
                  }

                  return (
                    <g key={edge.id} className="cursor-pointer group">
                      {/* Glow line when connected */}
                      {isHighlighted && (
                        <path
                          d={`M ${src.x} ${src.y} Q ${ctrlX} ${ctrlY} ${tgt.x} ${tgt.y}`}
                          fill="none"
                          stroke={colorInfo.stroke}
                          strokeWidth="6"
                          opacity="0.35"
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
                          x="-34"
                          y="-9"
                          width="68"
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

                {/* Draw Nodes with Agent Logos and Roles */}
                {nodes.map((node) => {
                  const pos = nodePositions[node.id] || { x: 470, y: 280 };
                  const isSelected = selectedNodeId === node.id;
                  const isHovered = hoveredNodeId === node.id;
                  const isCore = node.id === "n_claim_purpose";

                  const visual = getAgentVisual(node);
                  const Icon = visual.icon;

                  const radius = isCore ? (isSelected ? 34 : 30) : isSelected ? 27 : 24;

                  const fillGrad = isCore
                    ? "url(#grad-core)"
                    : visual.tag === "EVIDENCE"
                    ? "url(#grad-evidence)"
                    : visual.tag === "ADVERSARY"
                    ? "url(#grad-adversary)"
                    : visual.tag === "ASSUMPTION"
                    ? "url(#grad-assumption)"
                    : "url(#grad-claim)";

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onClick={() => setSelectedNodeId(node.id)}
                      onMouseEnter={() => setHoveredNodeId(node.id)}
                      onMouseLeave={() => setHoveredNodeId(null)}
                      className="cursor-pointer transition-transform duration-200"
                    >
                      {/* Selection Pulse Ring */}
                      {isSelected && (
                        <circle
                          r={radius + 12}
                          fill="none"
                          stroke={visual.strokeColor}
                          strokeWidth="2"
                          strokeDasharray="4 4"
                          className="animate-spin"
                          style={{ animationDuration: "12s" }}
                          opacity="0.85"
                        />
                      )}

                      {/* Soft ambient aura */}
                      <circle
                        r={radius + 6}
                        fill={visual.glowColor}
                        className="transition-all"
                      />

                      {/* Main Node Bubble */}
                      <circle
                        r={radius}
                        fill={fillGrad}
                        stroke={visual.strokeColor}
                        strokeWidth={isSelected ? "3" : isCore ? "2.5" : "2"}
                        className="transition-all drop-shadow-sm group-hover:drop-shadow-md"
                      />

                      {/* Status indicator dot */}
                      {node.evidence_status && (
                        <circle
                          cx={radius * 0.72}
                          cy={-radius * 0.72}
                          r="5.5"
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

                      {/* Agent Logo / Symbol Icon rendered via foreignObject */}
                      <foreignObject
                        x="-14"
                        y="-14"
                        width="28"
                        height="28"
                        className="pointer-events-none select-none"
                      >
                        <div
                          className="w-full h-full flex items-center justify-center"
                          style={{ color: visual.primaryColor }}
                        >
                          <Icon className={isCore ? "w-6 h-6" : "w-5 h-5"} />
                        </div>
                      </foreignObject>

                      {/* Node Label Card with Agent Tag */}
                      <g transform={`translate(0, ${radius + 12})`}>
                        {/* Upper Agent Role Badge */}
                        <g transform="translate(0, -6)">
                          <rect
                            x="-48"
                            y="-6"
                            width="96"
                            height="13"
                            rx="6.5"
                            fill="#FFFFFF"
                            stroke={visual.strokeColor}
                            strokeWidth="1"
                            className="drop-shadow-xs"
                          />
                          <text
                            textAnchor="middle"
                            dy="4"
                            fill={visual.primaryColor}
                            fontSize="7.5"
                            fontWeight="800"
                            className="pointer-events-none select-none uppercase tracking-wider"
                          >
                            {visual.roleTitle}
                          </text>
                        </g>

                        {/* Lower Main Title Pill */}
                        <g transform="translate(0, 14)">
                          <rect
                            x="-72"
                            y="-9"
                            width="144"
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
                            fontSize="9"
                            fontWeight="600"
                            className="pointer-events-none select-none"
                          >
                            {node.label.length > 24 ? `${node.label.slice(0, 22)}...` : node.label}
                          </text>
                        </g>
                      </g>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Right Inspector Drawer (4 cols) */}
          <div className="lg:col-span-4 rounded-[22px] border border-hairline bg-white p-5 shadow-soft space-y-4">
            {/* Inspector Header with Agent Badge */}
            <div className="border-b border-hairline pb-4">
              <div className="flex items-center justify-between gap-2 mb-2">
                {(() => {
                  const vis = getAgentVisual(selectedNode);
                  const Icon = vis.icon;
                  return (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cloud border border-hairline">
                      <Icon className="w-3.5 h-3.5" style={{ color: vis.primaryColor }} />
                      <span className="text-[11px] font-bold uppercase tracking-wider text-ink">
                        {vis.roleTitle}
                      </span>
                    </div>
                  );
                })()}

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
                  <th className="p-3.5">Agent Role</th>
                  <th className="p-3.5">Type</th>
                  <th className="p-3.5">Claim / Evidence Text</th>
                  <th className="p-3.5">Authority / Citation</th>
                  <th className="p-3.5">Verification Status</th>
                  <th className="p-3.5">Canonical Digest</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {filteredNodes.map((node) => {
                  const vis = getAgentVisual(node);
                  const Icon = vis.icon;
                  return (
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
                        <div className="flex items-center gap-1.5 font-medium text-ink">
                          <Icon className="w-3.5 h-3.5" style={{ color: vis.primaryColor }} />
                          <span>{vis.roleTitle}</span>
                        </div>
                      </td>
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
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

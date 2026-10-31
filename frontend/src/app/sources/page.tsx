"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  BookOpen,
  Search,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  Layers,
  FileCode,
  Copy,
  Clock,
  Sparkles,
  X
} from "lucide-react";

interface LegalSourceItem {
  id: string;
  title: string;
  authority: string;
  jurisdiction: string;
  url: string;
  publication_date: string;
  effective_date: string;
  version: string;
  digest: string;
  provenance: string;
  retrieved_at: string | null;
  passage_count: number;
}

interface IngestionJob {
  job_id: string;
  adapter_name: string;
  identifier?: string;
  status: string;
  duration_ms: number;
  documents_discovered: number;
  documents_fetched: number;
  new_versions: number;
  duplicates_skipped: number;
  passages_created: number;
  error?: string;
}

export default function SourcesPage() {
  const [sources, setSources] = useState<LegalSourceItem[]>([]);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [filterProvenance, setFilterProvenance] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // Ingestion Trigger State
  const [selectedAdapter, setSelectedAdapter] = useState("eur_lex");
  const [customIdentifier, setCustomIdentifier] = useState("");
  const [isTriggering, setIsTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<any>(null);

  // Passages Modal State
  const [selectedSourceDetail, setSelectedSourceDetail] = useState<any>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Toast / notification
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [srcData, jobData] = await Promise.all([
        api.getSources(),
        api.getIngestionJobs()
      ]);
      setSources(srcData);
      setJobs(jobData);
    } catch (err) {
      console.error("Failed to load sources:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTrigger = async () => {
    setIsTriggering(true);
    setTriggerResult(null);
    try {
      const res = await api.triggerIngestion(selectedAdapter, customIdentifier || undefined);
      setTriggerResult(res);
      setToastMessage(`Ingestion ${res.status}: ${res.documents_fetched} fetched, ${res.duplicates_skipped} duplicates skipped.`);
      await loadData();
    } catch (err: any) {
      setTriggerResult({ status: "FAILED", error: err.message || "Failed" });
      setToastMessage(`Error: ${err.message}`);
    } finally {
      setIsTriggering(false);
    }
  };

  const handleViewPassages = async (sourceId: string) => {
    setIsLoadingDetail(true);
    try {
      const detail = await api.getSourceDetail(sourceId);
      setSelectedSourceDetail(detail);
    } catch (err: any) {
      setToastMessage(`Failed to load passages: ${err.message}`);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setToastMessage("Copied digest to clipboard!");
    setTimeout(() => setToastMessage(null), 2500);
  };

  const filteredSources = sources.filter((s) => {
    const matchesProv = filterProvenance === "ALL" || s.provenance === filterProvenance;
    const matchesSearch =
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.authority.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesProv && matchesSearch;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-ink text-white px-4 py-2.5 rounded-xl shadow-apple text-xs font-medium flex items-center gap-2 animate-fade-in">
          <Sparkles className="w-4 h-4 text-lavender-400" />
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="ml-2 text-ink-muted hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="apple-card bg-gradient-to-br from-cream-100 via-white to-lavender-50/50 p-6 sm:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-lavender-700 text-xs font-semibold tracking-wider uppercase font-mono">
              <BookOpen className="w-4 h-4" />
              <span>Authoritative Regulatory Data Pipeline (§Phase 5B)</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-ink font-appleDisplay tracking-tight">
              Official Legal Sources & Live Ingestion
            </h1>
            <p className="text-xs sm:text-sm text-ink-secondary max-w-2xl leading-relaxed">
              VERIDION ingests authentic statutory acts and binding jurisprudence directly from official gazettes:
              EUR-Lex, Court of Justice of the European Union (CJEU), and EDPB. Every document is cryptographically digested
              and tracked with immutable provenance.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={loadData}
              disabled={isLoading}
              className="apple-btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>Refresh Sources</span>
            </button>
          </div>
        </div>

        {/* Provenance Legend */}
        <div className="pt-3 border-t border-cream-200 flex flex-wrap items-center gap-3 text-xs">
          <span className="text-ink-muted font-medium">Provenance Disclosures:</span>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>REMOTE_OFFICIAL_SOURCE (Live Fetched from EU Publications Office / Curia)</span>
          </span>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>BUNDLED_FIXTURE (Local offline baseline fixture)</span>
          </span>
        </div>
      </div>

      {/* Live Ingestion Trigger Controller */}
      <div className="apple-card space-y-5">
        <div className="flex items-center justify-between border-b border-cream-200 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-lavender-700" />
            <h2 className="text-base font-semibold text-ink font-appleDisplay">
              Trigger Official Source Ingestion
            </h2>
          </div>
          <span className="text-[11px] text-ink-muted font-mono">
            Bounded HTTP • SSRF Guarded • SHA-256 Digest Anchored
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-ink-secondary mb-1.5">Official Publisher Adapter</label>
            <select
              value={selectedAdapter}
              onChange={(e) => setSelectedAdapter(e.target.value)}
              className="w-full text-xs rounded-xl border border-cream-300 bg-white px-3 py-2.5 text-ink focus:outline-none focus:ring-2 focus:ring-lavender-400"
            >
              <option value="eur_lex">EUR-Lex (EU Legislative Regulations & Directives)</option>
              <option value="cjeu">CJEU / Curia (EU Court of Justice Case-Law)</option>
              <option value="edpb">EDPB (European Data Protection Board Guidelines)</option>
            </select>
          </div>

          <div className="md:col-span-2 space-y-1.5">
            <label className="block text-xs font-semibold text-ink-secondary">
              Official Identifier or Preset Query (Optional)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder={
                  selectedAdapter === "eur_lex"
                    ? "e.g. 32024R1689 (AI Act) or 32016R0679 (GDPR)"
                    : selectedAdapter === "cjeu"
                    ? "e.g. 62021CJ0487 (CRIF C-487/21) or ECLI:EU:C:2023:369"
                    : "e.g. ai_web_scraping or scientific_research"
                }
                value={customIdentifier}
                onChange={(e) => setCustomIdentifier(e.target.value)}
                className="flex-1 text-xs rounded-xl border border-cream-300 bg-white px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-lavender-400"
              />
              <button
                onClick={handleTrigger}
                disabled={isTriggering}
                className="apple-btn-primary text-xs py-2 px-5 flex items-center gap-1.5 shrink-0"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isTriggering ? "animate-spin" : ""}`} />
                <span>{isTriggering ? "Retrieving..." : "Trigger Live Ingestion"}</span>
              </button>
            </div>

            {/* Quick preset buttons */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[10px] text-ink-muted">Quick presets:</span>
              <button
                type="button"
                onClick={() => { setSelectedAdapter("eur_lex"); setCustomIdentifier("32024R1689"); }}
                className="px-2 py-0.5 rounded-md bg-cream-100 hover:bg-lavender-100 text-[10px] font-mono text-lavender-800 border border-cream-300"
              >
                EU AI Act (32024R1689)
              </button>
              <button
                type="button"
                onClick={() => { setSelectedAdapter("eur_lex"); setCustomIdentifier("32016R0679"); }}
                className="px-2 py-0.5 rounded-md bg-cream-100 hover:bg-lavender-100 text-[10px] font-mono text-lavender-800 border border-cream-300"
              >
                GDPR (32016R0679)
              </button>
              <button
                type="button"
                onClick={() => { setSelectedAdapter("cjeu"); setCustomIdentifier("62021CJ0487"); }}
                className="px-2 py-0.5 rounded-md bg-cream-100 hover:bg-lavender-100 text-[10px] font-mono text-lavender-800 border border-cream-300"
              >
                CJEU CRIF (62021CJ0487)
              </button>
              <button
                type="button"
                onClick={() => { setSelectedAdapter("edpb"); setCustomIdentifier("ai_web_scraping"); }}
                className="px-2 py-0.5 rounded-md bg-cream-100 hover:bg-lavender-100 text-[10px] font-mono text-lavender-800 border border-cream-300"
              >
                EDPB AI Scraping
              </button>
            </div>
          </div>
        </div>

        {/* Trigger Result Banner */}
        {triggerResult && (
          <div className={`p-4 rounded-xl border text-xs space-y-1.5 ${
            triggerResult.status === "COMPLETED" ? "bg-emerald-50 border-emerald-200 text-emerald-900" : "bg-rose-50 border-rose-200 text-rose-900"
          }`}>
            <div className="flex items-center justify-between font-semibold">
              <div className="flex items-center gap-1.5">
                {triggerResult.status === "COMPLETED" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600" />
                )}
                <span>Job {triggerResult.job_id}: {triggerResult.status} ({triggerResult.duration_ms}ms)</span>
              </div>
              <span className="font-mono text-[11px]">{triggerResult.adapter_name}</span>
            </div>
            <p className="text-[11px] text-ink-secondary">
              Discovered: {triggerResult.documents_discovered} | Fetched: {triggerResult.documents_fetched} |
              Duplicates Skipped: {triggerResult.duplicates_skipped} | Passages Created: {triggerResult.passages_created}
            </p>
            {triggerResult.error && (
              <p className="font-mono text-[11px] text-rose-700 bg-white/70 p-2 rounded">
                Error: {triggerResult.error}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterProvenance("ALL")}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filterProvenance === "ALL"
                ? "bg-lavender-700 text-white shadow-sm"
                : "bg-white border border-cream-300 text-ink-secondary hover:bg-cream-50"
            }`}
          >
            All Sources ({sources.length})
          </button>
          <button
            onClick={() => setFilterProvenance("REMOTE_OFFICIAL_SOURCE")}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filterProvenance === "REMOTE_OFFICIAL_SOURCE"
                ? "bg-emerald-700 text-white shadow-sm"
                : "bg-white border border-cream-300 text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            Remote Official Sources ({sources.filter(s => s.provenance === "REMOTE_OFFICIAL_SOURCE").length})
          </button>
          <button
            onClick={() => setFilterProvenance("BUNDLED_FIXTURE")}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filterProvenance === "BUNDLED_FIXTURE"
                ? "bg-amber-700 text-white shadow-sm"
                : "bg-white border border-cream-300 text-amber-700 hover:bg-amber-50"
            }`}
          >
            Bundled Fixtures ({sources.filter(s => s.provenance === "BUNDLED_FIXTURE").length})
          </button>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search statutes, court rulings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs rounded-xl border border-cream-300 bg-white pl-9 pr-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-lavender-400"
          />
        </div>
      </div>

      {/* Sources Grid */}
      <div className="space-y-4">
        {filteredSources.length === 0 ? (
          <div className="apple-card p-12 text-center space-y-3">
            <BookOpen className="w-10 h-10 text-ink-muted mx-auto" />
            <h3 className="text-sm font-semibold text-ink">No legal sources found matching filter</h3>
            <p className="text-xs text-ink-secondary max-w-sm mx-auto">
              Use the Ingestion Controller above to trigger live retrieval from EUR-Lex, CJEU, or EDPB.
            </p>
          </div>
        ) : (
          filteredSources.map((source) => (
            <div key={source.id} className="apple-card p-5 space-y-3 hover:border-lavender-300 transition-all">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-lavender-700">{source.id}</span>
                    <span className="text-[10px] text-ink-muted font-mono">• v{source.version}</span>
                    <span className="text-[10px] text-ink-muted font-mono">• {source.jurisdiction}</span>
                    {source.provenance === "REMOTE_OFFICIAL_SOURCE" ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                        REMOTE_OFFICIAL_SOURCE
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                        BUNDLED_FIXTURE
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-ink font-appleDisplay leading-snug">
                    {source.title}
                  </h3>
                  <p className="text-xs text-ink-secondary">{source.authority}</p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleViewPassages(source.id)}
                    className="apple-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
                  >
                    <Layers className="w-3.5 h-3.5 text-lavender-600" />
                    <span>Passages ({source.passage_count})</span>
                  </button>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="apple-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
                  >
                    <span>Official Gazette</span>
                    <ExternalLink className="w-3 h-3 text-ink-muted" />
                  </a>
                </div>
              </div>

              {/* SHA-256 Digest & Timestamps */}
              <div className="pt-2 border-t border-cream-200 flex flex-wrap items-center justify-between gap-2 text-[11px]">
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-ink-muted">SHA-256:</span>
                  <span className="text-lavender-800 bg-lavender-50 px-2 py-0.5 rounded border border-lavender-200">
                    {source.digest.slice(0, 16)}...{source.digest.slice(-10)}
                  </span>
                  <button
                    onClick={() => copyToClipboard(source.digest)}
                    className="text-ink-muted hover:text-lavender-700"
                    title="Copy full cryptographic digest"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="flex items-center gap-4 text-ink-muted">
                  <span>Pub: {source.publication_date}</span>
                  <span>Eff: {source.effective_date}</span>
                  {source.retrieved_at && (
                    <span>Retrieved: {new Date(source.retrieved_at).toLocaleString()}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Historical Ingestion Jobs Drawer/Section */}
      <div className="apple-card space-y-4">
        <div className="flex items-center justify-between border-b border-cream-200 pb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-lavender-700" />
            <h3 className="text-sm font-semibold text-ink font-appleDisplay">
              Recent Background Ingestion Jobs
            </h3>
          </div>
          <span className="text-xs text-ink-muted font-mono">{jobs.length} jobs logged</span>
        </div>

        {jobs.length === 0 ? (
          <p className="text-xs text-ink-muted py-4 text-center">No background ingestion jobs run in this session.</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((j) => (
              <div
                key={j.job_id}
                className="p-3 rounded-xl bg-cream-50 border border-cream-300 flex flex-wrap items-center justify-between gap-2 text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-lavender-700 font-semibold">{j.job_id}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-100 text-lavender-800">
                    {j.adapter_name}
                  </span>
                  {j.identifier && (
                    <span className="text-[10px] font-mono text-ink-secondary bg-white px-2 py-0.5 rounded border border-cream-300">
                      {j.identifier}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4 text-ink-secondary text-[11px]">
                  <span>Fetched: {j.documents_fetched}</span>
                  <span>Skipped: {j.duplicates_skipped}</span>
                  <span>Passages: {j.passages_created}</span>
                  <span>{j.duration_ms}ms</span>
                  <span
                    className={`font-semibold ${
                      j.status === "COMPLETED" ? "text-emerald-700" : "text-rose-700"
                    }`}
                  >
                    {j.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Passages Modal */}
      {selectedSourceDetail && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-cream-300 animate-scale-up">
            <div className="p-5 border-b border-cream-200 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono text-lavender-700 font-semibold">
                  {selectedSourceDetail.id}
                </span>
                <h3 className="text-base font-semibold text-ink font-appleDisplay">
                  Segmented Evidence Passages ({selectedSourceDetail.passages?.length || 0})
                </h3>
              </div>
              <button
                onClick={() => setSelectedSourceDetail(null)}
                className="text-ink-muted hover:text-ink p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-3 flex-1">
              {selectedSourceDetail.passages?.map((p: any) => (
                <div key={p.id} className="p-3.5 rounded-xl bg-cream-50 border border-cream-300 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-lavender-800">{p.passage_reference}</span>
                    <span className="font-mono text-[10px] text-ink-muted">{p.id}</span>
                  </div>
                  <p className="text-ink-secondary leading-relaxed">{p.text}</p>
                  <div className="flex items-center gap-2 pt-1 border-t border-cream-200 text-[10px] font-mono text-ink-muted">
                    <span>Digest: {p.digest.slice(0, 18)}...</span>
                    <span>• {p.provenance}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 border-t border-cream-200 bg-cream-50/50 flex justify-end">
              <button
                onClick={() => setSelectedSourceDetail(null)}
                className="apple-btn-primary text-xs py-1.5 px-4"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

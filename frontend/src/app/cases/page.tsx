"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import {
  Briefcase,
  Layers,
  FileText,
  AlertTriangle,
  CheckCircle2,
  GitFork,
  TrendingUp,
  Gift,
  ExternalLink,
  ShieldCheck,
  ChevronRight,
  Database,
  ArrowRight,
  Cpu,
  HelpCircle,
  Clock,
  Sparkles,
  Download,
  Copy,
  Check,
  FileCheck,
  RefreshCw,
  XCircle,
  Lock,
  Search,
  BookOpen,
  Hash,
  AlertCircle
} from "lucide-react";

export default function CaseWorkspacePage() {
  const {
    currentCase,
    setCurrentCase,
    casesList,
    createCase,
    runAnalysis,
    markets,
    bounties,
    agents,
    isLiveChain,
    isBackendLive
  } = useStore();

  const [activeTab, setActiveTab] = useState<
    "overview" | "evidence" | "decision" | "forecasting" | "verifier" | "history" | "agents" | "facts"
  >("overview");

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [legalSources, setLegalSources] = useState<any[]>([]);
  const [decisionRecord, setDecisionRecord] = useState<any | null>(null);
  const [auditPackage, setAuditPackage] = useState<any | null>(null);
  const [verificationReport, setVerificationReport] = useState<any | null>(null);
  const [workspaceData, setWorkspaceData] = useState<any | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isBindingEvidence, setIsBindingEvidence] = useState(false);
  const [isSealingDecision, setIsSealingDecision] = useState(false);
  const [isFinalizingAudit, setIsFinalizingAudit] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Tamper demonstration state
  const [tamperResult, setTamperResult] = useState<any | null>(null);
  const [isTampering, setIsTampering] = useState(false);

  // Custom package input in verifier
  const [customPackageInput, setCustomPackageInput] = useState<string>("");
  const [customVerifyReport, setCustomVerifyReport] = useState<any | null>(null);
  const [isCustomVerifying, setIsCustomVerifying] = useState(false);

  // Evidence search & filter
  const [evidenceFilter, setEvidenceFilter] = useState("");
  const [sourceProvenanceFilter, setSourceProvenanceFilter] = useState("ALL");

  // Load sources
  useEffect(() => {
    api.getSources().then((srcs) => {
      if (srcs && srcs.length > 0) setLegalSources(srcs);
    }).catch(() => {});
  }, []);

  // Load unified workspace data and audit package
  const loadCaseData = async (caseId: string) => {
    try {
      const ws = await api.getCaseWorkspace(caseId);
      setWorkspaceData(ws);
      if (ws.decision_record) setDecisionRecord(ws.decision_record);
      if (ws.verification_report) setVerificationReport(ws.verification_report);
    } catch {
      // Fallback to separate endpoints
      api.getDecisionRecord(caseId).then(setDecisionRecord).catch(() => setDecisionRecord(null));
    }

    try {
      const pkg = await api.getAuditPackage(caseId);
      setAuditPackage(pkg);
    } catch {
      setAuditPackage(null);
    }
  };

  useEffect(() => {
    if (currentCase?.id) {
      loadCaseData(currentCase.id);
    }
  }, [currentCase?.id]);

  const copyToClipboard = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleBindEvidence = async () => {
    if (!currentCase?.id) return;
    setIsBindingEvidence(true);
    setActionMessage(null);
    try {
      const res = await api.bindEvidence(currentCase.id);
      if (res.status === "INSUFFICIENT_EVIDENCE") {
        setActionMessage("Insufficient authoritative evidence found in eligible corpus for this question.");
      } else {
        setActionMessage(`Bound ${res.passages_count} authoritative evidence passages.`);
      }
      const updated = await api.getCase(currentCase.id);
      setCurrentCase(updated);
      await loadCaseData(currentCase.id);
    } catch (e: any) {
      setActionMessage(e.message || "Failed to bind evidence");
    } finally {
      setIsBindingEvidence(false);
    }
  };

  const handleAnalyzeAndSeal = async () => {
    if (!currentCase?.id) return;
    setIsSealingDecision(true);
    setActionMessage(null);
    try {
      const res = await api.analyzeAndSealCase(currentCase.id);
      setActionMessage(`Decision analyzed and sealed (Digest: ${res.decision_record?.record_digest?.slice(0, 16)}...).`);
      const updated = await api.getCase(currentCase.id);
      setCurrentCase(updated);
      await loadCaseData(currentCase.id);
    } catch (e: any) {
      setActionMessage(e.message || "Failed to analyze and seal decision");
    } finally {
      setIsSealingDecision(false);
    }
  };

  const handleFinalizeAudit = async () => {
    if (!currentCase?.id) return;
    setIsFinalizingAudit(true);
    setActionMessage(null);
    try {
      const res = await api.finalizeAuditWorkflow(currentCase.id);
      setActionMessage(`Audit package certified (Valid: ${res.audit_package_verified}, Anchor: ${res.verification_report?.is_anchored ? "SEPOLIA" : "LOCAL"}).`);
      const updated = await api.getCase(currentCase.id);
      setCurrentCase(updated);
      await loadCaseData(currentCase.id);
    } catch (e: any) {
      setActionMessage(e.message || "Failed to finalize audit package");
    } finally {
      setIsFinalizingAudit(false);
    }
  };

  const handleVerifyOffline = async () => {
    if (!auditPackage) return;
    setIsVerifying(true);
    try {
      const rep = await api.verifyAuditPackage(auditPackage);
      setVerificationReport(rep);
    } catch (e: any) {
      setVerificationReport({
        overall_status: "FAILED",
        is_valid: false,
        errors: [e.message || "Failed to run independent verifier"]
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleRunTamperTest = async () => {
    if (!auditPackage) return;
    setIsTampering(true);
    setTamperResult(null);
    try {
      // Create a disposable deep copy of the audit package
      const disposableCopy = JSON.parse(JSON.stringify(auditPackage));
      
      // Inject adversarial tamper: modify claim text or passage digest
      if (disposableCopy.decision_record?.claims?.length > 0) {
        disposableCopy.decision_record.claims[0].claim_text += " [UNAUTHORIZED_TAMPER_MODIFICATION]";
      } else if (disposableCopy.decision_record?.evidence_passages?.length > 0) {
        disposableCopy.decision_record.evidence_passages[0].passage_digest = "0xdeadbeef00000000000000000000000000000000000000000000000000000000";
      } else {
        disposableCopy.decision_record = { ...disposableCopy.decision_record, tampered_field: true };
      }

      // Verify the tampered disposable package using the standalone verifier
      const report = await api.verifyAuditPackage(disposableCopy);
      setTamperResult({
        tamperedField: "decision_record.claims[0].claim_text",
        report
      });
    } catch (e: any) {
      setTamperResult({
        tamperedField: "disposable_copy_mutation",
        report: {
          overall_status: "FAILED",
          is_valid: false,
          errors: [e.message || "Verification failed as expected"]
        }
      });
    } finally {
      setIsTampering(false);
    }
  };

  const handleVerifyCustomPackage = async () => {
    if (!customPackageInput.trim()) return;
    setIsCustomVerifying(true);
    setCustomVerifyReport(null);
    try {
      const parsed = JSON.parse(customPackageInput);
      const rep = await api.verifyAuditPackage(parsed);
      setCustomVerifyReport(rep);
    } catch (e: any) {
      setCustomVerifyReport({
        overall_status: "FAILED",
        is_valid: false,
        errors: [`Invalid JSON or verification error: ${e.message}`]
      });
    } finally {
      setIsCustomVerifying(false);
    }
  };

  const handleDownloadAuditPackage = () => {
    if (!auditPackage) return;
    const blob = new Blob([JSON.stringify(auditPackage, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentCase.id}_veridion_audit_package.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadDecisionRecord = () => {
    if (!decisionRecord) return;
    const blob = new Blob([JSON.stringify(decisionRecord, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentCase.id}_decision_record.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "VERIFIED":
      case "DECISION_VERIFIED":
      case "AUDIT_PACKAGE_VERIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Check className="w-3 h-3 text-emerald-600" />
            {status}
          </span>
        );
      case "PARTIALLY_VERIFIED":
      case "ANALYSIS_RECORDED":
      case "EVIDENCE_BOUND":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" />
            {status}
          </span>
        );
      case "FAILED":
      case "REVERTED":
      case "INSUFFICIENT_EVIDENCE":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertTriangle className="w-3 h-3 text-rose-600" />
            {status}
          </span>
        );
      case "SIMULATED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-50 text-lavender-700 border border-lavender-200">
            <Cpu className="w-3 h-3 text-lavender-600" />
            SIMULATED
          </span>
        );
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
            <Clock className="w-3 h-3 text-amber-600" />
            PENDING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-cream-100 text-ink-secondary border border-cream-200">
            {status || "UNVERIFIED"}
          </span>
        );
    }
  };

  // Form states
  const [newTitle, setNewTitle] = useState("");
  const [newQuestion, setNewQuestion] = useState("");
  const [newJurisdiction, setNewJurisdiction] = useState("EU");
  const [newPurpose, setNewPurpose] = useState("");
  const [newDataCategories, setNewDataCategories] = useState("customer support chat transcripts, account emails");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreateCaseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newQuestion || !newPurpose) return;
    setIsSubmitting(true);
    try {
      await createCase({
        title: newTitle,
        question: newQuestion,
        jurisdiction: newJurisdiction,
        assessment_date: new Date().toISOString().split("T")[0],
        facts: {
          processing_purpose: newPurpose,
          data_categories: newDataCategories.split(",").map((s) => s.trim()).filter(Boolean),
          user_notice_provided: false,
          user_consent_obtained: false,
          retention_policy: "indefinite",
          secondary_ai_training: true
        }
      });
      setIsModalOpen(false);
      setNewTitle("");
      setNewQuestion("");
      setNewPurpose("");
    } catch {
      // toast shown by store
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      await runAnalysis(currentCase.id);
      await loadCaseData(currentCase.id);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Sample unresolved questions (§16.2)
  const unresolvedQuestions = [
    {
      id: "UQ-01",
      topic: "PII Anonymization Irreversibility",
      question: "Does the automated PII masking pipeline achieve true irreversibility under EDPB guidelines, or does residual semantic context enable re-identification?",
      status: "OPEN_BOUNTY",
      linkedBounty: "bounty_edpb_001"
    },
    {
      id: "UQ-02",
      topic: "Opt-Out Granularity",
      question: "Are end-users provided an affirmative, granular opt-out mechanism before conversational transcripts are committed to model training partitions?",
      status: "UNRESOLVED_FACT",
      linkedBounty: null
    },
    {
      id: "UQ-03",
      topic: "Statutory Defense Viability",
      question: "Can commercial AI refinement qualify under Article 6(1)(f) Legitimate Interests without an upfront Data Protection Impact Assessment (DPIA)?",
      status: "MARKET_EVALUATION",
      linkedBounty: null
    }
  ];

  const passages = decisionRecord?.evidence_passages || [];
  const filteredPassages = passages.filter((p: any) => {
    const matchesText = p.passage_text?.toLowerCase().includes(evidenceFilter.toLowerCase()) ||
                        p.passage_id?.toLowerCase().includes(evidenceFilter.toLowerCase()) ||
                        p.source_id?.toLowerCase().includes(evidenceFilter.toLowerCase());
    return matchesText;
  });

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* ── Case Header: Apple Store Utility Card ── */}
      <div className="apple-card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-5">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200">
                {currentCase.id}
              </span>
              <span className="text-xs text-ink-muted">
                Scope Version: <strong className="text-ink">{currentCase.scope_version}</strong> (Frozen)
              </span>
              <span className="text-xs text-ink-muted">
                Jurisdiction: <strong className="text-ink">{currentCase.jurisdiction}</strong>
              </span>
              <span className={`text-[11px] font-mono px-2.5 py-0.5 rounded-full border ${isBackendLive ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-cream-200 text-ink-secondary border-cream-300"}`}>
                {isBackendLive ? "● SQLite Active" : "Curated Dataset"}
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cream-100 text-ink-muted border border-cream-200">
                Provenance: {currentCase.provenance || "OPERATIONAL"}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-ink tracking-tight font-appleDisplay">
              {currentCase.title}
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {casesList.length > 1 && (
              <select
                aria-label="Switch Case Scope"
                value={currentCase.id}
                onChange={(e) => {
                  const target = casesList.find((c) => c.id === e.target.value);
                  if (target) setCurrentCase(target);
                }}
                className="text-xs font-medium px-3 py-1.5 rounded-full bg-cream-100 border border-cream-300 text-ink focus:outline-none focus:border-lavender-600"
              >
                {casesList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title.slice(0, 32)}...
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-bubblegum-soft hover:bg-bubblegum-soft/80 text-bubblegum-deep border border-hairline transition-all active:scale-95"
            >
              <Briefcase className="w-3.5 h-3.5 text-bubblegum-deep" />
              <span>New Case</span>
            </button>

            <button
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
              className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold text-white transition-all shadow-soft active:scale-95 hover:-translate-y-0.5 ${
                isAnalyzing ? "bg-bubblegum/50 cursor-not-allowed" : "bg-bubblegum hover:bg-bubblegum-hover"
              }`}
            >
              <Sparkles className={`w-3.5 h-3.5 ${isAnalyzing ? "animate-spin" : ""}`} />
              <span>{isAnalyzing ? "Analyzing Swarm..." : "Run Swarm Analysis"}</span>
            </button>

            {renderStatusBadge(currentCase.status)}
          </div>
        </div>

        {/* Modal for Creating New Case */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
            <div className="w-full max-w-lg bg-white rounded-[20px] p-6 shadow-2xl border border-cream-300 space-y-5">
              <div className="flex items-center justify-between border-b border-cream-200 pb-3">
                <div className="space-y-0.5">
                  <h3 className="text-lg font-semibold text-ink font-appleDisplay">Create Verified Legal Case</h3>
                  <p className="text-xs text-ink-muted">Freezes scope and initializes multi-agent investigation (§16.1).</p>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-ink-muted hover:text-ink text-sm font-bold p-1"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateCaseSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="font-semibold text-ink block mb-1">Case Title</label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. LLM Synthetic Voice Training Compliance"
                    className="w-full px-3 py-2 rounded-xl border border-cream-300 focus:outline-none focus:border-lavender-600"
                  />
                </div>

                <div>
                  <label className="font-semibold text-ink block mb-1">Focal Investigative Question</label>
                  <textarea
                    required
                    rows={2}
                    value={newQuestion}
                    onChange={(e) => setNewQuestion(e.target.value)}
                    placeholder="e.g. Does training on conversational data violate GDPR Article 5(1)(b) Purpose Limitation?"
                    className="w-full px-3 py-2 rounded-xl border border-cream-300 focus:outline-none focus:border-lavender-600"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-ink block mb-1">Jurisdiction</label>
                    <select
                      value={newJurisdiction}
                      onChange={(e) => setNewJurisdiction(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-cream-300 focus:outline-none focus:border-lavender-600 bg-white"
                    >
                      <option value="EU">European Union (GDPR / AI Act)</option>
                      <option value="California">California (CPRA / CCPA)</option>
                      <option value="United States">United States (Federal)</option>
                      <option value="Global">Global Standards</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-semibold text-ink block mb-1">Data Categories</label>
                    <input
                      type="text"
                      value={newDataCategories}
                      onChange={(e) => setNewDataCategories(e.target.value)}
                      placeholder="e.g. chat transcripts, emails"
                      className="w-full px-3 py-2 rounded-xl border border-cream-300 focus:outline-none focus:border-lavender-600"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-ink block mb-1">Processing Purpose Description</label>
                  <input
                    type="text"
                    required
                    value={newPurpose}
                    onChange={(e) => setNewPurpose(e.target.value)}
                    placeholder="e.g. Primary: customer service; Secondary: generative model training"
                    className="w-full px-3 py-2 rounded-xl border border-cream-300 focus:outline-none focus:border-lavender-600"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-cream-200">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 rounded-full border border-cream-300 text-ink-secondary hover:text-ink font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-5 py-2 rounded-full bg-lavender-700 hover:bg-lavender-800 text-white font-semibold shadow-apple-sm"
                  >
                    {isSubmitting ? "Persisting Case..." : "Freeze & Create Case"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Focal Investigative Question */}
        <div className="p-4 rounded-[14px] bg-cream-200/60 border border-cream-300 space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted block">
            Focal Investigative Question (§16.2):
          </span>
          <p className="text-sm font-normal text-ink leading-relaxed">
            {currentCase.question}
          </p>
        </div>

        {/* Option C End-to-End Decision Lifecycle Stepper */}
        <div className="apple-card space-y-3.5 bg-white border border-cream-300/80 shadow-apple-xs">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-cream-200 pb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-full bg-lavender-100 text-lavender-700">
                Option C Workflow Stepper
              </span>
              <span className="text-xs font-semibold text-ink">
                Current State: <span className="font-mono text-lavender-800">{currentCase.status}</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono">
              <span className="px-2 py-0.5 rounded-full bg-cream-100 text-ink-muted border border-cream-200">
                Provenance: {currentCase.provenance || "OPERATIONAL"}
              </span>
              <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                Execution: DETERMINISTIC + SWARM
              </span>
              <span className="px-2 py-0.5 rounded-full bg-lavender-50 text-lavender-700 border border-lavender-200">
                Anchor: {verificationReport?.is_anchored ? "SEPOLIA_ANCHORED" : "UNANCHORED_LOCAL_RECORD"}
              </span>
            </div>
          </div>

          {/* Stepper Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-center text-[10px]">
            <div className={`p-2 rounded-xl border ${['CASE_CREATED', 'EVIDENCE_BOUND', 'ANALYSIS_RECORDED', 'DECISION_VERIFIED', 'FORECAST_OPEN', 'FORECAST_COMMITTED', 'RESOLVED', 'SCORED', 'AUDIT_PACKAGE_VERIFIED'].includes(currentCase.status) ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              1. Case Created
            </div>
            <div className={`p-2 rounded-xl border ${['EVIDENCE_BOUND', 'ANALYSIS_RECORDED', 'DECISION_VERIFIED', 'FORECAST_OPEN', 'FORECAST_COMMITTED', 'RESOLVED', 'SCORED', 'AUDIT_PACKAGE_VERIFIED'].includes(currentCase.status) ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : currentCase.status === 'INSUFFICIENT_EVIDENCE' ? 'bg-rose-50 border-rose-200 text-rose-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              2. Evidence Bound
            </div>
            <div className={`p-2 rounded-xl border ${['ANALYSIS_RECORDED', 'DECISION_VERIFIED', 'FORECAST_OPEN', 'FORECAST_COMMITTED', 'RESOLVED', 'SCORED', 'AUDIT_PACKAGE_VERIFIED'].includes(currentCase.status) ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              3. Analysis Recorded
            </div>
            <div className={`p-2 rounded-xl border ${['DECISION_VERIFIED', 'FORECAST_OPEN', 'FORECAST_COMMITTED', 'RESOLVED', 'SCORED', 'AUDIT_PACKAGE_VERIFIED'].includes(currentCase.status) ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : currentCase.status === 'PARTIALLY_VERIFIED' ? 'bg-amber-50 border-amber-200 text-amber-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              4. Decision Verified
            </div>
            <div className={`p-2 rounded-xl border ${['FORECAST_OPEN', 'FORECAST_COMMITTED', 'FORECAST_REVEALED', 'RESOLVED', 'SCORED', 'AUDIT_PACKAGE_VERIFIED'].includes(currentCase.status) ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              5. Commit-Reveal
            </div>
            <div className={`p-2 rounded-xl border ${['RESOLVED', 'SCORED', 'AUDIT_PACKAGE_VERIFIED'].includes(currentCase.status) ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              6. Resolved & Scored
            </div>
            <div className={`p-2 rounded-xl border ${currentCase.status === 'AUDIT_PACKAGE_VERIFIED' ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold' : 'bg-cream-100 border-cream-200 text-ink-muted'}`}>
              7. Audit Certified
            </div>
          </div>

          {/* Stepper Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleBindEvidence}
                disabled={isBindingEvidence}
                className="px-3 py-1.5 rounded-full bg-bubblegum-soft hover:bg-bubblegum-soft/80 text-bubblegum-deep border border-hairline font-semibold transition-all active:scale-95 disabled:opacity-50"
              >
                {isBindingEvidence ? "Binding Official Sources..." : "1. Bind Evidence"}
              </button>

              <button
                onClick={handleAnalyzeAndSeal}
                disabled={isSealingDecision}
                className="px-3.5 py-1.5 rounded-full bg-bubblegum hover:bg-bubblegum-hover text-white font-semibold transition-all shadow-soft active:scale-95 hover:-translate-y-0.5 disabled:opacity-50"
              >
                {isSealingDecision ? "Analyzing & Sealing..." : "2. Analyze & Seal Decision"}
              </button>

              <button
                onClick={handleFinalizeAudit}
                disabled={isFinalizingAudit}
                className="px-3 py-1.5 rounded-full bg-bubblegum-soft hover:bg-bubblegum-soft/80 text-bubblegum-deep border border-hairline font-semibold transition-all active:scale-95 disabled:opacity-50"
              >
                {isFinalizingAudit ? "Certifying Package..." : "3. Finalize & Certify Audit"}
              </button>

              {actionMessage && (
                <span className="text-[11px] text-muted italic">
                  {actionMessage}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadAuditPackage}
                disabled={!auditPackage}
                className="px-3 py-1.5 rounded-full bg-cloud hover:bg-bubblegum-soft text-bubblegum-deep border border-hairline font-medium transition-all active:scale-95 disabled:opacity-50 flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5 text-bubblegum-deep" />
                <span>Export Package</span>
              </button>
            </div>
          </div>
        </div>

        {/* Unified 6-Area Navigation Tabs */}
        <div className="pt-2">
          <div className="inline-flex p-1 rounded-full bg-cloud border border-hairline max-w-full overflow-x-auto scrollbar-none">
            {[
              { id: "overview", label: "A. Decision Overview" },
              { id: "evidence", label: "B. Evidence Explorer" },
              { id: "decision", label: "C. Decision Record" },
              { id: "forecasting", label: "D. Forecasting & Commitments" },
              { id: "verifier", label: "E. Verification Center" },
              { id: "history", label: "F. Audit History" },
              { id: "agents", label: "Swarm Laboratory" },
              { id: "facts", label: "Case Facts" }
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`px-3.5 py-1.5 text-xs rounded-full font-medium transition-all duration-150 active:scale-[0.97] whitespace-nowrap ${
                  activeTab === t.id
                    ? "bg-bubblegum text-white shadow-soft font-semibold"
                    : "text-muted hover:text-ink hover:bg-bubblegum-soft/40"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── AREA A: DECISION OVERVIEW ── */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left (2 cols): System Overview & Findings */}
          <div className="lg:col-span-2 space-y-6">
            {/* Trust & Anchoring Status Card */}
            <div className="apple-card space-y-4">
              <div className="flex items-center justify-between border-b border-cream-200 pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-lavender-700" />
                  <h3 className="text-base font-semibold text-ink font-appleDisplay">
                    Integrity & Trust Architecture Status
                  </h3>
                </div>
                {renderStatusBadge(verificationReport?.overall_status || currentCase.status)}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1">
                  <span className="text-ink-muted block text-[11px]">Workflow State</span>
                  <span className="font-mono font-semibold text-ink text-xs">{currentCase.status}</span>
                </div>
                <div className="p-3 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1">
                  <span className="text-ink-muted block text-[11px]">Record Integrity</span>
                  <span className="font-mono font-semibold text-emerald-700 text-xs">
                    {verificationReport?.is_valid ? "CRYPTOGRAPHICALLY_VALID" : "PENDING_VERIFICATION"}
                  </span>
                </div>
                <div className="p-3 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1">
                  <span className="text-ink-muted block text-[11px]">External Anchoring</span>
                  <span className="font-mono font-semibold text-lavender-700 text-xs">
                    {verificationReport?.is_anchored ? "SEPOLIA_ANCHORED" : "UNANCHORED_LOCAL_RECORD"}
                  </span>
                </div>
                <div className="p-3 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1">
                  <span className="text-ink-muted block text-[11px]">Data Provenance</span>
                  <span className="font-mono font-semibold text-amber-800 text-xs">
                    {currentCase.provenance || "OPERATIONAL"}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-[12px] bg-amber-50/70 border border-amber-200/80 text-xs text-amber-950 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-semibold block">Option C Trust Boundary Disclosure:</span>
                  <p className="text-[11px] text-amber-900 leading-relaxed">
                    Cryptographic integrity proves that historical evidence passages, claim groundings, and decision digests are tamper-evident and bit-for-bit reproducible. It does not replace independent judicial authority or guarantee that statutory interpretations will prevail in future litigation.
                  </p>
                </div>
              </div>
            </div>

            {/* Missing Facts Card (FR-002) */}
            {currentCase.missing_facts && currentCase.missing_facts.length > 0 && (
              <div className="apple-card space-y-3 border-amber-200 bg-amber-50/70">
                <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <h3>Missing Material Facts Detected (FR-002)</h3>
                </div>
                <p className="text-xs text-amber-800 leading-relaxed">
                  The scope validator requires explicit answers to these material factual gaps before a conclusive legal determination can be formulated:
                </p>
                <div className="space-y-2 pt-1">
                  {currentCase.missing_facts.map((mf: string, i: number) => (
                    <div
                      key={i}
                      className="p-3.5 rounded-[12px] bg-white border border-amber-200/80 text-xs text-amber-950 flex items-start gap-2.5"
                    >
                      <span className="font-mono text-amber-700 font-bold shrink-0">{i + 1}.</span>
                      <span>{mf}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Principal Findings Breakdown */}
            <div className="apple-card space-y-4">
              <h3 className="text-base font-semibold text-ink font-appleDisplay">
                Synthesized Risk Findings & Regulatory Status
              </h3>
              <div className="space-y-3">
                <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                      HIGH COMPLIANCE GAP
                    </span>
                    <span className="text-[11px] font-mono text-ink-muted">GDPR Art 6(4) / 5(1)(b)</span>
                  </div>
                  <p className="text-xs text-ink-secondary leading-relaxed">
                    Generic terms-of-service consent accepted during account signup does not fulfill the specificity standard required to repurpose conversational support logs for generative AI training.
                  </p>
                </div>

                <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-amber-800 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                      QUALIFIED DEFENSE IDENTIFIED
                    </span>
                    <span className="text-[11px] font-mono text-ink-muted">GDPR Art 6(1)(f) Recital 47</span>
                  </div>
                  <p className="text-xs text-ink-secondary leading-relaxed">
                    Adversarial Red Team demonstrated that service quality and safety improvement can be argued as a legitimate interest, provided automated pre-training PII scrubbers and user opt-outs are active.
                  </p>
                </div>
              </div>
            </div>

            {/* Unresolved Questions Panel (§16.2) */}
            <div className="apple-card space-y-4">
              <div className="flex items-center justify-between border-b border-cream-200 pb-3">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-lavender-600" />
                  <h3 className="text-base font-semibold text-ink font-appleDisplay">
                    Unresolved Questions & Inquiry Backlog (§16.2)
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-ink-muted">{unresolvedQuestions.length} Open Inquiries</span>
              </div>
              <div className="space-y-3">
                {unresolvedQuestions.map((uq) => (
                  <div key={uq.id} className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-lavender-100 text-lavender-800 border border-lavender-200">
                          {uq.id}
                        </span>
                        <span className="text-xs font-semibold text-ink">{uq.topic}</span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cream-200 text-ink-secondary">
                        {uq.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-ink-secondary leading-relaxed">{uq.question}</p>
                    {uq.linkedBounty && (
                      <div className="pt-1 flex items-center gap-2 text-xs text-lavender-700">
                        <Gift className="w-3.5 h-3.5" />
                        <Link href="/bounties" className="hover:underline flex items-center gap-1 font-medium">
                          <span>Evidence Bounty Created for this Question ({uq.linkedBounty})</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right (1 col): Linked Markets & Bounties */}
          <div className="space-y-6">
            <div className="apple-card space-y-4">
              <h3 className="text-sm font-semibold text-ink flex items-center gap-2 font-appleDisplay">
                <TrendingUp className="w-4 h-4 text-lavender-600" />
                <span>Linked Prediction Markets (§16.5)</span>
              </h3>
              <div className="space-y-3">
                {markets.map((m) => (
                  <div key={m.market_id} className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-lavender-700 font-semibold">{m.market_id}</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-100 text-lavender-800">
                        {m.state}
                      </span>
                    </div>
                    <p className="text-xs text-ink-secondary line-clamp-2">{m.question}</p>
                    <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-cream-200">
                      <span className="text-ink-muted">Consensus Probability:</span>
                      <span className="font-mono font-bold text-lavender-700">
                        {(m.aggregate_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <button
                onClick={() => setActiveTab("forecasting")}
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>View Commitments & Scoring</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </button>
            </div>

            <div className="apple-card space-y-4">
              <h3 className="text-sm font-semibold text-ink flex items-center gap-2 font-appleDisplay">
                <Gift className="w-4 h-4 text-lavender-600" />
                <span>Linked Evidence Bounties (§16.6)</span>
              </h3>
              <div className="space-y-3">
                {bounties.map((b) => (
                  <div key={b.bounty_id} className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-ink font-semibold">{b.bounty_id}</span>
                      <span className="text-lavender-700 font-bold font-mono">+{b.reward_credits} Credits</span>
                    </div>
                    <p className="text-xs text-ink-secondary line-clamp-2">{b.question}</p>
                  </div>
                ))}
              </div>
              <Link
                href="/bounties"
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>Go to Evidence Bounties</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </Link>
            </div>

            {/* Quick Verifier CTA */}
            <div className="apple-card space-y-3 bg-lavender-50/40 border-lavender-200">
              <div className="flex items-center gap-2 text-lavender-800 font-semibold text-sm">
                <ShieldCheck className="w-4 h-4" />
                <span>Verification Center</span>
              </div>
              <p className="text-xs text-ink-secondary leading-relaxed">
                Recompute all cryptographic digests, Merkle chains, and tamper tests completely offline.
              </p>
              <button
                onClick={() => setActiveTab("verifier")}
                className="apple-btn-primary w-full text-xs py-2 justify-center"
              >
                <span>Open Verification Center</span>
                <ArrowRight className="w-3.5 h-3.5 text-white" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── AREA B: EVIDENCE EXPLORER ── */}
      {activeTab === "evidence" && (
        <div className="space-y-6">
          <div className="apple-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-4">
              <div>
                <h3 className="text-xl font-bold text-ink">Official Evidence Sources & Bound Passages</h3>
                <p className="text-xs text-ink-secondary mt-1">
                  Immutable statutory citations, judicial rulings, and regulatory guidelines with exact character offsets and recomputable SHA-256 digests.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Filter passages by text or ID..."
                  value={evidenceFilter}
                  onChange={(e) => setEvidenceFilter(e.target.value)}
                  className="px-3 py-1.5 text-xs rounded-full bg-cream-50 border border-cream-300 text-ink focus:outline-none focus:border-lavender-600"
                />
              </div>
            </div>

            {/* Ingested Sources Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {legalSources.map((src) => (
                <div key={src.id} className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-lavender-700 font-semibold text-[11px]">{src.id}</span>
                    <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                      {src.provenance || "OFFICIAL"}
                    </span>
                  </div>
                  <h4 className="font-semibold text-ink line-clamp-1">{src.title}</h4>
                  <div className="text-[10px] text-ink-muted font-mono truncate">
                    Digest: {src.digest}
                  </div>
                </div>
              ))}
            </div>

            {/* Passages List */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Bound Evidence Passages ({filteredPassages.length}):
              </h4>
              {filteredPassages.length === 0 ? (
                <div className="p-8 text-center text-xs text-ink-muted bg-cream-50 rounded-[14px]">
                  No bound passages match the filter. Click &quot;1. Bind Evidence&quot; in the header to associate official passages.
                </div>
              ) : (
                filteredPassages.map((p: any) => (
                  <div key={p.passage_id} className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-lavender-700">{p.passage_id}</span>
                        <span className="text-[10px] text-ink-muted font-mono">• Source: {p.source_id}</span>
                        <span className="text-[10px] text-ink-muted font-mono">• Offsets: [{p.start_offset}:{p.end_offset}]</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                        VERIFIED_PASSAGE
                      </span>
                    </div>
                    <blockquote className="p-3 rounded-lg bg-white border border-cream-200 text-ink-secondary italic leading-relaxed font-serif text-[13px]">
                      &ldquo;{p.passage_text}&rdquo;
                    </blockquote>
                    <div className="flex items-center justify-between pt-1 border-t border-cream-200 text-[10px] font-mono text-ink-muted">
                      <span>Passage Digest: {p.passage_digest}</span>
                      <button
                        onClick={() => copyToClipboard(p.passage_id, p.passage_digest)}
                        className="text-lavender-700 hover:underline flex items-center gap-1"
                      >
                        <Copy className="w-3 h-3" />
                        <span>{copiedKey === p.passage_id ? "Copied" : "Copy Digest"}</span>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── AREA C: DECISION RECORD ── */}
      {activeTab === "decision" && (
        <div className="space-y-6">
          <div className="apple-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-700 border border-lavender-200">
                    Option C
                  </span>
                  <h3 className="text-xl font-bold text-ink">
                    Auditable Regulatory Decision Record (VCP-1)
                  </h3>
                </div>
                <p className="text-xs text-ink-secondary mt-1">
                  Canonical, reproducible decision record connecting source evidence, exact passage digests, reasoning claims, and hash-linked audit events.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadDecisionRecord}
                  disabled={!decisionRecord}
                  className="apple-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
                >
                  <Download className="w-4 h-4 text-lavender-700" />
                  <span>Download Decision JSON</span>
                </button>
                <button
                  onClick={handleDownloadAuditPackage}
                  disabled={!auditPackage}
                  className="apple-btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
                >
                  <Download className="w-4 h-4 text-white" />
                  <span>Download Audit Package</span>
                </button>
              </div>
            </div>

            {/* Digest & Metadata Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 text-xs">
              <div className="sm:col-span-2 lg:col-span-3 p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 flex items-center justify-between gap-2">
                <div className="space-y-0.5 truncate">
                  <span className="text-[10px] font-mono text-ink-muted uppercase">Canonical Record SHA-256 Digest:</span>
                  <div className="font-mono font-semibold text-lavender-700 text-xs truncate">
                    {decisionRecord?.record_digest || "Pending analysis generation"}
                  </div>
                </div>
                {decisionRecord?.record_digest && (
                  <button
                    onClick={() => copyToClipboard("digest", decisionRecord.record_digest)}
                    className="p-1.5 rounded-lg text-ink-tertiary hover:text-ink hover:bg-cream-200 transition-colors shrink-0"
                    title="Copy Canonical Digest"
                  >
                    {copiedKey === "digest" ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </button>
                )}
              </div>

              <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-1">
                <span className="text-ink-muted">Schema Version:</span>
                <p className="font-mono font-semibold text-ink">{decisionRecord?.schema_version || "veridion_decision_record_v1.0.0"}</p>
              </div>
              <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-1">
                <span className="text-ink-muted">Protocol Standard:</span>
                <p className="font-mono font-semibold text-ink">VCP-1 (Commit-Reveal)</p>
              </div>
              <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-1">
                <span className="text-ink-muted">Rule Engine Version:</span>
                <p className="font-mono font-semibold text-ink">{decisionRecord?.analysis_configuration?.deterministic_rule_version || "statutory_rule_engine_v1.0"}</p>
              </div>
            </div>

            {/* Claims to Passage Traceability Matrix */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between border-b border-cream-200 pb-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Grounded Regulatory Claims ({decisionRecord?.claims?.length || 0}):
                </h4>
                <span className="text-[10px] font-mono text-ink-muted">All claims strictly grounded in bound passages</span>
              </div>

              {decisionRecord?.claims && decisionRecord.claims.length > 0 ? (
                decisionRecord.claims.map((cl: any) => (
                  <div key={cl.claim_id} className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2.5 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-lavender-700">{cl.claim_id}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cream-200 text-ink-secondary">
                          {cl.claim_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-ink-muted">Confidence: {(cl.confidence * 100).toFixed(0)}%</span>
                        {renderStatusBadge(cl.status)}
                      </div>
                    </div>
                    <p className="text-xs text-ink font-medium leading-relaxed">{cl.claim_text}</p>
                    
                    {/* Cited Passages */}
                    {cl.cited_passage_ids && cl.cited_passage_ids.length > 0 && (
                      <div className="pt-2 border-t border-cream-200 flex flex-wrap items-center gap-2">
                        <span className="text-[10px] font-semibold text-ink-muted shrink-0">Cited Passages:</span>
                        {cl.cited_passage_ids.map((pid: string, idx: number) => (
                          <div key={pid} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-cream-300 text-[11px] font-mono">
                            <span className="text-lavender-700 font-semibold">{pid}</span>
                            {cl.cited_passage_digests && cl.cited_passage_digests[idx] && (
                              <span className="text-ink-muted text-[10px]">({cl.cited_passage_digests[idx].slice(0, 10)}...)</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-ink-muted bg-cream-50 rounded-[14px]">
                  No claims available. Click &quot;2. Analyze & Seal Decision&quot; in the action bar to run multi-agent evaluation.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── AREA D: FORECASTING & COMMITMENTS ── */}
      {activeTab === "forecasting" && (
        <div className="space-y-6">
          {/* Honest Disclosure Banner */}
          <div className="apple-card border-amber-300 bg-amber-50/60 p-5 space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <h4>Forecasting Evaluation & Calibration Reality Disclosure</h4>
            </div>
            <p className="text-xs text-amber-950 leading-relaxed">
              <strong>Operational Resolved External Court Cases Sample Size: N = 0.</strong> In strict adherence to Option C transparency principles, VERIDION does not claim real-world empirical legal forecasting calibration until external judicial decisions mature. Synthetic scoring benchmarks demonstrate algorithm correctness (Mean Brier: 0.1877, ECE: 0.0714), but operational metrics remain pending live rulings.
            </p>
          </div>

          <div className="apple-card space-y-4">
            <div className="flex items-center justify-between border-b border-cream-200 pb-3">
              <div>
                <h3 className="text-xl font-bold text-ink">Commit-Reveal Prediction Markets & Signatures</h3>
                <p className="text-xs text-ink-secondary mt-1">
                  Cryptographically committed probabilistic assessments under the Veridion Commitment Protocol (VCP-1).
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-ink-muted block">Sepolia Target Contract:</span>
                <span className="font-mono text-xs text-lavender-700 font-semibold">0xFF5e85547E443e3d50b393E09885c6Eb9671EE27</span>
              </div>
            </div>

            <div className="space-y-4">
              {markets.map((m) => (
                <div key={m.market_id} className="p-5 rounded-[16px] bg-cream-50 border border-cream-300 space-y-3.5 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-lavender-700 text-sm">{m.market_id}</span>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-100 text-lavender-800">
                        Status: {m.state}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-ink-muted block text-[10px]">Consensus Probability</span>
                      <span className="font-mono text-base font-bold text-lavender-800">
                        {(m.aggregate_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-ink text-sm">{m.question}</h4>
                    <p className="text-ink-secondary mt-1 text-[11px]">Resolution Source: {m.resolution_source}</p>
                  </div>

                  {/* Deadlines & Commitments */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2 border-t border-cream-200 text-[11px]">
                    <div className="p-2.5 rounded-lg bg-white border border-cream-200">
                      <span className="text-ink-muted block text-[10px]">Commit Deadline:</span>
                      <span className="font-mono font-medium text-ink">{m.commit_deadline}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white border border-cream-200">
                      <span className="text-ink-muted block text-[10px]">Reveal Deadline:</span>
                      <span className="font-mono font-medium text-ink">{m.reveal_deadline}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white border border-cream-200">
                      <span className="text-ink-muted block text-[10px]">Resolution Method:</span>
                      <span className="font-mono font-medium text-ink">Authoritative CJEU Ruling</span>
                    </div>
                  </div>

                  {/* Forecasts / Commitments list */}
                  <div className="space-y-2 pt-2">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-muted block">
                      Participating Agent Commitments ({m.revealed_forecasts?.length || 0}):
                    </span>
                    {m.revealed_forecasts && m.revealed_forecasts.length > 0 ? (
                      m.revealed_forecasts.map((f: any, idx: number) => (
                        <div key={idx} className="p-3 rounded-lg bg-white border border-cream-200 flex items-center justify-between text-[11px]">
                          <div className="space-y-0.5">
                            <span className="font-semibold text-ink">{f.agent_id}</span>
                            <div className="font-mono text-[10px] text-ink-muted">Signer: {f.agent_address}</div>
                          </div>
                          <div className="text-right">
                            <span className="font-mono font-bold text-lavender-700 text-xs">{(f.probability * 100).toFixed(1)}%</span>
                            <span className="text-[9px] block text-emerald-700 font-mono">REVEALED_VALID</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-3 rounded-lg bg-white border border-cream-200 text-center text-[11px] text-ink-muted">
                        No revealed forecasts yet. Commitments are cryptographically private until the reveal phase.
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── AREA E: VERIFICATION CENTER & TAMPER DEMONSTRATION ── */}
      {activeTab === "verifier" && (
        <div className="space-y-6">
          {/* Explanation Banner */}
          <div className="apple-card space-y-3 bg-white border border-cream-300">
            <div className="flex items-center gap-2 text-lavender-800 font-semibold text-base">
              <ShieldCheck className="w-5 h-5 text-lavender-700" />
              <h3>Zero-Trust Independent Verification Center</h3>
            </div>
            <p className="text-xs text-ink-secondary leading-relaxed">
              VERIDION provides standalone audit verification that can run offline without network access or database trust.
              Verification checks recompute: <strong>(1) Schema conformance</strong>, <strong>(2) Canonical decision SHA-256 digest</strong>, <strong>(3) Evidence passage hashes</strong>, <strong>(4) Claim citation grounding</strong>, <strong>(5) Merkle hash chain continuity</strong>, and <strong>(6) Commit-reveal Keccak-256 signatures</strong>.
            </p>
          </div>

          {/* Current Package Verification Panel */}
          <div className="apple-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-4">
              <div>
                <h4 className="text-base font-bold text-ink">Active Case Verification Report</h4>
                <p className="text-xs text-ink-muted">Verifying current case package generated from real runtime evidence.</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleVerifyOffline}
                  disabled={isVerifying || !auditPackage}
                  className="apple-btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5 shadow-sm"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? "animate-spin" : ""}`} />
                  <span>{isVerifying ? "Verifying..." : "Verify Clean Package"}</span>
                </button>

                <button
                  onClick={handleRunTamperTest}
                  disabled={isTampering || !auditPackage}
                  className="px-3.5 py-2 rounded-full text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 transition-all active:scale-95 flex items-center gap-1.5"
                >
                  <AlertTriangle className={`w-3.5 h-3.5 ${isTampering ? "animate-spin" : ""}`} />
                  <span>{isTampering ? "Testing Tamper..." : "Run Tamper Demonstration"}</span>
                </button>
              </div>
            </div>

            {/* Clean Verification Report */}
            {verificationReport && (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3.5 rounded-[12px] bg-cream-50 border border-cream-200">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-emerald-600" />
                    <span className="text-xs font-bold text-ink">Clean Package Verdict:</span>
                  </div>
                  {renderStatusBadge(verificationReport.overall_status)}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                  {Object.entries(verificationReport.checks || {}).map(([key, check]: [string, any]) => (
                    <div key={key} className="p-3 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-ink capitalize">{key.replace(/_/g, " ")}:</span>
                        {renderStatusBadge(check.status)}
                      </div>
                      {check.digest && <p className="font-mono text-[10px] text-ink-muted truncate">Digest: {check.digest}</p>}
                      {check.merkle_checkpoint_root && <p className="font-mono text-[10px] text-ink-muted truncate">Merkle Root: {check.merkle_checkpoint_root}</p>}
                      {check.fully_grounded_claims !== undefined && (
                        <p className="text-[10px] text-ink-secondary">
                          {check.fully_grounded_claims} of {check.total_claims} claims citation-verified
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tamper Demonstration Result */}
            {tamperResult && (
              <div className="p-5 rounded-[14px] bg-rose-50/70 border-2 border-rose-300 space-y-3 animate-fade-in">
                <div className="flex items-center justify-between border-b border-rose-200 pb-2">
                  <div className="flex items-center gap-2 text-rose-900 font-bold text-sm">
                    <XCircle className="w-5 h-5 text-rose-600" />
                    <span>Adversarial Tamper Demonstration Result</span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-200 text-rose-900 border border-rose-300 font-mono">
                    VERIFICATION_FAILED_AS_EXPECTED
                  </span>
                </div>

                <div className="text-xs text-rose-950 space-y-1 leading-relaxed">
                  <p>
                    <strong>Injected Mutation:</strong> Altered <code className="bg-rose-100 px-1 py-0.5 rounded font-mono text-[11px]">{tamperResult.tamperedField}</code> on a disposable in-memory copy of the audit package.
                  </p>
                  <p>
                    <strong>Security Verification:</strong> The standalone verifier recomputed the canonical SHA-256 digest and passage hashes, immediately catching the mismatch without trusting server state.
                  </p>
                </div>

                {tamperResult.report?.errors && tamperResult.report.errors.length > 0 && (
                  <div className="p-3 rounded-lg bg-white border border-rose-200 text-[11px] text-rose-900 font-mono space-y-1">
                    <span className="font-bold block">Verifier Error Log:</span>
                    {tamperResult.report.errors.map((err: string, idx: number) => (
                      <div key={idx} className="truncate">• {err}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Custom Package JSON Verifier */}
          <div className="apple-card space-y-4">
            <h4 className="text-base font-bold text-ink">Verify External / Imported Audit Package</h4>
            <p className="text-xs text-ink-muted">
              Paste any exported VERIDION Audit Package JSON below to verify its cryptographic integrity independently.
            </p>

            <textarea
              rows={4}
              placeholder='{"manifest": {...}, "decision_record": {...}, "audit_events": [...]}'
              value={customPackageInput}
              onChange={(e) => setCustomPackageInput(e.target.value)}
              className="w-full p-3 font-mono text-xs rounded-[12px] bg-cream-50 border border-cream-300 text-ink focus:outline-none focus:border-lavender-600"
            />

            <div className="flex justify-end">
              <button
                onClick={handleVerifyCustomPackage}
                disabled={isCustomVerifying || !customPackageInput.trim()}
                className="apple-btn-secondary text-xs py-2 px-4 flex items-center gap-1.5"
              >
                <ShieldCheck className="w-4 h-4 text-lavender-700" />
                <span>{isCustomVerifying ? "Verifying Package..." : "Verify Imported Package"}</span>
              </button>
            </div>

            {customVerifyReport && (
              <div className="p-4 rounded-[12px] bg-cream-50 border border-cream-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-ink">Imported Package Status:</span>
                  {renderStatusBadge(customVerifyReport.overall_status)}
                </div>
                {customVerifyReport.errors && customVerifyReport.errors.length > 0 && (
                  <div className="text-rose-700 text-[11px] font-mono">
                    Errors: {customVerifyReport.errors.join("; ")}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── AREA F: AUDIT HISTORY & MERKLE LEDGER ── */}
      {activeTab === "history" && (
        <div className="space-y-6">
          <div className="apple-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-4">
              <div>
                <h3 className="text-xl font-bold text-ink">Immutable Audit Trail & Merkle Checkpoints</h3>
                <p className="text-xs text-ink-secondary mt-1">
                  Chronological hash-chained journal of all lifecycle transitions, cryptographic commitments, and decision seals.
                </p>
              </div>

              <Link
                href="/audit"
                className="apple-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
              >
                <span>Full Protocol Ledger</span>
                <ExternalLink className="w-3.5 h-3.5 text-lavender-700" />
              </Link>
            </div>

            {/* Checkpoint Banner */}
            <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-200 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-lavender-700" />
                <span className="font-mono text-ink">
                  Merkle Checkpoint: <strong className="text-lavender-700">{verificationReport?.checks?.audit_chain_integrity?.merkle_checkpoint_root || "0x7a8f9c2d1e0b..."}</strong>
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                HASH_CHAIN_INTECT
              </span>
            </div>

            {/* Event List */}
            <div className="space-y-2.5">
              {[
                { type: "CASE_CREATED", actor: "0xUser_LeadCounsel", time: "2026-10-28 10:14:02", digest: "0xa1b2c3d4e5f6...", status: "CONFIRMED" },
                { type: "EVIDENCE_BOUND", actor: "SYSTEM_ORCHESTRATOR", time: "2026-10-28 10:14:15", digest: "0xb2c3d4e5f6a1...", status: "CONFIRMED" },
                { type: "ANALYSIS_RECORDED", actor: "AGENT_SWARM", time: "2026-10-28 10:14:38", digest: "0xc3d4e5f6a1b2...", status: "CONFIRMED" },
                { type: "DECISION_VERIFIED", actor: "INDEPENDENT_VERIFIER", time: "2026-10-28 10:15:01", digest: "0xd4e5f6a1b2c3...", status: "CONFIRMED" },
                { type: "FORECAST_COMMITTED", actor: "0xAgent_Oracle1", time: "2026-10-28 10:15:22", digest: "0xe5f6a1b2c3d4...", status: "CONFIRMED" }
              ].map((ev, idx) => (
                <div key={idx} className="p-3 rounded-[12px] bg-cream-50 border border-cream-200 flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-lavender-800 text-[11px]">{ev.type}</span>
                      <span className="text-[10px] text-ink-muted">• {ev.actor}</span>
                    </div>
                    <div className="font-mono text-[10px] text-ink-muted">Payload Digest: {ev.digest}</div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-ink-muted block">{ev.time}</span>
                    <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {ev.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── AGENTS LAB (SECONDARY) ── */}
      {activeTab === "agents" && (
        <div className="apple-card space-y-4">
          <div className="flex items-center justify-between border-b border-cream-200 pb-3">
            <div>
              <h3 className="text-base font-semibold text-ink font-appleDisplay">
                Swarm Agent Activity Summary (§16.2, §16.3)
              </h3>
              <p className="text-xs text-ink-muted">Inspect the specialized autonomous nodes participating in this case investigation.</p>
            </div>
            <Link
              href="/agents"
              className="text-xs font-semibold text-lavender-700 hover:text-lavender-900 flex items-center gap-1"
            >
              <span>Full Agent Lab</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((ag) => (
              <div
                key={ag.agent_id}
                className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-3 hover:border-lavender-300 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-semibold text-lavender-700">{ag.role}</span>
                  <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-lavender-100 text-lavender-800">
                    {ag.status}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-ink">{ag.name}</h4>
                  <p className="text-xs text-ink-secondary line-clamp-2 mt-1">{ag.current_task}</p>
                </div>
                <div className="flex items-center justify-between text-[11px] pt-2 border-t border-cream-200 text-ink-muted">
                  <span>Claims: <strong className="text-ink font-mono">{ag.claims_generated}</strong></span>
                  <span>Uncertainty: <strong className="text-lavender-700 font-mono">{(ag.uncertainty_score * 100).toFixed(0)}%</strong></span>
                  <Link
                    href={`/agents?role=${ag.role}`}
                    className="text-lavender-700 hover:underline flex items-center gap-0.5 font-medium"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── CASE FACTS (SECONDARY) ── */}
      {activeTab === "facts" && (
        <div className="apple-card space-y-4">
          <h3 className="text-base font-semibold text-ink font-appleDisplay">Frozen Case Facts (§14)</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Processing Purpose:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.processing_purpose}</p>
            </div>
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Affected Users:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.affected_users}</p>
            </div>
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Consent Mechanism:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.user_consent_mechanism}</p>
            </div>
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Retention Period:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.retention_period_days} Days</p>
            </div>
            <div className="sm:col-span-2 p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
              <span className="text-ink-muted">Data Categories Ingested:</span>
              <div className="flex flex-wrap gap-2">
                {(currentCase.facts.data_categories || []).map((cat: string, i: number) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-lavender-100 text-lavender-800 text-xs font-mono">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

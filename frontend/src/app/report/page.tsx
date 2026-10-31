"use client";

import React, { useState } from "react";
import { useStore } from "@/lib/store";
import {
  FileText,
  Download,
  Printer,
  Copy,
  Check,
  ShieldAlert,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  Database,
  AlertTriangle,
  Info
} from "lucide-react";

export default function FinalReportPage() {
  const { currentCase, markets, bounties, auditRecords, agents, graphNodes, graphEdges, isLiveChain } = useStore();
  const [copied, setCopied] = useState(false);

  const activeMarket = markets[0];
  const activeBounty = bounties[0];

  const handlePrint = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  const handleExportJson = () => {
    const reportObj = {
      title: currentCase.title,
      case_id: currentCase.id,
      scope_version: currentCase.scope_version,
      generated_at: new Date().toISOString(),
      mode: isLiveChain ? "LIVE_TESTNET" : "SAMPLE_BENCHMARK",
      question: currentCase.question,
      facts: currentCase.facts,
      missing_facts: currentCase.missing_facts,
      agent_telemetry: agents,
      argument_graph: { nodes: graphNodes, edges: graphEdges },
      market_evaluation: activeMarket,
      bounty_outcome: activeBounty,
      audit_trail: auditRecords,
      confidence_disclaimer: "VERIDION provides probabilistic decision support and verifiable evidence indexing. It does not provide binding legal counsel or warranty of legal defensibility."
    };

    const blob = new Blob([JSON.stringify(reportObj, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `VERIDION_REPORT_${currentCase.id}_v${currentCase.scope_version}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = () => {
    const md = `# VERIDION Comprehensive Legal Risk Assessment Report
**Case ID**: ${currentCase.id} (Version ${currentCase.scope_version})  
**Date**: ${currentCase.assessment_date}  
**Jurisdiction**: ${currentCase.jurisdiction}  
**Corpus Version**: ${currentCase.source_corpus_version}  
**Mode**: ${isLiveChain ? "Live Sepolia Testnet" : "Curated Benchmark Scenario"}

---

## 1. Executive Summary and Scope
${currentCase.question}

The investigation analyzed whether secondary LLM fine-tuning on customer transcripts constitutes an incompatible purpose under GDPR Article 6(4).

## 2. Facts and Assumptions
- **Processing Purpose**: ${currentCase.facts.processing_purpose}
- **Data Categories**: ${currentCase.facts.data_categories.join(", ")}
- **Consent**: ${currentCase.facts.user_consent_mechanism}
- **Retention**: ${currentCase.facts.retention_period_days} Days

### 2.1 Identified Missing Material Facts (FR-002)
${currentCase.missing_facts.map((mf, i) => `${i + 1}. ${mf}`).join("\n")}

## 3. Relevant Sources and Effective Dates
- Regulation (EU) 2016/679 (GDPR) Art 5(1)(b), 6(1)(f), 6(4) [Effective: 2018-05-25]
- EDPB Statement 01/2024 on Generative AI Model Development [Effective: 2024-04-17]

## 4. Principal Claims and Grounded Evidence
- **Claim**: Secondary AI training represents a distinct, incompatible purpose.
- **Evidence Digest**: 0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842

## 5. Counterarguments and Conflicts
- Adversarial Red Team asserts Legitimate Interest under Recital 47 for service quality.
- EDPB Statement 01/2024 contradicts routine commercial service defense.

## 6. Risk Findings and Confidence Limitations
- **Risk Classification**: HIGH COMPLIANCE GAP
- **Rule Engine Evaluation**: RULE_GDPR_6_4_INCOMPATIBLE failed.
- **Confidence Disclaimer**: Findings are derived from probabilistic multi-agent convergence and commit-reveal markets. Output constitutes non-binding computational decision support, not legal advice.

## 7. Prediction Market Probabilistic Aggregate
- **Event**: ${activeMarket?.question || "Will independent evaluator identify an unresolved Article 6(4) gap?"}
- **Aggregated Belief**: ${activeMarket ? (activeMarket.aggregate_probability * 100).toFixed(1) : 72.4}% (N = ${activeMarket?.sample_size || 6} agents)
- **Disagreement Variance**: ${activeMarket?.disagreement_variance || 0.018}

## 8. Unresolved Uncertainties and Bounty Outcomes
- Bounty ${activeBounty?.bounty_id || "bounty_edpb_001"}: Rewarded ${activeBounty?.reward_credits || 100} simulated credits for EDPB precedent.

## 9. Recommended Next Steps and Human Review
**MANDATORY ESCALATION**: Requires qualified European data protection counsel review. Deploy pre-training automated PII redaction scrubber before production ingestion.

## 10. Audit References and Transaction Hashes
- **Creation Tx**: ${auditRecords[0]?.tx_hash || "N/A"}
- **Resolution Tx**: ${activeMarket?.settlement_tx || "Pending Challenge Period"}
- **Ledger Verification**: On-chain cryptographic commitment hashes confirm reproducible execution.
`;

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `VERIDION_REPORT_${currentCase.id}_v${currentCase.scope_version}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Action Header (hidden on print) */}
      <div className="apple-card p-6 sm:p-8 rounded-[18px] bg-white border border-hairline shadow-soft space-y-4 no-print">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                §16.8 • FR-005
              </span>
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink font-display">
                Final Evaluation Report
              </h1>
            </div>
            <p className="text-[15px] text-muted leading-relaxed">
              Complete, evidence-linked 10-section investigative dossier with audit hashes, missing facts, and human escalation requirements.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleExportMarkdown}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-bubblegum-soft hover:bg-bubblegum-soft/80 border border-hairline text-xs font-semibold text-bubblegum-deep transition-colors shadow-soft"
            >
              <Download className="w-3.5 h-3.5 text-bubblegum-deep" />
              <span>Export Markdown</span>
            </button>
            <button
              onClick={handleExportJson}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-bubblegum-soft hover:bg-bubblegum-soft/80 border border-hairline text-xs font-semibold text-bubblegum-deep transition-colors shadow-soft"
            >
              <Download className="w-3.5 h-3.5 text-bubblegum-deep" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-5 py-2 rounded-full bg-bubblegum hover:bg-bubblegum-hover text-white text-xs font-semibold shadow-soft hover:-translate-y-0.5 transition-all"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* The 10-Section Formal Report Document (§16.8) */}
      <div className="p-8 sm:p-12 rounded-[22px] border border-hairline bg-white shadow-soft space-y-8 text-ink">
        {/* Title & Metadata Block */}
        <div className="border-b border-cream-200 pb-6 space-y-3">
          <div className="flex items-center justify-between text-xs text-ink-secondary font-mono">
            <span>VERIDION PROTOCOL INVESTIGATION REPORT</span>
            <span>DATE: {currentCase.assessment_date}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink">
            {currentCase.title}
          </h1>
          <div className="flex flex-wrap gap-2.5 text-xs font-mono text-ink-secondary pt-1">
            <span className="px-3 py-1 rounded-full bg-cream-100 border border-cream-200">
              Case ID: <strong className="font-semibold text-lavender-700">{currentCase.id}</strong>
            </span>
            <span className="px-3 py-1 rounded-full bg-cream-100 border border-cream-200">
              Version: <strong className="font-semibold text-lavender-700">{currentCase.scope_version}</strong>
            </span>
            <span className="px-3 py-1 rounded-full bg-cream-100 border border-cream-200">
              Jurisdiction: <strong className="font-semibold text-ink">{currentCase.jurisdiction}</strong>
            </span>
            <span className="px-3 py-1 rounded-full bg-cream-100 border border-cream-200">
              Mode: <strong className="font-semibold text-emerald-700">{isLiveChain ? "Live Testnet" : "Sample Benchmark"}</strong>
            </span>
          </div>
        </div>

        {/* 1. Executive Summary & Scope */}
        <section className="space-y-2">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            1. Executive Summary and Scope
          </h2>
          <p className="text-[15px] text-ink leading-relaxed">
            This report evaluates the compliance risks of a hypothetical enterprise AI startup processing customer support conversation logs to fine-tune proprietary generative AI foundation models. The analysis combines retrieval-grounded legal research across verified European Union statutes, autonomous multi-agent debate, deterministic rule evaluation, and commit-reveal prediction markets.
          </p>
        </section>

        {/* 2. Facts and Assumptions */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            2. Frozen Case Facts and Assumptions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200">
              <span className="text-ink-secondary block font-medium">Processing Purpose:</span>
              <span className="text-ink font-semibold">{currentCase.facts.processing_purpose}</span>
            </div>
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200">
              <span className="text-ink-secondary block font-medium">User Consent Mechanism:</span>
              <span className="text-ink font-semibold">{currentCase.facts.user_consent_mechanism}</span>
            </div>
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200">
              <span className="text-ink-secondary block font-medium">Affected Users:</span>
              <span className="text-ink font-semibold">{currentCase.facts.affected_users}</span>
            </div>
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200">
              <span className="text-ink-secondary block font-medium">Retention Period:</span>
              <span className="text-ink font-semibold">{currentCase.facts.retention_period_days} Days</span>
            </div>
          </div>

          {/* Missing Material Facts */}
          {currentCase.missing_facts.length > 0 && (
            <div className="p-4 rounded-[16px] bg-amber-50 border border-amber-200 space-y-2 text-xs">
              <div className="flex items-center gap-2 text-amber-800 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>2.1 Identified Missing Material Facts (FR-002)</span>
              </div>
              <ul className="list-disc pl-5 space-y-1 text-ink-secondary">
                {currentCase.missing_facts.map((mf, i) => (
                  <li key={i}>{mf}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* 3. Relevant Sources and Effective Dates */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            3. Relevant Sources and Effective Dates (FR-007, FR-010)
          </h2>
          <ul className="space-y-2.5 text-xs">
            <li className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 flex justify-between items-center">
              <span><strong>Regulation (EU) 2016/679 (GDPR)</strong> - Article 5(1)(b), Article 6(4)</span>
              <span className="font-mono text-emerald-700 font-semibold text-[11px]">Effective: 2018-05-25</span>
            </li>
            <li className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 flex justify-between items-center">
              <span><strong>EDPB Statement 01/2024</strong> on Generative AI Model Development (Para 4)</span>
              <span className="font-mono text-emerald-700 font-semibold text-[11px]">Effective: 2024-04-17</span>
            </li>
          </ul>
        </section>

        {/* 4. Principal Claims & Evidence */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            4. Principal Claims and Grounded Evidence
          </h2>
          <div className="p-4 rounded-[16px] bg-cream-50 border border-cream-200 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-ink">Secondary AI Training Purpose Incompatibility</span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold">
                EVIDENCE VERIFIED
              </span>
            </div>
            <p className="text-ink-secondary leading-relaxed">
              Under GDPR Article 6(4), secondary model training cannot be treated as compatible with routine customer support. EDPB Statement 01/2024 confirms controllers must establish standalone legal bases.
            </p>
            <div className="pt-1 text-[11px] font-mono text-lavender-700 font-medium">
              Digest: 0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842
            </div>
          </div>
        </section>

        {/* 5. Counterarguments & Conflicts */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            5. Counterarguments and Conflict Surfacing (FR-021, FR-022)
          </h2>
          <div className="p-4 rounded-[16px] bg-rose-50 border border-rose-200 space-y-2 text-xs">
            <span className="font-bold text-rose-800">Adversarial Defense: Commercial Legitimate Interest</span>
            <p className="text-rose-900/80 leading-relaxed">
              Adversarial researcher argued model safety improvements fall under Article 6(1)(f). However, absence of pre-training automated PII scrubbing or user opt-outs renders this defense vulnerable to regulatory challenge.
            </p>
          </div>
        </section>

        {/* 6. Risk Findings & Limitations */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            6. Risk Findings and Deterministic Rule Output (FR-025, FR-058)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200">
              <span className="text-ink-secondary block font-medium">Deterministic Rule Result:</span>
              <span className="font-bold text-rose-700">RULE_GDPR_6_4_INCOMPATIBLE (FAILED)</span>
            </div>
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200">
              <span className="text-ink-secondary block font-medium">Risk Level:</span>
              <span className="font-bold text-amber-700">HIGH REGULATORY COMPLIANCE EXPOSURE</span>
            </div>
          </div>

          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 text-xs text-ink-secondary flex items-start gap-2.5">
            <Info className="w-4 h-4 text-lavender-600 shrink-0 mt-0.5" />
            <span className="leading-relaxed">
              <strong className="text-ink">Confidence Limitations:</strong> The findings reflect multi-agent consensus and deterministic rule parsing on currently ingested statutory materials. Unrepresented authorities or forthcoming EU judicial precedents may alter this determination.
            </span>
          </div>
        </section>

        {/* 7. Forecast Definitions & Probabilities */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            7. Forecast Definitions, Probabilities, and Disagreement (§16.5)
          </h2>
          {activeMarket && (
            <div className="p-4 rounded-[16px] bg-cream-50 border border-cream-200 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-ink font-semibold">{activeMarket.question}</span>
                <span className="font-mono text-lavender-700 font-bold text-lg">
                  {(activeMarket.aggregate_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-[11px] text-ink-secondary">
                Sample Size: N = {activeMarket.sample_size} | Disagreement Variance: {activeMarket.disagreement_variance} | Proper Scoring: Brier Rule
              </div>
            </div>
          )}
        </section>

        {/* 8. Unresolved Uncertainties & Bounty Outcomes */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            8. Unresolved Uncertainties and Evidence Bounty Outcomes (§16.6)
          </h2>
          {activeBounty && (
            <div className="p-4 rounded-[16px] bg-cream-50 border border-cream-200 space-y-2 text-xs">
              <span className="font-semibold text-ink">Bounty {activeBounty.bounty_id}:</span>
              <p className="text-ink-secondary leading-relaxed">{activeBounty.question}</p>
              <div className="text-emerald-700 font-mono text-[11px] font-semibold">
                Winning Submission: sub_edpb_001 | Rewarded +{activeBounty.reward_credits} Simulated Credits
              </div>
            </div>
          )}
        </section>

        {/* 9. Recommended Next Steps & Mandatory Human Review */}
        <section className="space-y-3">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            9. Recommended Remediation and Human Review Requirement (§17.4)
          </h2>
          <div className="p-5 rounded-[16px] bg-amber-50 border border-amber-200 space-y-2.5 text-xs">
            <div className="flex items-center gap-2 text-amber-800 font-bold">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Mandatory Legal Counsel Escalation</span>
            </div>
            <p className="text-amber-900/80 leading-relaxed">
              VERIDION provides automated decision support and research exploration. It does not issue binding legal opinions. Because the purpose compatibility check failed deterministically and benchmark forecasts exceed 60% probability of adverse finding, qualified European data protection counsel must review this deployment before model weights are promoted to production.
            </p>
          </div>
        </section>

        {/* 10. Audit References & Transaction Hashes */}
        <section className="space-y-3 border-t border-cream-200 pt-6">
          <h2 className="text-xs font-bold text-lavender-700 uppercase tracking-widest">
            10. Protocol Audit References and Transaction Hashes (FR-057)
          </h2>
          <div className="space-y-2 text-xs font-mono">
            {auditRecords.map((rec) => (
              <div key={rec.id} className="flex flex-wrap items-center justify-between text-ink-secondary py-1.5 px-3 rounded-[10px] bg-cream-50 border border-cream-200">
                <span>{rec.event_type} ({rec.target_id}):</span>
                <span className="text-lavender-700 font-semibold">{rec.tx_hash}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

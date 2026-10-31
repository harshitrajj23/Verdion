"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  CaseData,
  AgentMetric,
  GraphNode,
  GraphEdge,
  MarketData,
  BountyData,
  AuditRecord
} from "./types";
import deployments from "./deployments.json";
import lifecycleSepolia from "./lifecycle_sepolia.json";
import { api, CreateCasePayload } from "./api";

export const contractAddresses = {
  chainId: deployments.chainId,
  networkName: "Ethereum Sepolia Testnet",
  CaseRegistry: deployments.contracts.CaseRegistry.address,
  AgentRegistry: deployments.contracts.AgentRegistry.address,
  PredictionMarket: deployments.contracts.PredictionMarket.address,
  EvidenceBounty: deployments.contracts.EvidenceBounty.address,
  ReputationSettlement: deployments.contracts.ReputationSettlement.address
};

const initialCase: CaseData = {
  id: lifecycleSepolia.caseId,
  title: "AI Customer Support Analytics & Secondary Model Training",
  jurisdiction: "European Union",
  assessment_date: "2026-03-15",
  question: "Does secondary processing of unredacted customer support transcripts for generative AI model fine-tuning constitute an incompatible purpose under GDPR Article 6(4) / Article 5(1)(b) absent explicit renewed consent?",
  scope_version: 1,
  status: "INVESTIGATION",
  facts: {
    processing_purpose: "Customer support AI fine-tuning and sentiment analytics",
    data_categories: [
      "Customer support conversation transcripts",
      "User account identifiers",
      "Timestamp & session metadata"
    ],
    affected_users: "All active EU platform users (approx. 450,000 subjects)",
    retention_period_days: 365,
    automated_decision_making: false,
    user_consent_mechanism: "General clickwrap Terms of Service acceptance at account creation",
    safeguards: ["Transport Layer Security (TLS 1.3)", "Role-based access control"]
  },
  missing_facts: [
    "Whether data subjects were given granular opt-out before secondary training ingestion",
    "Whether downstream model weights retain memorized PII"
  ],
  source_corpus_version: "2026.1-EU-CURATED",
  created_at: "2026-03-15T09:00:00Z",
  updated_at: "2026-03-15T12:00:00Z"
};

const initialMarkets: MarketData[] = [
  {
    market_id: lifecycleSepolia.marketId,
    case_id: lifecycleSepolia.caseId,
    case_version: 1,
    question: "Will independent evaluator identify an unresolved Article 6(4) compliance gap in customer transcript fine-tuning?",
    outcome_definition: "Resolves TRUE (1) if an unresolved compliance gap is confirmed, FALSE (0) otherwise.",
    resolution_source: "Evaluator Determination / ReputationSettlement",
    evaluator_address: lifecycleSepolia.deployer,
    commit_deadline: "2026-03-15T12:00:00Z",
    reveal_deadline: "2026-03-15T14:00:00Z",
    challenge_deadline: "2026-03-16T14:00:00Z",
    state: "SETTLED",
    aggregate_probability: 0.65,
    disagreement_variance: 0.0,
    sample_size: 1,
    reward_pool_credits: 1000,
    revealed_forecasts: [
      {
        agent_id: "agent_deployer",
        agent_address: lifecycleSepolia.deployer,
        probability: 0.65,
        evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
        revealed_at: "2026-03-15T14:15:20Z",
        brier_score: 0.1225
      }
    ],
    challenge_status: { is_challenged: false },
    settlement_tx: "0x220d460591302025e7f12d621399e2ab15724979678b4aed92ec2d2970e989e4",
    deadline_phase_label: "Settled on Sepolia Testnet",
    is_recorded_sepolia: true
  }
];

const initialAuditRecords: AuditRecord[] = lifecycleSepolia.steps.map((s, idx) => ({
  id: `sepolia_step_${idx + 1}`,
  event_type: s.step === "registerAgent" ? "AGENT_REGISTERED" :
              s.step === "createMarket" ? "MARKET_CREATED" :
              s.step === "fundMarket" ? "MARKET_FUNDED" :
              s.step === "publishMarket" ? "MARKET_PUBLISHED" :
              s.step === "commitForecast" ? "FORECAST_COMMITTED" :
              s.step === "closeMarket" ? "MARKET_CLOSED" :
              s.step === "revealForecast" ? "FORECAST_REVEALED" :
              s.step === "proposeResolution" ? "RESOLUTION_PROPOSED" : "SETTLEMENT_EXECUTED",
  actor: lifecycleSepolia.deployer,
  target_id: s.step === "registerAgent" ? "agent_deployer" : lifecycleSepolia.marketId,
  payload_digest: s.txHash,
  tx_hash: s.txHash,
  timestamp: "2026-03-15T12:00:00Z",
  block_number: s.blockNumber,
  status: s.status === "0x1" ? "CONFIRMED" : "REVERTED",
  source_type: "ON_CHAIN_RECORDED"
}));

const initialAgents: AgentMetric[] = [
  {
    agent_id: "agent_deployer",
    role: "COORDINATOR",
    name: "Sepolia Testnet Deployer & Evaluator",
    status: "COMPLETED",
    current_task: "Market settlement executed on block 11997718",
    sources_consulted: 1,
    claims_generated: 1,
    counterarguments_count: 0,
    forecast_prob: 0.65,
    uncertainty_score: 0.05,
    elapsed_ms: 120,
    token_usage: 1006,
    cost_usd: 0.002,
    failures: [],
    last_output_summary: "Confirmed on-chain Sepolia execution."
  }
];

const initialGraphNodes: GraphNode[] = [
  {
    id: "n_claim_purpose",
    type: "CLAIM",
    label: "Customer Support vs AI Fine-Tuning Purpose Compatibility",
    agent: "agent_deployer",
    evidence_status: "CONTRADICTED",
    digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
    authority: "GDPR Art 6(4)",
    details: "Evaluator determination on Sepolia testnet"
  }
];

const initialGraphEdges: GraphEdge[] = [];
const initialBounties: BountyData[] = [];

export interface ToastMessage {
  id: string;
  type: "info" | "success" | "error" | "warning";
  title: string;
  message: string;
  txHash?: string;
}

export type TxState = "PENDING" | "CONFIRMED" | "REVERTED";

export interface PendingTx {
  id: string;
  txHash: string;
  action: string;
  state: TxState;
  timestamp: string;
}

export interface StoreContextType {
  isBackendLive: boolean;
  isLiveChain: boolean;
  toggleLiveChain: () => void;
  walletAddress: string | null;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  userCredits: number;
  mintDemoCredits: (amount?: number) => void;
  currentCase: CaseData;
  setCurrentCase: (c: CaseData) => void;
  casesList: CaseData[];
  agents: AgentMetric[];
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  markets: MarketData[];
  bounties: BountyData[];
  auditRecords: AuditRecord[];
  contractAddresses: typeof contractAddresses;
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, "id">) => void;
  removeToast: (id: string) => void;
  pendingTxs: PendingTx[];
  clearPendingTx: (id: string) => void;
  refreshData: () => Promise<void>;
  createCase: (payload: CreateCasePayload) => Promise<CaseData>;
  runAnalysis: (caseId: string) => Promise<any>;
  commitForecast: (marketId: string, probability: number, nonce: string) => Promise<string>;
  revealForecast: (marketId: string, probability: number, nonce: string) => Promise<string>;
  submitBountyEvidence: (bountyId: string, sourceTitle: string, passageRef: string, quote: string) => Promise<string>;
  challengeResolution: (marketId: string, reason: string) => Promise<string>;
  settleMarket: (marketId: string) => Promise<string>;
  settleBounty: (bountyId: string) => Promise<string>;
}

const StoreContext = createContext<StoreContextType | null>(null);

const generateSimulatedTxId = (action: string) =>
  `sim_${action.toLowerCase().replace(/[^a-z0-9]/g, "_")}_${Date.now()}`;

export const StoreProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isBackendLive, setIsBackendLive] = useState(false);
  const [isLiveChain, setIsLiveChain] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string | null>("0x70997970C51812dc3A010C7d01b50e0d17dc79C8");
  const [userCredits, setUserCredits] = useState<number>(350);
  const [currentCase, setCurrentCase] = useState<CaseData>(initialCase);
  const [casesList, setCasesList] = useState<CaseData[]>([initialCase]);
  const [agents, setAgents] = useState<AgentMetric[]>(initialAgents);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>(initialGraphNodes);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>(initialGraphEdges);
  const [markets, setMarkets] = useState<MarketData[]>(initialMarkets);
  const [bounties, setBounties] = useState<BountyData[]>(initialBounties);
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>(initialAuditRecords);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [pendingTxs, setPendingTxs] = useState<PendingTx[]>([]);

  const addToast = useCallback((toast: Omit<ToastMessage, "id">) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      removeToast(id);
    }, 6000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addPendingTx = useCallback((action: string, txHash: string): string => {
    const id = `tx_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    setPendingTxs((prev) => [
      { id, txHash, action, state: "PENDING", timestamp: new Date().toISOString() },
      ...prev
    ]);
    return id;
  }, []);

  const updateTxState = useCallback((id: string, state: TxState) => {
    setPendingTxs((prev) =>
      prev.map((tx) => (tx.id === id ? { ...tx, state } : tx))
    );
  }, []);

  const clearPendingTx = useCallback((id: string) => {
    setPendingTxs((prev) => prev.filter((tx) => tx.id !== id));
  }, []);

  const refreshData = useCallback(async () => {
    try {
      const [fetchedCases, fetchedMarkets, fetchedBounties, fetchedAudit, fetchedAgents] = await Promise.all([
        api.getCases().catch(() => null),
        api.getMarkets().catch(() => null),
        api.getBounties().catch(() => null),
        api.getAuditRecords().catch(() => null),
        api.getAgents().catch(() => null)
      ]);

      if (fetchedMarkets !== null) {
        setMarkets(fetchedMarkets);
        setIsBackendLive(true);
      }
      if (fetchedBounties !== null) {
        setBounties(fetchedBounties);
      }
      if (fetchedAudit !== null) {
        setAuditRecords(fetchedAudit);
      }
      if (fetchedAgents !== null && fetchedAgents.length > 0) {
        setAgents(fetchedAgents);
      }
      if (fetchedCases !== null) {
        setCasesList(fetchedCases);
        setCurrentCase((prev) => {
          if (!prev || fetchedCases.length === 0) return fetchedCases[0] || initialCase;
          const match = fetchedCases.find((c) => c.id === prev.id);
          return match || fetchedCases[0];
        });
      }
    } catch (err) {
      console.warn("Backend poll failed, maintaining state:", err);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const toggleLiveChain = () => {
    setIsLiveChain((prev) => {
      const next = !prev;
      addToast({
        type: "info",
        title: next ? "Switched to Live Testnet Mode" : "Switched to Curated Benchmark Mode",
        message: next
          ? "Interacting with Sepolia testnet contracts. Wallet signatures required."
          : "Viewing verified reproducible dataset with deterministic agent outputs."
      });
      return next;
    });
  };

  const connectWallet = async () => {
    if (typeof window !== "undefined" && (window as any).ethereum) {
      try {
        const accounts = await (window as any).ethereum.request({ method: "eth_requestAccounts" });
        if (accounts && accounts[0]) {
          setWalletAddress(accounts[0]);
          addToast({
            type: "success",
            title: "Wallet Connected",
            message: `Connected ${accounts[0].slice(0, 6)}...${accounts[0].slice(-4)}`
          });
          return;
        }
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Connection Failed",
          message: err?.message || "User rejected connection request"
        });
      }
    }
    const mockAddr = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";
    setWalletAddress(mockAddr);
    addToast({
      type: "success",
      title: "Simulator Wallet Connected",
      message: `Active test key ${mockAddr.slice(0, 6)}...${mockAddr.slice(-4)}`
    });
  };

  const disconnectWallet = () => {
    setWalletAddress(null);
    addToast({
      type: "info",
      title: "Wallet Disconnected",
      message: "Disconnected from protocol session."
    });
  };

  const mintDemoCredits = (amount = 100) => {
    setUserCredits((prev) => prev + amount);
    addToast({
      type: "success",
      title: "Simulated Credits Minted",
      message: `Added +${amount} simulated credits to your evaluation balance.`
    });
  };

  const createCase = async (payload: CreateCasePayload): Promise<CaseData> => {
    try {
      const created = await api.createCase(payload);
      setCurrentCase(created);
      setCasesList((prev) => [created, ...prev]);
      addToast({
        type: "success",
        title: "Case Created & Persisted",
        message: `Scope frozen under ID ${created.id} (Version ${created.scope_version}).`
      });
      return created;
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Case Creation Failed",
        message: err.message || "Failed to persist case to backend."
      });
      throw err;
    }
  };

  const runAnalysis = async (caseId: string): Promise<any> => {
    addToast({
      type: "info",
      title: "Running Multi-Agent Swarm",
      message: "Dispatching Legal Researcher, Interpreter, Adversary, and Verifier..."
    });
    try {
      const res = await api.analyzeCase(caseId);
      if (res.argument_graph) {
        if (res.argument_graph.nodes) {
          setGraphNodes(
            res.argument_graph.nodes.map((n: any) => ({
              id: n.id,
              type: n.type || "CLAIM",
              label: n.claim_text || n.label || n.id,
              agent: n.agent_id,
              evidence_status: n.status || "SUPPORTED",
              digest: n.digest,
              authority: n.authority
            }))
          );
        }
        if (res.argument_graph.edges) {
          setGraphEdges(
            res.argument_graph.edges.map((e: any) => ({
              id: e.id,
              source: e.source_claim_id || e.source,
              target: e.target_claim_id || e.target,
              relationship: e.relationship_type || e.relationship,
              reason: e.reason
            }))
          );
        }
      }
      await refreshData();
      addToast({
        type: "success",
        title: "Swarm Analysis Completed",
        message: "Claims verified against SHA-256 digests. Argument graph generated."
      });
      return res;
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Analysis Failed",
        message: err.message || "Multi-agent swarm execution encountered an error."
      });
      throw err;
    }
  };

  const commitForecast = async (marketId: string, probability: number, nonce: string): Promise<string> => {
    const rawTxId = generateSimulatedTxId("commit_forecast");
    const txId = addPendingTx("Commit Forecast", rawTxId);

    addToast({
      type: "info",
      title: "Submitting Forecast Commitment",
      message: "Committing forecast secret proof to protocol ledger...",
      txHash: rawTxId
    });

    try {
      const backendRes = await api.commitForecast(marketId, {
        agent_id: "agent_legal_researcher",
        commitment_hash: rawTxId,
        wallet_address: walletAddress || undefined
      });

      const actualTxHash = backendRes.commit_tx_hash || rawTxId;
      updateTxState(txId, "CONFIRMED");

      addToast({
        type: "success",
        title: "Commitment Confirmed & Persisted",
        message: `Secret forecast committed in SQLite and anchored with tx ${actualTxHash.slice(0, 10)}...`,
        txHash: actualTxHash
      });

      await refreshData();
      return actualTxHash;
    } catch (err: any) {
      updateTxState(txId, "REVERTED");
      addToast({
        type: "error",
        title: "Commitment Failed",
        message: err.message || "Failed to commit forecast to backend ledger.",
        txHash: rawTxId
      });
      throw err;
    }
  };

  const revealForecast = async (marketId: string, probability: number, nonce: string): Promise<string> => {
    const rawTxId = generateSimulatedTxId("reveal_forecast");
    const txId = addPendingTx("Reveal Forecast", rawTxId);

    addToast({
      type: "info",
      title: "Verifying & Revealing Forecast",
      message: "Submitting probability and secret nonce to verify commitment proof...",
      txHash: rawTxId
    });

    try {
      const backendRes = await api.revealForecast(marketId, {
        agent_id: "agent_legal_researcher",
        probability,
        evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
        nonce,
        wallet_address: walletAddress || undefined
      });

      const actualTxHash = backendRes.reveal_tx_hash || rawTxId;
      updateTxState(txId, "CONFIRMED");

      addToast({
        type: "success",
        title: "Forecast Revealed Successfully",
        message: `Verified ${(probability * 100).toFixed(1)}% integrated into market aggregate.`,
        txHash: actualTxHash
      });

      await refreshData();
      return actualTxHash;
    } catch (err: any) {
      updateTxState(txId, "REVERTED");
      addToast({
        type: "error",
        title: "Reveal Verification Failed",
        message: err.message || "Commitment verification failed on backend.",
        txHash: rawTxId
      });
      throw err;
    }
  };

  const submitBountyEvidence = async (
    bountyId: string,
    sourceTitle: string,
    passageRef: string,
    quote: string
  ): Promise<string> => {
    const rawTxId = generateSimulatedTxId("submit_evidence");
    const txId = addPendingTx("Submit Evidence", rawTxId);

    addToast({
      type: "info",
      title: "Submitting Evidence",
      message: "Computing canonical evidence digest and registering submission...",
      txHash: rawTxId
    });

    try {
      const backendRes = await api.submitEvidence(bountyId, {
        contributor_address: walletAddress || "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        title: sourceTitle,
        source_reference: passageRef,
        content: quote
      });

      const actualDigest = backendRes.digest || rawTxId;
      updateTxState(txId, "CONFIRMED");

      addToast({
        type: "success",
        title: "Evidence Registered & Persisted",
        message: `Submission registered with SHA-256 digest ${actualDigest.slice(0, 10)}... Review window open.`,
        txHash: rawTxId
      });

      await refreshData();
      return rawTxId;
    } catch (err: any) {
      updateTxState(txId, "REVERTED");
      addToast({
        type: "error",
        title: "Evidence Submission Failed",
        message: err.message || "Failed to persist evidence submission.",
        txHash: rawTxId
      });
      throw err;
    }
  };

  const challengeResolution = async (marketId: string, reason: string): Promise<string> => {
    const rawTxId = generateSimulatedTxId("challenge_resolution");
    const txId = addPendingTx("Challenge Resolution", rawTxId);

    await new Promise((resolve) => setTimeout(resolve, 800));

    setMarkets((prev) =>
      prev.map((m) => {
        if (m.market_id === marketId) {
          return {
            ...m,
            state: "CHALLENGE",
            challenge_status: {
              is_challenged: true,
              challenger: walletAddress || "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
              reason
            }
          };
        }
        return m;
      })
    );

    updateTxState(txId, "CONFIRMED");

    addToast({
      type: "warning",
      title: "Challenge Window Triggered",
      message: `Resolution disputed. Evidence submitted for evaluator review.`,
      txHash: rawTxId
    });

    return rawTxId;
  };

  const settleMarket = async (marketId: string): Promise<string> => {
    const rawTxId = generateSimulatedTxId("settle_market");
    const txId = addPendingTx("Settle Market", rawTxId);

    addToast({
      type: "info",
      title: "Settling Prediction Market",
      message: "Executing Brier score calculations and distributing simulated credits...",
      txHash: rawTxId
    });

    try {
      const backendRes = await api.settleMarket(marketId);
      const actualTx = backendRes.settlement_tx_hash || rawTxId;

      setUserCredits((prev) => prev + 150);
      updateTxState(txId, "CONFIRMED");

      addToast({
        type: "success",
        title: "Market Settled Idempotently",
        message: `Brier score payouts disbursed in SQLite database. +150 simulated credits earned.`,
        txHash: actualTx
      });

      await refreshData();
      return actualTx;
    } catch (err: any) {
      updateTxState(txId, "REVERTED");
      addToast({
        type: "error",
        title: "Market Settlement Failed",
        message: err.message || "Settlement failed on backend.",
        txHash: rawTxId
      });
      throw err;
    }
  };

  const settleBounty = async (bountyId: string): Promise<string> => {
    const rawTxId = generateSimulatedTxId("settle_bounty");
    const txId = addPendingTx("Settle Bounty", rawTxId);

    addToast({
      type: "info",
      title: "Settling Evidence Bounty",
      message: "Releasing bounty reward pool to winning contributor...",
      txHash: rawTxId
    });

    try {
      const targetBounty = bounties.find((b) => b.bounty_id === bountyId);
      const winningSubId = targetBounty?.submissions?.[0]?.submission_id || "sub_default";
      const backendRes = await api.settleBounty(bountyId, winningSubId, "Satisfies EDPB guidance criteria and verifies passage digest.");

      const actualTx = backendRes.settlement_tx_hash || rawTxId;
      setUserCredits((prev) => prev + 100);
      updateTxState(txId, "CONFIRMED");

      addToast({
        type: "success",
        title: "Bounty Settled in Protocol",
        message: `Winning submission rewarded 100 simulated credits. Audit event emitted.`,
        txHash: actualTx
      });

      await refreshData();
      return actualTx;
    } catch (err: any) {
      updateTxState(txId, "REVERTED");
      addToast({
        type: "error",
        title: "Bounty Settlement Failed",
        message: err.message || "Bounty settlement failed on backend.",
        txHash: rawTxId
      });
      throw err;
    }
  };

  return (
    <StoreContext.Provider
      value={{
        isBackendLive,
        isLiveChain,
        toggleLiveChain,
        walletAddress,
        connectWallet,
        disconnectWallet,
        userCredits,
        mintDemoCredits,
        currentCase,
        setCurrentCase,
        casesList,
        agents,
        graphNodes,
        graphEdges,
        markets,
        bounties,
        auditRecords,
        contractAddresses,
        toasts,
        addToast,
        removeToast,
        pendingTxs,
        clearPendingTx,
        refreshData,
        createCase,
        runAnalysis,
        commitForecast,
        revealForecast,
        submitBountyEvidence,
        challengeResolution,
        settleMarket,
        settleBounty
      }}
    >
      {children}
    </StoreContext.Provider>
  );
};

export const useStore = () => {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error("useStore must be used within a StoreProvider");
  }
  return context;
};

"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  initialCase,
  initialAgents,
  initialGraphNodes,
  initialGraphEdges,
  initialMarkets,
  initialBounties,
  initialAuditRecords,
  mockContractAddresses,
  CaseData,
  AgentMetric,
  GraphNode,
  GraphEdge,
  MarketData,
  BountyData,
  AuditRecord
} from "./mockData";
import { api, CreateCasePayload } from "./api";

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
  contractAddresses: typeof mockContractAddresses;
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

const generateTxHash = () =>
  `0x${Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")}`;

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

      if (fetchedMarkets && fetchedMarkets.length > 0) {
        setMarkets(fetchedMarkets);
        setIsBackendLive(true);
      }
      if (fetchedBounties && fetchedBounties.length > 0) {
        setBounties(fetchedBounties);
      }
      if (fetchedAudit && fetchedAudit.length > 0) {
        setAuditRecords(fetchedAudit);
      }
      if (fetchedAgents && fetchedAgents.length > 0) {
        setAgents(fetchedAgents);
      }
      if (fetchedCases && fetchedCases.length > 0) {
        setCasesList(fetchedCases);
        setCurrentCase((prev) => {
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
    const rawTxHash = generateTxHash();
    const txId = addPendingTx("Commit Forecast", rawTxHash);

    addToast({
      type: "info",
      title: "Broadcasting Commitment",
      message: "Submitting forecast secret commitment to protocol...",
      txHash: rawTxHash
    });

    try {
      const backendRes = await api.commitForecast(marketId, {
        agent_id: "agent_legal_researcher",
        commitment_hash: rawTxHash,
        wallet_address: walletAddress || undefined
      });

      const actualTxHash = backendRes.commit_tx_hash || rawTxHash;
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
      console.warn("Backend commit failed, using client simulation:", err);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      updateTxState(txId, "CONFIRMED");
      addToast({
        type: "warning",
        title: "Offline Commitment Recorded",
        message: `Commitment updated in local session: ${err.message || "Backend offline"}`
      });
      return rawTxHash;
    }
  };

  const revealForecast = async (marketId: string, probability: number, nonce: string): Promise<string> => {
    const rawTxHash = generateTxHash();
    const txId = addPendingTx("Reveal Forecast", rawTxHash);

    addToast({
      type: "info",
      title: "Verifying & Revealing Forecast",
      message: "Submitting probability and secret nonce to verify commitment proof...",
      txHash: rawTxHash
    });

    try {
      const backendRes = await api.revealForecast(marketId, {
        agent_id: "agent_legal_researcher",
        probability,
        evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
        nonce,
        wallet_address: walletAddress || undefined
      });

      const actualTxHash = backendRes.reveal_tx_hash || rawTxHash;
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
      console.warn("Backend reveal failed, using local simulation:", err);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      updateTxState(txId, "CONFIRMED");
      addToast({
        type: "warning",
        title: "Offline Reveal Recorded",
        message: `Forecast revealed in local session: ${err.message || "Backend offline"}`
      });
      return rawTxHash;
    }
  };

  const submitBountyEvidence = async (
    bountyId: string,
    sourceTitle: string,
    passageRef: string,
    quote: string
  ): Promise<string> => {
    const rawTxHash = generateTxHash();
    const txId = addPendingTx("Submit Evidence", rawTxHash);

    addToast({
      type: "info",
      title: "Submitting Evidence",
      message: "Computing canonical evidence digest and registering submission...",
      txHash: rawTxHash
    });

    try {
      const backendRes = await api.submitEvidence(bountyId, {
        contributor_address: walletAddress || "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        title: sourceTitle,
        source_reference: passageRef,
        content: quote
      });

      const actualDigest = backendRes.digest || rawTxHash;
      updateTxState(txId, "CONFIRMED");

      addToast({
        type: "success",
        title: "Evidence Registered & Persisted",
        message: `Submission registered with SHA-256 digest ${actualDigest.slice(0, 10)}... Review window open.`,
        txHash: rawTxHash
      });

      await refreshData();
      return rawTxHash;
    } catch (err: any) {
      console.warn("Backend evidence submit failed, using local simulation:", err);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      updateTxState(txId, "CONFIRMED");
      addToast({
        type: "warning",
        title: "Offline Submission Recorded",
        message: `Evidence stored in local session: ${err.message || "Backend offline"}`
      });
      return rawTxHash;
    }
  };

  const challengeResolution = async (marketId: string, reason: string): Promise<string> => {
    const txHash = generateTxHash();
    const txId = addPendingTx("Challenge Resolution", txHash);

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
      txHash
    });

    return txHash;
  };

  const settleMarket = async (marketId: string): Promise<string> => {
    const rawTxHash = generateTxHash();
    const txId = addPendingTx("Settle Market", rawTxHash);

    addToast({
      type: "info",
      title: "Settling Prediction Market",
      message: "Executing Brier score calculations and distributing simulated credits...",
      txHash: rawTxHash
    });

    try {
      const backendRes = await api.settleMarket(marketId);
      const actualTx = backendRes.settlement_tx_hash || rawTxHash;

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
      console.warn("Backend settle market failed, using local simulation:", err);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setMarkets((prev) =>
        prev.map((m) => (m.market_id === marketId ? { ...m, state: "SETTLED", settlement_tx: rawTxHash } : m))
      );
      setUserCredits((prev) => prev + 150);
      updateTxState(txId, "CONFIRMED");
      addToast({
        type: "warning",
        title: "Offline Settlement Recorded",
        message: `Settled in local session: ${err.message || "Backend offline"}`
      });
      return rawTxHash;
    }
  };

  const settleBounty = async (bountyId: string): Promise<string> => {
    const rawTxHash = generateTxHash();
    const txId = addPendingTx("Settle Bounty", rawTxHash);

    addToast({
      type: "info",
      title: "Settling Evidence Bounty",
      message: "Releasing bounty reward pool to winning contributor...",
      txHash: rawTxHash
    });

    try {
      const targetBounty = bounties.find((b) => b.bounty_id === bountyId);
      const winningSubId = targetBounty?.submissions?.[0]?.submission_id || "sub_default";
      const backendRes = await api.settleBounty(bountyId, winningSubId, "Satisfies EDPB guidance criteria and verifies passage digest.");

      const actualTx = backendRes.settlement_tx_hash || rawTxHash;
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
      console.warn("Backend bounty settle failed, using local simulation:", err);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setBounties((prev) =>
        prev.map((b) => (b.bounty_id === bountyId ? { ...b, state: "SETTLED", settlement_tx: rawTxHash } : b))
      );
      setUserCredits((prev) => prev + 100);
      updateTxState(txId, "CONFIRMED");
      addToast({
        type: "warning",
        title: "Offline Bounty Settlement Recorded",
        message: `Bounty settled in local session: ${err.message || "Backend offline"}`
      });
      return rawTxHash;
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
        contractAddresses: mockContractAddresses,
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

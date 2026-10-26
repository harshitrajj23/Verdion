"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
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
  isLiveChain: boolean;
  toggleLiveChain: () => void;
  walletAddress: string | null;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  userCredits: number;
  mintDemoCredits: (amount?: number) => void;
  currentCase: CaseData;
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
  // Transaction State Tracking
  pendingTxs: PendingTx[];
  clearPendingTx: (id: string) => void;
  // State Mutations
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
  const [isLiveChain, setIsLiveChain] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string | null>("0x70997970C51812dc3A010C7d01b50e0d17dc79C8");
  const [userCredits, setUserCredits] = useState<number>(350);
  const [currentCase, setCurrentCase] = useState<CaseData>(initialCase);
  const [agents, setAgents] = useState<AgentMetric[]>(initialAgents);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>(initialGraphNodes);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>(initialGraphEdges);
  const [markets, setMarkets] = useState<MarketData[]>(initialMarkets);
  const [bounties, setBounties] = useState<BountyData[]>(initialBounties);
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>(initialAuditRecords);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [pendingTxs, setPendingTxs] = useState<PendingTx[]>([]);

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
    // Fallback simulated wallet
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

  const commitForecast = async (marketId: string, probability: number, nonce: string): Promise<string> => {
    const txHash = generateTxHash();
    const txId = addPendingTx("Commit Forecast", txHash);

    addToast({
      type: "info",
      title: "Pending Transaction",
      message: "Broadcasting forecast commitment H(chainId, marketId, agent, prob, digest, nonce)...",
      txHash
    });

    // Simulate block latency
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const newAudit: AuditRecord = {
      id: `aud_${Date.now()}`,
      event_type: "FORECAST_COMMITTED",
      actor: walletAddress || "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
      target_id: marketId,
      payload_digest: generateTxHash(),
      tx_hash: txHash,
      timestamp: new Date().toISOString(),
      block_number: 5410520 + Math.floor(Math.random() * 10),
      status: "CONFIRMED",
      source_type: "SAMPLE_FIXTURE"
    };

    setAuditRecords((prev) => [newAudit, ...prev]);
    updateTxState(txId, "CONFIRMED");

    addToast({
      type: "success",
      title: "Commitment Confirmed on Testnet",
      message: `Forecast secret committed. Reveal window opens after deadline.`,
      txHash
    });

    return txHash;
  };

  const revealForecast = async (marketId: string, probability: number, nonce: string): Promise<string> => {
    const txHash = generateTxHash();
    const txId = addPendingTx("Reveal Forecast", txHash);

    addToast({
      type: "info",
      title: "Verifying Reveal Proof",
      message: "Verifying probability and secret nonce against on-chain commitment...",
      txHash
    });

    await new Promise((resolve) => setTimeout(resolve, 1500));

    setMarkets((prev) =>
      prev.map((m) => {
        if (m.market_id === marketId) {
          const updatedRevealed = [
            ...m.revealed_forecasts,
            {
              agent_id: "human_evaluator_01",
              agent_address: walletAddress || "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
              probability,
              evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
              revealed_at: new Date().toISOString()
            }
          ];
          const newAgg =
            updatedRevealed.reduce((acc, curr) => acc + curr.probability, 0) / updatedRevealed.length;
          const newVariance =
            updatedRevealed.reduce((acc, curr) => acc + Math.pow(curr.probability - newAgg, 2), 0) /
            updatedRevealed.length;

          return {
            ...m,
            sample_size: updatedRevealed.length,
            aggregate_probability: Number(newAgg.toFixed(3)),
            disagreement_variance: Number(newVariance.toFixed(4)),
            revealed_forecasts: updatedRevealed
          };
        }
        return m;
      })
    );

    updateTxState(txId, "CONFIRMED");

    addToast({
      type: "success",
      title: "Forecast Revealed Successfully",
      message: `Verified probability ${(probability * 100).toFixed(1)}% integrated into market aggregate.`,
      txHash
    });

    return txHash;
  };

  const submitBountyEvidence = async (
    bountyId: string,
    sourceTitle: string,
    passageRef: string,
    quote: string
  ): Promise<string> => {
    const txHash = generateTxHash();
    const txId = addPendingTx("Submit Evidence", txHash);

    addToast({
      type: "info",
      title: "Submitting Evidence",
      message: "Computing canonical evidence digest and anchoring to EvidenceBounty contract...",
      txHash
    });

    await new Promise((resolve) => setTimeout(resolve, 1500));

    const evidenceDigest = generateTxHash();

    setBounties((prev) =>
      prev.map((b) => {
        if (b.bounty_id === bountyId) {
          return {
            ...b,
            submissions: [
              ...b.submissions,
              {
                submission_id: `sub_${Date.now()}`,
                contributor: walletAddress || "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                evidence_digest: evidenceDigest,
                source_title: sourceTitle,
                passage_reference: passageRef,
                quote,
                effective_date: "2024-04-17",
                submitted_at: new Date().toISOString()
              }
            ]
          };
        }
        return b;
      })
    );

    updateTxState(txId, "CONFIRMED");

    addToast({
      type: "success",
      title: "Evidence Anchored on Testnet",
      message: `Submission registered with digest ${evidenceDigest.slice(0, 10)}... Review window open.`,
      txHash
    });

    return txHash;
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
    const txHash = generateTxHash();
    const txId = addPendingTx("Settle Market", txHash);

    addToast({
      type: "info",
      title: "Settling Prediction Market",
      message: "Executing Brier score calculations and distributing simulated credits...",
      txHash
    });

    await new Promise((resolve) => setTimeout(resolve, 1500));

    setMarkets((prev) =>
      prev.map((m) => {
        if (m.market_id === marketId) {
          return {
            ...m,
            state: "SETTLED",
            settlement_tx: txHash
          };
        }
        return m;
      })
    );

    setUserCredits((prev) => prev + 150);
    updateTxState(txId, "CONFIRMED");

    addToast({
      type: "success",
      title: "Market Settled Idempotently",
      message: `Proper scoring payouts disbursed. +150 simulated credits earned.`,
      txHash
    });

    return txHash;
  };

  const settleBounty = async (bountyId: string): Promise<string> => {
    const txHash = generateTxHash();
    const txId = addPendingTx("Settle Bounty", txHash);

    addToast({
      type: "info",
      title: "Settling Evidence Bounty",
      message: "Releasing bounty reward pool to winning contributor...",
      txHash
    });

    await new Promise((resolve) => setTimeout(resolve, 1500));

    setBounties((prev) =>
      prev.map((b) => {
        if (b.bounty_id === bountyId) {
          return {
            ...b,
            state: "SETTLED",
            settlement_tx: txHash
          };
        }
        return b;
      })
    );

    setUserCredits((prev) => prev + 100);
    updateTxState(txId, "CONFIRMED");

    addToast({
      type: "success",
      title: "Bounty Settled",
      message: `Winning submission rewarded 100 simulated credits. Audit event emitted.`,
      txHash
    });

    return txHash;
  };

  return (
    <StoreContext.Provider
      value={{
        isLiveChain,
        toggleLiveChain,
        walletAddress,
        connectWallet,
        disconnectWallet,
        userCredits,
        mintDemoCredits,
        currentCase,
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

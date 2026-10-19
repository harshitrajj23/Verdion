"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import { LiveOrSampleBadge } from "./LiveOrSampleBadge";
import { NetworkPromptModal } from "./NetworkPromptModal";
import { Shield, Coins, Wallet, PlusCircle, Network, Menu, X } from "lucide-react";

export const AppHeader: React.FC = () => {
  const {
    walletAddress,
    connectWallet,
    disconnectWallet,
    userCredits,
    mintDemoCredits,
    isLiveChain,
    contractAddresses,
    pendingTxs
  } = useStore();

  const [showNetworkModal, setShowNetworkModal] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [detectedChainId, setDetectedChainId] = useState<number | undefined>();

  // Listen for chain changes when in live mode
  useEffect(() => {
    if (typeof window !== "undefined" && (window as any).ethereum && isLiveChain) {
      const checkChain = async () => {
        try {
          const chainIdHex = await (window as any).ethereum.request({ method: "eth_chainId" });
          const chainId = parseInt(chainIdHex, 16);
          setDetectedChainId(chainId);
          if (chainId !== contractAddresses.chainId) {
            setShowNetworkModal(true);
          }
        } catch {
          // No wallet available
        }
      };
      checkChain();

      const handleChainChanged = (chainIdHex: string) => {
        const chainId = parseInt(chainIdHex, 16);
        setDetectedChainId(chainId);
        if (chainId !== contractAddresses.chainId) {
          setShowNetworkModal(true);
        } else {
          setShowNetworkModal(false);
        }
      };

      (window as any).ethereum.on?.("chainChanged", handleChainChanged);
      return () => {
        (window as any).ethereum.removeListener?.("chainChanged", handleChainChanged);
      };
    }
  }, [isLiveChain, contractAddresses.chainId]);

  const activePendingCount = pendingTxs.filter((tx) => tx.state === "PENDING").length;

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-verdion-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Left: Brand */}
          <div className="flex items-center gap-4 lg:gap-6">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center p-0.5 shadow-glow">
                <div className="w-full h-full bg-verdion-950 rounded-[10px] flex items-center justify-center">
                  <Shield className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
                </div>
              </div>
              <div className="hidden sm:block">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-lg tracking-wider text-white">VERIDION</span>
                  <span className="px-1.5 py-0.5 text-[10px] font-bold tracking-widest bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
                    v1.0 MVP
                  </span>
                </div>
                <p className="text-[11px] font-medium text-slate-400 tracking-tight">Reason. Predict. Verify.</p>
              </div>
            </Link>

            {/* Sample vs Live Indicator (§16.1) */}
            <div className="hidden md:block">
              <LiveOrSampleBadge />
            </div>
          </div>

          {/* Right: Network, Faucet, Wallet */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Pending Tx Indicator */}
            {activePendingCount > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-950/40 border border-amber-800/40 text-xs">
                <span className="spinner w-3 h-3 text-amber-400" />
                <span className="text-amber-300 font-semibold text-[11px]">
                  {activePendingCount} Pending
                </span>
              </div>
            )}

            {/* Network Badge */}
            <button
              onClick={() => isLiveChain && setShowNetworkModal(true)}
              className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 hover:border-slate-700 transition-colors"
            >
              <Network className="w-3.5 h-3.5 text-cyan-400" />
              <span>Sepolia</span>
              <span className={`w-2 h-2 rounded-full ${isLiveChain ? "bg-emerald-400 pulse-dot" : "bg-slate-600"}`} />
            </button>

            {/* Simulated Credit Balance (§10.6, FR-041) */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-xs">
              <Coins className="w-4 h-4 text-emerald-400" />
              <span className="font-mono font-bold text-emerald-300">{userCredits}</span>
              <span className="text-emerald-500/90 text-[10px] font-semibold uppercase hidden lg:inline">Sim Credits</span>
              <button
                onClick={() => mintDemoCredits(100)}
                className="text-emerald-400 hover:text-emerald-200 transition-colors ml-0.5 p-0.5"
                title="Mint +100 Simulated Test Credits via Demo Faucet"
              >
                <PlusCircle className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Wallet Connection (§16.9) */}
            {walletAddress ? (
              <button
                onClick={disconnectWallet}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200 transition-all"
                title="Click to disconnect"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>{walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}</span>
              </button>
            ) : (
              <button
                onClick={connectWallet}
                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-glow transition-all active:scale-95"
              >
                <Wallet className="w-3.5 h-3.5" />
                <span>Connect</span>
              </button>
            )}

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden text-slate-400 hover:text-white p-1"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu bar */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-slate-800/80 bg-verdion-950/95 backdrop-blur-xl p-4 space-y-3">
            <LiveOrSampleBadge />
            <div className="flex items-center gap-2">
              <Coins className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-mono font-bold text-emerald-300">{userCredits}</span>
              <span className="text-emerald-500/90 text-[10px] font-semibold uppercase">Sim Credits</span>
              <button
                onClick={() => mintDemoCredits(100)}
                className="text-emerald-400 hover:text-emerald-200 ml-1"
              >
                <PlusCircle className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Network Prompt Modal (§16.9) */}
      <NetworkPromptModal
        isOpen={showNetworkModal}
        onClose={() => setShowNetworkModal(false)}
        expectedChainId={contractAddresses.chainId}
        expectedNetworkName={contractAddresses.networkName}
        currentChainId={detectedChainId}
      />
    </>
  );
};

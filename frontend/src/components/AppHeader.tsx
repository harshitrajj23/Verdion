"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useStore } from "@/lib/store";
import { LiveOrSampleBadge } from "./LiveOrSampleBadge";
import { NetworkPromptModal } from "./NetworkPromptModal";
import {
  Shield,
  Coins,
  Wallet,
  PlusCircle,
  Network,
  Menu,
  X,
  Layers,
  Sparkles,
  ChevronRight
} from "lucide-react";

const subNavTabs = [
  { href: "/", label: "Overview" },
  { href: "/cases", label: "Cases" },
  { href: "/sources", label: "Legal Sources" },
  { href: "/agents", label: "Agents" },
  { href: "/graph", label: "Argument Graph" },
  { href: "/markets", label: "Markets" },
  { href: "/bounties", label: "Bounties" },
  { href: "/audit", label: "Audit" },
  { href: "/report", label: "Final Report" },
  { href: "/benchmark", label: "Benchmark" },
];

export const AppHeader: React.FC = () => {
  const pathname = usePathname();
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
      {/* ── Tier 1: Apple Global Navigation Bar (height: 44px, design.md §global-nav) ── */}
      <nav className="w-full h-11 bg-tile-dark text-cream-100 border-b border-tile-border/70 z-50 text-[12px] font-normal tracking-[-0.01em]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
          {/* Brand mark & Protocol Identity */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2 group transition-opacity hover:opacity-85">
              <div className="w-5 h-5 rounded-full bg-lavender-500/20 border border-lavender-400/40 flex items-center justify-center">
                <Shield className="w-3 h-3 text-lavender-300" />
              </div>
              <span className="font-semibold tracking-tight text-white">VERIDION</span>
            </Link>

            <div className="hidden md:flex items-center gap-4 text-cream-400 text-[11px]">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-lavender-400" />
                EU Legal Intelligence
              </span>
              <span>•</span>
              <span>Corpus v2026.1</span>
              <span>•</span>
              <span className="font-mono text-lavender-300">Commit-Reveal v1.0</span>
            </div>
          </div>

          {/* Right Global Actions */}
          <div className="flex items-center gap-3">
            {/* Pending Txs */}
            {activePendingCount > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-950/80 border border-amber-600/50 text-amber-200 text-[11px] font-medium">
                <span className="spinner w-2.5 h-2.5 text-amber-300" />
                <span>{activePendingCount} pending</span>
              </div>
            )}

            {/* Network indicator pill */}
            <button
              onClick={() => isLiveChain && setShowNetworkModal(true)}
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-tile-dark2 hover:bg-tile-dark3 border border-tile-border text-cream-300 text-[11px] transition-colors"
            >
              <Network className="w-3 h-3 text-lavender-400" />
              <span>Sepolia</span>
              <span className={`w-1.5 h-1.5 rounded-full ${isLiveChain ? "bg-lavender-400 pulse-dot" : "bg-cream-600"}`} />
            </button>

            {/* Demo Faucet Credits */}
            <div className="flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-lavender-900/40 border border-lavender-700/50 text-cream-100 text-[11px]">
              <Coins className="w-3 h-3 text-lavender-300" />
              <span className="font-mono font-semibold text-lavender-200">{userCredits}</span>
              <span className="text-cream-400 text-[10px] hidden md:inline">Sim</span>
              <button
                onClick={() => mintDemoCredits(100)}
                className="text-lavender-300 hover:text-white transition-colors ml-0.5"
                title="Mint +100 Simulated Test Credits"
              >
                <PlusCircle className="w-3 h-3" />
              </button>
            </div>

            {/* Wallet Connect Pill */}
            {walletAddress ? (
              <button
                onClick={disconnectWallet}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-tile-dark2 hover:bg-tile-dark3 border border-tile-border text-cream-200 text-[11px] font-mono transition-colors active:scale-[0.97]"
                title="Click to disconnect"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-lavender-400" />
                <span>{walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}</span>
              </button>
            ) : (
              <button
                onClick={connectWallet}
                className="flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-lavender-600 hover:bg-lavender-500 text-white text-[11px] font-medium shadow-apple-pill transition-all active:scale-[0.97]"
              >
                <Wallet className="w-3 h-3" />
                <span>Connect</span>
              </button>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden text-cream-400 hover:text-white p-1 ml-1"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </nav>

      {/* ── Tier 2: Apple Sub-Nav Frosted Glass (height: 52px, design.md §sub-nav-frosted) ── */}
      <header className="sticky top-0 z-40 w-full apple-frosted-nav">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[52px] flex items-center justify-between gap-4">
          {/* Section Category Title */}
          <div className="flex items-center gap-4 shrink-0">
            <Link href="/" className="font-appleDisplay font-semibold text-lg text-ink tracking-tight hover:opacity-85 transition-opacity">
              Legal Intelligence
            </Link>
          </div>

          {/* Horizontal Apple Pill Navigation Tabs */}
          <nav className="hidden lg:flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
            {subNavTabs.map((tab) => {
              const isActive = pathname === tab.href;
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  className={`px-3 py-1.5 rounded-full text-[13px] font-medium tracking-tight transition-all duration-150 active:scale-[0.97] whitespace-nowrap ${
                    isActive
                      ? "bg-lavender-600 text-white shadow-apple-pill"
                      : "text-ink-secondary hover:text-ink hover:bg-cream-200/80"
                  }`}
                >
                  {tab.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Action: Live vs Sample Capsule Badge */}
          <div className="flex items-center gap-2 shrink-0">
            <LiveOrSampleBadge />
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-cream-300 bg-cream-100/98 backdrop-blur-xl p-4 space-y-2 animate-fade-in-up shadow-apple">
            <div className="grid grid-cols-2 gap-1.5 pb-3 border-b border-cream-300">
              {subNavTabs.map((tab) => {
                const isActive = pathname === tab.href;
                return (
                  <Link
                    key={tab.href}
                    href={tab.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`px-3 py-2 rounded-xl text-xs font-medium text-center transition-all ${
                      isActive
                        ? "bg-lavender-600 text-white shadow-sm"
                        : "bg-cream-200 text-ink-secondary hover:bg-cream-300 hover:text-ink"
                    }`}
                  >
                    {tab.label}
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </header>

      {/* Network Prompt Modal */}
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


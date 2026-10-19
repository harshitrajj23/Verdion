"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Cpu,
  GitFork,
  TrendingUp,
  Gift,
  FileCheck2,
  FileText,
  BarChart3,
  ExternalLink
} from "lucide-react";

const navigationItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, section: "§16.1" },
  { href: "/cases", label: "Case Workspace", icon: Briefcase, section: "§16.2" },
  { href: "/agents", label: "Agent Laboratory", icon: Cpu, section: "§16.3" },
  { href: "/graph", label: "Argument Graph", icon: GitFork, section: "§16.4" },
  { href: "/markets", label: "Prediction Markets", icon: TrendingUp, section: "§16.5" },
  { href: "/bounties", label: "Evidence Bounties", icon: Gift, section: "§16.6" },
  { href: "/audit", label: "Audit Explorer", icon: FileCheck2, section: "§16.7" },
  { href: "/report", label: "Final Report", icon: FileText, section: "§16.8" },
  { href: "/benchmark", label: "Benchmark & Baselines", icon: BarChart3, section: "§18.1" }
];

export const AppSidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 hidden lg:block border-r border-slate-800/80 bg-verdion-950/50 p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Protocol Workspace
          </p>
          <nav className="space-y-1">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                    isActive
                      ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 shadow-glow"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/60 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-4 h-4 transition-colors ${
                        isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-slate-200"
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                      isActive
                        ? "bg-emerald-500/20 text-emerald-400 font-bold"
                        : "text-slate-600 group-hover:text-slate-500"
                    }`}
                  >
                    {item.section}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Protocol Metadata Card */}
        <div className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 text-[11px] space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span>Jurisdiction</span>
            <span className="font-semibold text-slate-200">European Union</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Corpus Version</span>
            <span className="font-mono text-emerald-400">2026.1.0</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Commit Hash</span>
            <span className="font-mono text-cyan-400">0x8fa12b...</span>
          </div>
          <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-500 leading-relaxed">
            VERIDION is decision support; it does not replace qualified legal counsel.
          </div>
        </div>
      </div>
    </aside>
  );
};

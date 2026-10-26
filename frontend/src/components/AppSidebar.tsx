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
  ShieldCheck
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
    <aside className="w-64 shrink-0 hidden lg:block border-r border-cream-300/80 bg-cream-100/40 p-4 min-h-[calc(100vh-6rem)]">
      <div className="space-y-6">
        <div>
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-ink-muted mb-2 font-appleDisplay">
            Protocol Workspaces
          </p>
          <nav className="space-y-1">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3.5 py-2 rounded-full text-xs transition-all duration-150 active:scale-[0.97] group ${
                    isActive
                      ? "bg-lavender-100 text-lavender-800 font-semibold border border-lavender-200 shadow-sm"
                      : "text-ink-secondary hover:text-ink hover:bg-cream-200/70 border border-transparent font-normal"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={`w-3.5 h-3.5 transition-colors ${
                        isActive ? "text-lavender-600" : "text-ink-muted group-hover:text-ink"
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                      isActive
                        ? "bg-white text-lavender-700 font-semibold shadow-xs"
                        : "text-ink-muted group-hover:text-ink-secondary"
                    }`}
                  >
                    {item.section}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Apple Store Utility Card: Protocol Metadata */}
        <div className="apple-card p-4 text-[11px] space-y-2.5 bg-white border border-cream-300">
          <div className="flex items-center justify-between text-ink-secondary">
            <span>Jurisdiction</span>
            <span className="font-semibold text-ink">European Union</span>
          </div>
          <div className="flex items-center justify-between text-ink-secondary">
            <span>Corpus Version</span>
            <span className="font-mono text-lavender-700 font-medium">2026.1.0</span>
          </div>
          <div className="flex items-center justify-between text-ink-secondary">
            <span>Commit Hash</span>
            <span className="font-mono text-lavender-600">0x8fa12b...</span>
          </div>
          <div className="pt-2 border-t border-cream-200 text-[10px] text-ink-muted leading-relaxed">
            VERIDION is decision support; it does not replace qualified legal counsel.
          </div>
        </div>
      </div>
    </aside>
  );
};


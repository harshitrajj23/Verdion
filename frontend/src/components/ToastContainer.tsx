"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X, ExternalLink } from "lucide-react";

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-md w-full pointer-events-none">
      {toasts.map((toast) => {
        const icon = {
          success: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />,
          error: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />,
          warning: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
          info: <Info className="w-5 h-5 text-cyan-400 shrink-0" />
        }[toast.type];

        const borderColor = {
          success: "border-emerald-500/40 bg-emerald-950/90",
          error: "border-rose-500/40 bg-rose-950/90",
          warning: "border-amber-500/40 bg-amber-950/90",
          info: "border-cyan-500/40 bg-cyan-950/90"
        }[toast.type];

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto p-4 rounded-xl border backdrop-blur-md shadow-2xl flex items-start justify-between gap-3 text-slate-100 animate-in slide-in-from-bottom-5 duration-300 ${borderColor}`}
          >
            <div className="flex items-start gap-3">
              {icon}
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-white tracking-wide">{toast.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{toast.message}</p>
                {toast.txHash && (
                  <div className="pt-1 flex items-center gap-1.5 text-[11px] font-mono text-cyan-400 hover:text-cyan-300">
                    <span>Tx: {toast.txHash.slice(0, 10)}...{toast.txHash.slice(-8)}</span>
                    <ExternalLink className="w-3 h-3" />
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

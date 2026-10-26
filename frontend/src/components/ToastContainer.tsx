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
          success: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
          error: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />,
          warning: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
          info: <Info className="w-5 h-5 text-lavender-600 shrink-0" />
        }[toast.type];

        const borderColor = {
          success: "border-emerald-200",
          error: "border-rose-200",
          warning: "border-amber-200",
          info: "border-lavender-200"
        }[toast.type];

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto p-4 rounded-[16px] border bg-white/95 backdrop-blur-xl shadow-apple-float flex items-start justify-between gap-3 text-ink animate-fade-in-up ${borderColor}`}
          >
            <div className="flex items-start gap-3">
              {icon}
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-ink tracking-tight">{toast.title}</h4>
                <p className="text-xs text-ink-secondary leading-relaxed">{toast.message}</p>
                {toast.txHash && (
                  <div className="pt-1 flex items-center gap-1.5 text-[11px] font-mono text-lavender-700 hover:text-lavender-900 font-medium">
                    <span>Tx: {toast.txHash.slice(0, 10)}...{toast.txHash.slice(-8)}</span>
                    <ExternalLink className="w-3 h-3 text-lavender-600" />
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="p-1 rounded-full text-ink-tertiary hover:text-ink hover:bg-cream-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

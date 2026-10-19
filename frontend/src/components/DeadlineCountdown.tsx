"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Clock, AlertTriangle } from "lucide-react";

interface DeadlineCountdownProps {
  /** ISO timestamp of the deadline */
  deadline: string;
  /** Label describing this deadline */
  label: string;
  /** Accent color theme */
  accent?: "cyan" | "amber" | "rose" | "emerald";
  /** Whether to show compact single-line variant */
  compact?: boolean;
}

const accentMap = {
  cyan: {
    bg: "bg-cyan-950/30",
    border: "border-cyan-800/40",
    text: "text-cyan-300",
    icon: "text-cyan-400",
    value: "text-cyan-400"
  },
  amber: {
    bg: "bg-amber-950/30",
    border: "border-amber-800/40",
    text: "text-amber-300",
    icon: "text-amber-400",
    value: "text-amber-400"
  },
  rose: {
    bg: "bg-rose-950/30",
    border: "border-rose-800/40",
    text: "text-rose-300",
    icon: "text-rose-400",
    value: "text-rose-400"
  },
  emerald: {
    bg: "bg-emerald-950/30",
    border: "border-emerald-800/40",
    text: "text-emerald-300",
    icon: "text-emerald-400",
    value: "text-emerald-400"
  }
};

export const DeadlineCountdown: React.FC<DeadlineCountdownProps> = ({
  deadline,
  label,
  accent = "cyan",
  compact = false
}) => {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const { hours, minutes, seconds, isExpired, totalMs } = useMemo(() => {
    const target = new Date(deadline).getTime();
    const diff = target - now;
    if (diff <= 0) {
      return { hours: 0, minutes: 0, seconds: 0, isExpired: true, totalMs: 0 };
    }
    return {
      hours: Math.floor(diff / 3600000),
      minutes: Math.floor((diff % 3600000) / 60000),
      seconds: Math.floor((diff % 60000) / 1000),
      isExpired: false,
      totalMs: diff
    };
  }, [deadline, now]);

  const colors = accentMap[accent];
  const isUrgent = !isExpired && totalMs < 3600000; // under 1 hour

  if (compact) {
    if (isExpired) {
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono text-slate-500">
          <Clock className="w-3 h-3" />
          <span>Expired</span>
        </span>
      );
    }
    return (
      <span className={`flex items-center gap-1 text-[10px] font-mono ${isUrgent ? "text-rose-400" : colors.value}`}>
        <Clock className="w-3 h-3" />
        <span>
          {String(hours).padStart(2, "0")}:{String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
        </span>
      </span>
    );
  }

  return (
    <div className={`p-3 rounded-xl ${colors.bg} border ${colors.border} space-y-2`}>
      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-semibold uppercase tracking-wider ${colors.text} flex items-center gap-1.5`}>
          {isUrgent && !isExpired ? (
            <AlertTriangle className={`w-3 h-3 ${colors.icon}`} />
          ) : (
            <Clock className={`w-3 h-3 ${colors.icon}`} />
          )}
          {label}
        </span>
        {isExpired && (
          <span className="text-[10px] font-bold text-slate-500 uppercase">Expired</span>
        )}
      </div>

      {!isExpired && (
        <div className="flex items-center gap-3">
          <div className="countdown-segment">
            <span className={`countdown-value ${isUrgent ? "text-rose-400" : colors.value}`}>
              {String(hours).padStart(2, "0")}
            </span>
            <span className="countdown-label">Hrs</span>
          </div>
          <span className="text-slate-600 font-mono text-sm">:</span>
          <div className="countdown-segment">
            <span className={`countdown-value ${isUrgent ? "text-rose-400" : colors.value}`}>
              {String(minutes).padStart(2, "0")}
            </span>
            <span className="countdown-label">Min</span>
          </div>
          <span className="text-slate-600 font-mono text-sm">:</span>
          <div className="countdown-segment">
            <span className={`countdown-value ${isUrgent ? "text-rose-400" : colors.value}`}>
              {String(seconds).padStart(2, "0")}
            </span>
            <span className="countdown-label">Sec</span>
          </div>
        </div>
      )}
    </div>
  );
};

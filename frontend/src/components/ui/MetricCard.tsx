"use client";

import React from "react";
import { cn } from "@/lib/design-tokens";

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  iconBg?: string;
  iconColor?: string;
  trendText?: string;
  trendDirection?: "up" | "down" | "neutral";
  className?: string;
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  iconBg = "bg-red-50",
  iconColor = "text-[#DC2626]",
  trendText,
  trendDirection = "up",
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "aurora-glass-card p-5 relative overflow-hidden transition-all duration-200 select-none",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div
          className={cn(
            "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border border-white/60 shadow-2xs",
            iconBg
          )}
        >
          <Icon className={cn("w-5 h-5", iconColor)} />
        </div>

        {trendText && (
          <span
            className={cn(
              "text-[11px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1",
              trendDirection === "up"
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                : trendDirection === "down"
                ? "bg-rose-50 text-rose-700 border border-rose-200/60"
                : "bg-gray-100 text-gray-700 border border-gray-200"
            )}
          >
            {trendDirection === "up" ? "↑" : trendDirection === "down" ? "↓" : "•"}{" "}
            {trendText}
          </span>
        )}
      </div>

      <div className="mt-4">
        <div className="text-2xl lg:text-3xl font-black tracking-tight text-[#1A1D26] tabular-nums">
          {value}
        </div>
        <p className="text-xs font-medium text-[#687080] mt-0.5">{label}</p>
      </div>
    </div>
  );
}

export default MetricCard;


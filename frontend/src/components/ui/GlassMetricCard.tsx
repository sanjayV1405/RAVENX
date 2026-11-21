"use client";

import React from "react";
import { FileText, CheckCircle2, AlertTriangle, Clock } from "lucide-react";
import { cn } from "@/lib/design-tokens";

interface GlassMetricCardProps {
  type: "documents" | "inspections" | "issues" | "reviews";
  title: string;
  value: number | string;
  trend?: string;
  isPositive?: boolean;
  className?: string;
}

export function GlassMetricCard({
  type,
  title,
  value,
  trend,
  isPositive = true,
  className,
}: GlassMetricCardProps) {
  const getIcon = () => {
    switch (type) {
      case "documents":
        return (
          <div className="w-9 h-9 rounded-xl bg-red-50 border border-red-200/60 flex items-center justify-center text-[#DC2626]">
            <FileText className="w-4 h-4" />
          </div>
        );
      case "inspections":
        return (
          <div className="w-9 h-9 rounded-xl bg-slate-100 border border-slate-200/60 flex items-center justify-center text-[#1A1D26]">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        );
      case "issues":
        return (
          <div className="w-9 h-9 rounded-xl bg-red-50 border border-red-200/60 flex items-center justify-center text-[#DC2626]">
            <AlertTriangle className="w-4 h-4" />
          </div>
        );
      case "reviews":
        return (
          <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200/60 flex items-center justify-center text-indigo-600">
            <Clock className="w-4 h-4" />
          </div>
        );
    }
  };

  const getSparkline = () => {
    const strokeColor =
      type === "documents"
        ? "#DC2626"
        : type === "inspections"
        ? "#475569"
        : type === "issues"
        ? "#DC2626"
        : "#3B82F6";

    return (
      <svg className="w-24 h-7 shrink-0 overflow-visible opacity-75" viewBox="0 0 100 30" fill="none">
        <path
          d={
            isPositive
              ? "M0 24 C 20 22, 35 28, 50 18 C 65 8, 80 14, 100 4"
              : "M0 6 C 25 10, 45 4, 65 18 C 80 26, 90 20, 100 24"
          }
          stroke={strokeColor}
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  return (
    <div
      className={cn(
        "aurora-glass-card p-5 relative overflow-hidden transition-all duration-200 select-none",
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-[#687080] tracking-tight">{title}</span>
        {getIcon()}
      </div>

      <div className="flex items-end justify-between gap-2 mt-2">
        <div className="flex flex-col">
          <span className="text-3xl font-black tracking-tight text-[#1A1D26] tabular-nums">
            {value}
          </span>
          {trend ? (
            <span
              className={cn(
                "text-[11px] font-semibold tracking-tight mt-1 inline-flex items-center gap-0.5",
                isPositive ? "text-emerald-600" : "text-rose-600"
              )}
            >
              {trend}
            </span>
          ) : (
            <span className="text-[10px] text-[#9CA3AF] mt-1 font-medium">Live verified</span>
          )}
        </div>

        {getSparkline()}
      </div>
    </div>
  );
}

export default GlassMetricCard;

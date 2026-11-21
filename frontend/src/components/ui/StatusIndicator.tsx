"use client";

import React from "react";
import { cn } from "@/lib/design-tokens";

export type SystemStatus =
  | "completed"
  | "processing"
  | "uploaded"
  | "failed"
  | "pending"
  | "MET"
  | "PARTIALLY MET"
  | "MISSING"
  | "AMBIGUOUS"
  | "NOT VERIFIABLE"
  | "CRITICAL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";

interface StatusIndicatorProps {
  status: string;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

export function StatusIndicator({
  status,
  label,
  size = "md",
  className,
}: StatusIndicatorProps) {
  const norm = status.toUpperCase();

  const getStyle = () => {
    switch (norm) {
      case "COMPLETED":
      case "MET":
        return {
          bg: "bg-emerald-50",
          border: "border-emerald-200",
          text: "text-emerald-700",
          dot: "bg-emerald-500",
        };
      case "PROCESSING":
      case "UPLOADED":
        return {
          bg: "bg-blue-50",
          border: "border-blue-200",
          text: "text-blue-700",
          dot: "bg-blue-500 animate-pulse",
        };
      case "PARTIALLY MET":
      case "MEDIUM":
        return {
          bg: "bg-amber-50",
          border: "border-amber-200",
          text: "text-amber-700",
          dot: "bg-amber-500",
        };
      case "FAILED":
      case "MISSING":
      case "CRITICAL":
        return {
          bg: "bg-rose-50",
          border: "border-rose-200",
          text: "text-rose-700",
          dot: "bg-rose-500",
        };
      case "AMBIGUOUS":
      case "HIGH":
        return {
          bg: "bg-purple-50",
          border: "border-purple-200",
          text: "text-purple-700",
          dot: "bg-purple-500",
        };
      case "NOT VERIFIABLE":
      case "LOW":
      default:
        return {
          bg: "bg-gray-100",
          border: "border-gray-200",
          text: "text-gray-700",
          dot: "bg-gray-400",
        };
    }
  };

  const style = getStyle();
  const padding = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-semibold rounded-full border shadow-2xs select-none",
        style.bg,
        style.border,
        style.text,
        padding,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", style.dot)} />
      <span className="capitalize">{label || status.toLowerCase()}</span>
    </span>
  );
}

export default StatusIndicator;


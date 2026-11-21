"use client";

import React from "react";
import { cn } from "@/lib/design-tokens";

interface PageHeaderProps {
  badge?: string;
  title: string;
  highlightedTitle?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  badge,
  title,
  highlightedTitle,
  description,
  action,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2", className)}>
      <div className="space-y-1.5 max-w-3xl">
        {badge && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-[#DDE0E6] text-[11px] font-semibold text-[#687080] shadow-2xs backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-[#DC2626]" />
            {badge}
          </div>
        )}
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#1A1D26]">
          {title}{" "}
          {highlightedTitle && (
            <span className="text-[#DC2626] font-extrabold">{highlightedTitle}</span>
          )}
        </h1>
        {description && (
          <p className="text-xs md:text-sm text-[#687080] leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {action && <div className="flex items-center gap-3 shrink-0">{action}</div>}
    </div>
  );
}

export default PageHeader;


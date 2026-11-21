"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/design-tokens";

interface SectionHeaderProps {
  title: string;
  count?: number | string;
  actionText?: string;
  actionHref?: string;
  onAction?: () => void;
  className?: string;
}

export function SectionHeader({
  title,
  count,
  actionText,
  actionHref,
  onAction,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between py-1 select-none", className)}>
      <div className="flex items-center">
        <span className="section-accent-bar" />
        <h2 className="text-sm md:text-base font-bold tracking-tight text-[#1A1D26]">
          {title}
        </h2>
        {count !== undefined && (
          <span className="ml-2 px-2 py-0.5 text-[11px] font-semibold rounded-full bg-black/5 text-[#687080] tabular-nums">
            {count}
          </span>
        )}
      </div>

      {actionText && actionHref && (
        <Link
          href={actionHref}
          className="text-xs font-semibold text-[#687080] hover:text-[#DC2626] transition-colors inline-flex items-center gap-1 group"
        >
          <span>{actionText}</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      )}

      {actionText && !actionHref && onAction && (
        <button
          onClick={onAction}
          className="text-xs font-semibold text-[#687080] hover:text-[#DC2626] transition-colors inline-flex items-center gap-1 group cursor-pointer"
        >
          <span>{actionText}</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
        </button>
      )}
    </div>
  );
}

export default SectionHeader;


"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, FileText, Scale, ShieldCheck, BarChart3 } from "lucide-react";

interface QuickActionCardProps {
  title: string;
  subtitle: string;
  href: string;
  iconType: "inspect" | "compare" | "requirements" | "audit";
}

export function QuickActionCard({
  title,
  subtitle,
  href,
  iconType,
}: QuickActionCardProps) {
  const getIcon = () => {
    switch (iconType) {
      case "inspect":
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-50 to-red-100/80 border border-red-200/60 flex items-center justify-center text-[#DC2626] shadow-sm">
            <FileText className="w-5 h-5" />
          </div>
        );
      case "compare":
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100/80 border border-slate-200/60 flex items-center justify-center text-[#20232B] shadow-sm">
            <Scale className="w-5 h-5" />
          </div>
        );
      case "requirements":
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-50 to-red-100/80 border border-red-200/60 flex items-center justify-center text-[#DC2626] shadow-sm">
            <ShieldCheck className="w-5 h-5" />
          </div>
        );
      case "audit":
        return (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-50 to-slate-100/80 border border-rose-200/60 flex items-center justify-center text-[#DC2626] shadow-sm">
            <BarChart3 className="w-5 h-5" />
          </div>
        );
    }
  };

  return (
    <Link
      href={href}
      className="flex items-center justify-between p-4 rounded-2xl aurora-glass-card group select-none"
    >
      <div className="flex items-center gap-3.5 min-w-0">
        {getIcon()}
        <div className="min-w-0">
          <h4 className="text-xs font-bold text-[#20232B] group-hover:text-[#DC2626] transition-colors truncate">
            {title}
          </h4>
          <p className="text-[11px] text-[#727989] truncate mt-0.5">
            {subtitle}
          </p>
        </div>
      </div>

      {/* Black circular arrow button matching reference */}
      <div className="w-7 h-7 rounded-full bg-[#181A22] group-hover:bg-[#DC2626] text-white flex items-center justify-center shrink-0 ml-2 transition-all duration-200 shadow-sm group-hover:translate-x-0.5">
        <ArrowRight className="w-3.5 h-3.5" />
      </div>
    </Link>
  );
}

export default QuickActionCard;


"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Check, FileText } from "lucide-react";

export function PromoCard() {
  return (
    <div className="rounded-2xl p-6 aurora-obsidian-card relative overflow-hidden flex flex-col justify-between min-h-[220px]">
      {/* Background radial crimson aura */}
      <div
        className="absolute -right-6 -bottom-6 w-48 h-48 rounded-full pointer-events-none opacity-40 blur-2xl"
        style={{
          background: "radial-gradient(circle, #DC2626 0%, transparent 70%)",
        }}
      />

      {/* Top Header Pill */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#DC2626]/20 border border-[#DC2626]/40 text-[#EF4444] text-[10px] font-mono font-bold uppercase tracking-wider mb-3">
          <span>RAVENX AI v4.0</span>
        </div>

        <h3 className="text-base font-bold text-white tracking-tight leading-snug">
          Advanced Document
          <br />
          Intelligence
        </h3>

        <p className="text-xs text-gray-400 mt-1 font-medium">
          Detect • Verify • Comply • Improve
        </p>
      </div>

      {/* 3D Holographic Document Visual on Right */}
      <div className="absolute right-4 bottom-4 w-32 h-36 pointer-events-none select-none flex items-center justify-center">
        {/* Glowing pedestal ellipse */}
        <div className="absolute bottom-1 w-24 h-7 rounded-full bg-gradient-to-r from-red-600/40 via-red-500/60 to-red-600/40 blur-sm" />
        <div className="absolute bottom-2 w-20 h-5 rounded-full border border-red-500/80 shadow-[0_0_15px_rgba(220,38,38,0.8)]" />
        <div className="absolute bottom-3 w-16 h-4 rounded-full border border-red-400/60" />

        {/* Floating holographic document */}
        <div
          className="relative w-14 h-18 rounded-lg p-2 flex flex-col justify-between border border-blue-400/40 bg-gradient-to-br from-blue-500/20 via-blue-400/10 to-transparent shadow-[0_8px_20px_rgba(59,130,246,0.3)] transform -rotate-6 hover:rotate-0 transition-transform"
          style={{ backdropFilter: "blur(6px)" }}
        >
          {/* Header lines */}
          <div className="space-y-1">
            <div className="w-6 h-1 rounded bg-blue-300/80" />
            <div className="w-10 h-1 rounded bg-blue-200/50" />
            <div className="w-8 h-1 rounded bg-blue-200/50" />
          </div>

          {/* Floating red check badge */}
          <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-[#DC2626] border border-white text-white flex items-center justify-center shadow-lg">
            <Check className="w-3 h-3 stroke-[3]" />
          </div>
        </div>
      </div>

      {/* Learn More Button */}
      <div className="pt-4 z-10">
        <Link
          href="/inspection"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold text-white bg-white/10 hover:bg-white/20 border border-white/20 transition-all duration-200"
        >
          <span>Learn More</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}

export default PromoCard;


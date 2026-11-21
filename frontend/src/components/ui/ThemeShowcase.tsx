"use client";

import React from "react";
import Link from "next/link";
import { Check, ArrowRight } from "lucide-react";
import { RavenXLogo } from "@/components/brand/RavenXLogo";

export function ThemeShowcase() {
  return (
    <div className="mt-8 p-6 rounded-2xl aurora-glass-card flex flex-col md:flex-row items-center justify-between gap-6 select-none border border-white/90">
      {/* Brand logo left */}
      <div className="flex items-center gap-4 shrink-0">
        <RavenXLogo variant="showcase" size="lg" showTagline={true} />
      </div>

      {/* Middle: Pearl Theme & Color Swatches */}
      <div className="flex flex-col sm:flex-row items-center gap-6">
        <div>
          <h4 className="text-base font-black text-[#20232B] tracking-tight">
            Pearl Theme
          </h4>
          <p className="text-xs text-[#727989] font-medium">
            Clean. Elegant. Powerful.
          </p>
          {/* Swatches */}
          <div className="flex items-center gap-2 mt-2">
            <span className="w-4 h-4 rounded-full bg-white border border-[#DDE1E9] shadow-sm" />
            <span className="w-4 h-4 rounded-full bg-[#ECEEF4] border border-[#DDE1E9]" />
            <span className="w-4 h-4 rounded-full bg-[#94A3B8]" />
            <span className="w-4 h-4 rounded-full bg-[#DC2626] shadow-[0_0_8px_rgba(220,38,38,0.5)]" />
            <span className="w-4 h-4 rounded-full bg-[#181A22]" />
          </div>
        </div>

        {/* Feature Checkpoints */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs font-semibold text-[#20232B]">
          <div className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-[#DC2626] stroke-[2.5]" />
            <span>Glassmorphism Design</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-[#DC2626] stroke-[2.5]" />
            <span>Smooth Animations</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-[#DC2626] stroke-[2.5]" />
            <span>Premium UI/UX</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-[#DC2626] stroke-[2.5]" />
            <span>Perfect Alignment</span>
          </div>
        </div>
      </div>

      {/* Right Brand CTA Button */}
      <div className="shrink-0">
        <Link
          href="/inspection"
          className="flex items-center gap-2.5 px-6 py-3 rounded-full text-xs font-bold text-white aurora-btn-crimson"
        >
          <span>RAVENX AI Signature UI Style</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}

export default ThemeShowcase;


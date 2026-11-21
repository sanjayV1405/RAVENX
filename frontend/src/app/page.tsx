"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Layers,
  FileSearch,
  Lock,
  ArrowRight,
  GitBranch,
  SplitSquareVertical,
  Zap,
} from "lucide-react";
import { RavenIllustration } from "@/components/brand/RavenIllustration";
import { ThemeShowcase } from "@/components/ui/ThemeShowcase";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";

const capabilities = [
  {
    title: "Micro-Typographical & Syntax Audit",
    description:
      "Detects missing separators, omitted spaces, double punctuation, and subtle grammatical discrepancies that standard spellcheckers silently bypass.",
    icon: FileSearch,
    badge: "Typographical",
    color: "#3B82F6",
  },
  {
    title: "Cross-Field Entity Consistency",
    description:
      "Identifies mismatched names, discordant dates, contradicting currency values, and inconsistent addresses across disparate sections of multi-page files.",
    icon: SplitSquareVertical,
    badge: "Entity Integrity",
    color: "#8B5CF6",
  },
  {
    title: "Visual Geometry & Layout Defects",
    description:
      "Scans for margin drift, overlapping text blocks, header/footer collisions, and misaligned tabular columns using multi-tier geometric analysis.",
    icon: Layers,
    badge: "Layout Bounds",
    color: "#F59E0B",
  },
  {
    title: "Structural & Heading Coherence",
    description:
      "Validates numerical hierarchy in headings, broken lists, orphaned headers, and malformed cell boundaries across document tables.",
    icon: GitBranch,
    badge: "Structure",
    color: "#10B981",
  },
  {
    title: "Requirement Compliance Verification",
    description:
      "Cross-examines document clauses against user-specified guidelines and contractual mandates to detect omissions and policy discrepancies.",
    icon: ShieldCheck,
    badge: "Compliance",
    color: "#DC2626",
  },
  {
    title: "Immutable Source Guarantee",
    description:
      "RAVENX AI never modifies your source files automatically. Every suggestion includes granular evidence, confidence ratings, and requires human approval.",
    icon: Lock,
    badge: "Governance",
    color: "#6B7280",
  },
];

export default function LandingPage() {
  return (
    <div className="space-y-8 select-none">
      {/* 1. HERO SECTION: Project Aurora Glass Hero */}
      <div className="relative rounded-3xl p-8 lg:p-12 aurora-hero-glass overflow-hidden">
        <div
          className="absolute -right-20 -top-20 w-[500px] h-[500px] rounded-full pointer-events-none opacity-25 blur-3xl"
          style={{
            background: "radial-gradient(circle, rgba(220, 38, 38, 0.35) 0%, transparent 70%)",
          }}
        />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          <div className="lg:col-span-7 space-y-5">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#171B2A] text-white text-xs font-semibold shadow-sm border border-white/10">
              <span className="w-2 h-2 rounded-full bg-[#DC2626] animate-pulse" />
              <span>Intelligence That Sees What Others Miss</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#1A1D26] tracking-tight leading-[1.08]">
              Document Quality <br />
              <span className="text-[#DC2626]">Intelligence</span> <br />
              Engineered for Precision.
            </h1>

            <p className="text-sm sm:text-base text-[#687080] font-medium leading-relaxed max-w-xl">
              General-purpose LLMs hallucinate and spell-checkers miss context.
              RAVENX AI applies deterministic inspection pipelines and AI reasoning
              to surface every defect with verifiable evidence.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link href="/inspection">
                <PrimaryButton
                  size="lg"
                  leftIcon={<Zap className="w-4 h-4 fill-current" />}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Launch Inspection Portal
                </PrimaryButton>
              </Link>

              <Link href="/dashboard">
                <SecondaryButton size="lg">
                  Open Command Center
                </SecondaryButton>
              </Link>
            </div>
          </div>

          <div className="lg:col-span-5 relative flex items-center justify-center">
            <div className="w-full max-w-[420px]">
              <RavenIllustration className="w-full h-auto drop-shadow-2xl" />
            </div>
          </div>
        </div>
      </div>

      {/* 2. CAPABILITIES GRID */}
      <div className="space-y-4">
        <SectionHeader title="Inspection Capabilities" />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {capabilities.map((cap, idx) => {
            const Icon = cap.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-2xl aurora-glass-card flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div
                      className="w-9 h-9 rounded-xl flex items-center justify-center"
                      style={{
                        background: `${cap.color}15`,
                        color: cap.color,
                        border: `1px solid ${cap.color}30`,
                      }}
                    >
                      <Icon className="w-4.5 h-4.5" />
                    </div>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/80 border border-[#DDE0E6] text-[#687080]">
                      {cap.badge}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-[#1A1D26] mb-1">
                    {cap.title}
                  </h4>
                  <p className="text-xs text-[#687080] leading-relaxed">
                    {cap.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. SIGNATURE THEME SHOWCASE */}
      <ThemeShowcase />
    </div>
  );
}

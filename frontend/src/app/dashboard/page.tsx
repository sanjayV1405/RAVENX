"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  FileText,
  Zap,
  Scale,
  ArrowRight,
  ChevronDown,
  RefreshCw,
  FolderOpen,
} from "lucide-react";
import { RavenIllustration } from "@/components/brand/RavenIllustration";
import { GlassMetricCard } from "@/components/ui/GlassMetricCard";
import { QuickActionCard } from "@/components/ui/QuickActionCard";
import { DonutChart } from "@/components/ui/DonutChart";
import { PromoCard } from "@/components/ui/PromoCard";
import { ThemeShowcase } from "@/components/ui/ThemeShowcase";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { ErrorState } from "@/components/ui/ErrorState";
import { listDocuments, listInspections, getAuditHistory, type InspectionResponse, type AuditLogItem } from "@/lib/api";
import type { Document } from "@/types/extraction";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [inspections, setInspections] = useState<InspectionResponse[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [docsResult, inspResult, auditResult] = await Promise.allSettled([
        listDocuments(),
        listInspections(),
        getAuditHistory({ limit: 6 }),
      ]);

      if (docsResult.status === "fulfilled") {
        setDocuments(docsResult.value);
      }
      if (inspResult.status === "fulfilled") {
        setInspections(inspResult.value);
      }
      if (auditResult.status === "fulfilled") {
        setAuditLogs(auditResult.value);
      }

      // If all three failed due to offline backend
      if (
        docsResult.status === "rejected" &&
        inspResult.status === "rejected" &&
        auditResult.status === "rejected"
      ) {
        setError(
          docsResult.reason?.message ||
            "Unable to connect to RAVENX AI engine. Please ensure the backend server is running on port 8000."
        );
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Derive real statistics from verified backend entities
  const totalDocs = documents.length;
  const completedInspections = inspections.filter((i) => i.status === "completed").length;

  // Calculate real issue counts across inspections
  let criticalCount = 0;
  let highCount = 0;
  let mediumCount = 0;
  let lowCount = 0;

  inspections.forEach((insp) => {
    if (insp.findings && Array.isArray(insp.findings)) {
      insp.findings.forEach((f) => {
        const sev = f.severity?.toUpperCase();
        if (sev === "CRITICAL") criticalCount++;
        else if (sev === "HIGH") highCount++;
        else if (sev === "MEDIUM") mediumCount++;
        else lowCount++;
      });
    } else if (insp.summary) {
      criticalCount += Number(insp.summary.critical || insp.summary.CRITICAL || 0);
      highCount += Number(insp.summary.high || insp.summary.HIGH || 0);
      mediumCount += Number(insp.summary.medium || insp.summary.MEDIUM || 0);
      lowCount += Number(insp.summary.low || insp.summary.LOW || 0);
    }
  });

  const totalIssues = criticalCount + highCount + mediumCount + lowCount;
  const pendingReviews = inspections.filter(
    (i) => i.status === "processing" || i.status === "uploaded" || i.status === "queued"
  ).length;

  // Format relative timestamp
  const formatTimeAgo = (dateStr?: string) => {
    if (!dateStr) return "Recent";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className="space-y-6 select-none">
      {/* Optional Connection Error Banner */}
      {error && (
        <ErrorState
          title="Backend Operational Notice"
          message={error}
          onRetry={loadDashboardData}
        />
      )}

      {/* 1. HERO SECTION: Document Intelligence Command Center */}
      <div className="relative rounded-3xl p-7 lg:p-9 aurora-hero-glass overflow-hidden">
        {/* Ambient Crimson Glow Pool */}
        <div
          className="absolute -right-20 -top-20 w-[460px] h-[460px] rounded-full pointer-events-none opacity-25 blur-3xl"
          style={{
            background: "radial-gradient(circle, rgba(220, 38, 38, 0.35) 0%, transparent 70%)",
          }}
        />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          {/* Left Text Block */}
          <div className="lg:col-span-7 space-y-4">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#171B2A] text-white text-xs font-semibold shadow-sm border border-white/10">
              <span className="w-2 h-2 rounded-full bg-[#DC2626]" />
              <span>Welcome back, Sanjay! 👋</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#1A1D26] tracking-tight leading-[1.1]">
              Document Intelligence <br />
              <span className="text-[#DC2626]">Command Center</span>
            </h1>

            <p className="text-xs sm:text-sm text-[#687080] font-medium leading-relaxed max-w-xl">
              See beyond the surface. Discover micro-typographical errors, semantic contradictions,
              and cross-document discrepancies with evidence-backed AI.
            </p>

            {/* Dual Action CTA Buttons */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href="/inspection"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-xs font-bold text-white aurora-btn-crimson"
              >
                <Zap className="w-4 h-4 fill-current" />
                <span>Correct Document</span>
                <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </Link>

              <Link
                href="/comparison"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-xs font-bold text-[#1A1D26] aurora-btn-frosted"
              >
                <Scale className="w-4 h-4 text-[#1A1D26]" />
                <span>Compare Documents</span>
              </Link>
            </div>
          </div>

          {/* Right Raven Artwork & Slogan */}
          <div className="lg:col-span-5 relative flex items-center justify-end">
            <div className="w-full max-w-[340px] sm:max-w-[420px] relative">
              <RavenIllustration className="w-full h-auto drop-shadow-xl" />
            </div>

            <div className="hidden xl:flex flex-col text-right pl-3 pr-1 py-4 border-l border-[#DDE0E6]">
              <span className="text-[11px] font-black tracking-[0.2em] uppercase text-[#1A1D26] leading-tight">
                INTELLIGENCE
              </span>
              <span className="text-[11px] font-black tracking-[0.2em] uppercase text-[#687080] leading-tight mt-1">
                THAT SEES
              </span>
              <span className="text-[11px] font-black tracking-[0.2em] uppercase text-[#DC2626] leading-tight mt-1">
                WHAT OTHERS MISS.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. ANALYTICS ROW: Real, Evidence-Backed Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassMetricCard
          type="documents"
          title="Total Documents"
          value={totalDocs}
        />
        <GlassMetricCard
          type="inspections"
          title="Completed Inspections"
          value={completedInspections}
        />
        <GlassMetricCard
          type="issues"
          title="Issues Detected"
          value={totalIssues}
        />
        <GlassMetricCard
          type="reviews"
          title="Pending Reviews"
          value={pendingReviews}
        />
      </div>

      {/* 3. QUICK ACTIONS */}
      <div className="space-y-3">
        <SectionHeader
          title="Quick Actions"
          actionText="Explore All"
          actionHref="/inspection"
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickActionCard
            title="Correct Document"
            subtitle="Detect and fix mistakes"
            href="/inspection"
            iconType="inspect"
          />
          <QuickActionCard
            title="Compare Documents"
            subtitle="Track changes & differences"
            href="/comparison"
            iconType="compare"
          />
          <QuickActionCard
            title="Requirements Alignment"
            subtitle="Verify compliance checklist"
            href="/requirements"
            iconType="requirements"
          />
          <QuickActionCard
            title="Audit Reports"
            subtitle="Generate verified PDF reports"
            href="/audit-history"
            iconType="audit"
          />
        </div>
      </div>

      {/* 4. BOTTOM 3-COLUMN CONTENT GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Recent Activity from Real Backend Records */}
        <div className="lg:col-span-5 rounded-2xl p-5 aurora-glass-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E6EE] mb-3">
              <div className="flex items-center gap-2">
                <span className="section-accent-bar" />
                <h4 className="text-sm font-bold text-[#1A1D26]">Recent Activity</h4>
              </div>
              <Link
                href="/audit-history"
                className="text-xs font-semibold text-[#687080] hover:text-[#DC2626] flex items-center gap-1 transition-colors"
              >
                <span>Audit Trail</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {/* Document / Activity items list */}
            <div className="space-y-2.5">
              {documents.length > 0 ? (
                documents.slice(0, 4).map((doc) => (
                  <Link
                    key={doc.id}
                    href={`/inspection?doc=${doc.id}`}
                    className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/90 transition-all border border-transparent hover:border-[#DDE0E6]/80 group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-red-50/80 border border-red-100 flex items-center justify-center text-[#DC2626] shrink-0 group-hover:scale-105 transition-transform">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-[#1A1D26] truncate max-w-[200px]">
                          {doc.filename}
                        </p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <StatusIndicator status={doc.status} size="sm" />
                          <span className="text-[10px] text-[#9CA3AF] uppercase">
                            • {doc.file_extension}
                          </span>
                        </div>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-[#8F96A3] shrink-0 ml-2">
                      {formatTimeAgo(doc.created_at)}
                    </span>
                  </Link>
                ))
              ) : (
                <div className="p-8 text-center flex flex-col items-center justify-center">
                  <div className="w-10 h-10 rounded-2xl bg-gray-50 flex items-center justify-center text-[#687080] mb-2">
                    <FolderOpen className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-bold text-[#1A1D26]">No documents uploaded yet</p>
                  <p className="text-[11px] text-[#687080] mt-0.5 max-w-[220px]">
                    Upload your first document in Inspect & Evidence to begin analysis.
                  </p>
                  <Link
                    href="/inspection"
                    className="mt-3 text-xs font-semibold text-[#DC2626] hover:underline"
                  >
                    + Upload Document
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Center: Inspection Overview (Donut Chart) */}
        <div className="lg:col-span-4 rounded-2xl p-5 aurora-glass-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E6EE] mb-3">
              <div className="flex items-center gap-2">
                <span className="section-accent-bar" />
                <h4 className="text-sm font-bold text-[#1A1D26]">Inspection Overview</h4>
              </div>
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-[#687080] bg-white/80 border border-[#DDE0E6]">
                <span>Active Data</span>
              </div>
            </div>

            {/* Donut Chart Component with Live Data */}
            <DonutChart
              totalIssues={totalIssues}
              critical={criticalCount}
              high={highCount}
              medium={mediumCount}
              low={lowCount}
            />
          </div>
        </div>

        {/* Right: Obsidian Feature Promo Card */}
        <div className="lg:col-span-3 flex flex-col">
          <PromoCard />
        </div>
      </div>

      {/* 5. THEME SHOWCASE FOOTER PANEL */}
      <ThemeShowcase />
    </div>
  );
}

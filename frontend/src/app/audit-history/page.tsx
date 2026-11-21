"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  History,
  CheckCircle2,
  XCircle,
  EyeOff,
  FileText,
  RotateCcw,
  GitCompare,
  CheckSquare,
  Download,
  Filter,
  ShieldCheck,
  Tag,
  RefreshCw,
  Clock,
} from "lucide-react";
import { getAuditHistory, type AuditLogItem } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { SecondaryButton } from "@/components/ui/Buttons";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { cn } from "@/lib/design-tokens";

const EVENT_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  finding_accepted: { label: "Finding Accepted", color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", icon: CheckCircle2 },
  finding_rejected: { label: "Finding Rejected", color: "text-rose-700", bg: "bg-rose-50", border: "border-rose-200", icon: XCircle },
  finding_ignored: { label: "Finding Ignored", color: "text-gray-700", bg: "bg-gray-100", border: "border-gray-200", icon: EyeOff },
  finding_restored: { label: "Finding Restored", color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200", icon: RotateCcw },
  report_generated: { label: "Audit Report Exported", color: "text-purple-700", bg: "bg-purple-50", border: "border-purple-200", icon: Download },
  comparison_performed: { label: "Comparison Executed", color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200", icon: GitCompare },
  document_corrected: { label: "Document Corrected", color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", icon: CheckCircle2 },
  requirements_assessed: { label: "Requirements Assessed", color: "text-teal-700", bg: "bg-teal-50", border: "border-teal-200", icon: CheckSquare },
  requirement_set_created: { label: "Requirement Set Created", color: "text-indigo-700", bg: "bg-indigo-50", border: "border-indigo-200", icon: Tag },
};

export default function AuditHistoryPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("all");
  const [refreshing, setRefreshing] = useState(false);

  async function loadLogs() {
    try {
      const items = await getAuditHistory({ limit: 100 });
      setLogs(items);
    } catch (e) {
      console.error("Failed to load audit history", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs();
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    await loadLogs();
    setRefreshing(false);
  }

  const entityTypes = Array.from(new Set(logs.map((l) => l.entity_type)));
  const filteredLogs = logs.filter((l) => filterType === "all" || l.entity_type === filterType);

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  return (
    <div className="space-y-6 select-none">
      {/* Page Header */}
      <PageHeader
        badge="My Documents & Dossier"
        title="My Documents & Audit"
        highlightedTitle="History"
        description="Immutable chronological audit trail recording all uploaded documents, corrected outputs, review actions, and verification events."
        action={
          <SecondaryButton
            size="sm"
            onClick={handleRefresh}
            loading={refreshing}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh Feed
          </SecondaryButton>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Events", value: logs.length, color: "text-[#1A1D26]" },
          { label: "Accepted", value: logs.filter((l) => l.event_type === "finding_accepted").length, color: "text-emerald-700" },
          { label: "Rejected", value: logs.filter((l) => l.event_type === "finding_rejected").length, color: "text-rose-700" },
          { label: "Comparisons", value: logs.filter((l) => l.event_type === "comparison_performed").length, color: "text-blue-700" },
        ].map((stat) => (
          <div key={stat.label} className="aurora-glass-card p-4 text-center">
            <div className={cn("text-2xl font-black mb-0.5 tabular-nums", stat.color)}>
              {stat.value}
            </div>
            <div className="text-xs font-semibold text-[#687080]">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Filter and Timeline Card */}
      <div className="aurora-glass-card overflow-hidden">
        {/* Filter bar */}
        <div className="flex items-center gap-2 px-5 py-3.5 border-b border-[#E2E6EE] overflow-x-auto">
          <Filter className="w-3.5 h-3.5 text-[#687080] shrink-0" />
          <span className="text-xs font-semibold text-[#687080] mr-1 shrink-0">
            Filter entity:
          </span>
          {["all", ...entityTypes].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={cn(
                "px-3 py-1 rounded-xl text-xs font-semibold capitalize transition-all shrink-0 cursor-pointer",
                filterType === type
                  ? "bg-[#171B2A] text-white shadow-2xs"
                  : "bg-white/70 text-[#687080] hover:text-[#1A1D26] border border-[#DDE0E6]"
              )}
            >
              {type === "all" ? `All (${logs.length})` : type}
            </button>
          ))}
        </div>

        {/* Timeline list */}
        {loading ? (
          <LoadingState message="Retrieving tamper-evident audit history..." />
        ) : filteredLogs.length === 0 ? (
          <EmptyState
            icon={History}
            title="No audit events found"
            description="Audit events are recorded automatically whenever users accept, reject, or export document findings."
          />
        ) : (
          <div className="relative p-2">
            <div className="divide-y divide-[#E2E6EE]/80">
              {filteredLogs.map((log, idx) => {
                const cfg = EVENT_CONFIG[log.event_type] ?? {
                  label: log.event_type,
                  color: "text-gray-700",
                  bg: "bg-gray-100",
                  border: "border-gray-200",
                  icon: ShieldCheck,
                };
                const Icon = cfg.icon;

                return (
                  <motion.div
                    key={log.id ?? idx}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(idx * 0.02, 0.4) }}
                    className="flex gap-4 px-5 py-4 hover:bg-white/60 transition-colors"
                  >
                    {/* Event Icon Pill */}
                    <div className="shrink-0 mt-0.5">
                      <div className={cn("w-8 h-8 rounded-xl flex items-center justify-center border", cfg.bg, cfg.border, cfg.color)}>
                        <Icon className="w-4 h-4" />
                      </div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                        <div>
                          <span className={cn("inline-flex items-center text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border mb-1", cfg.bg, cfg.border, cfg.color)}>
                            {cfg.label}
                          </span>
                          <p className="text-xs md:text-sm font-semibold text-[#1A1D26]">
                            {log.summary}
                          </p>
                        </div>
                        <span className="text-[11px] font-mono text-[#8F96A3] shrink-0">
                          {formatDate(log.event_timestamp ?? log.created_at)}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 mt-1.5 text-[11px] font-mono text-[#8F96A3]">
                        <span>Actor: {log.actor}</span>
                        <span>•</span>
                        <span className="capitalize">{log.entity_type}</span>
                        <span>•</span>
                        <span>ID: {log.entity_id.slice(0, 10)}…</span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

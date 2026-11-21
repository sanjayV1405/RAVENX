"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  GitCompare,
  FileText,
  PlusCircle,
  MinusCircle,
  AlertTriangle,
  Paintbrush,
  Layers,
  ArrowRight,
  Filter,
  Sparkles,
} from "lucide-react";
import {
  listDocuments,
  compareDocuments,
  type DocumentComparison,
  type ComparisonDifference,
} from "@/lib/api";
import type { Document } from "@/types/extraction";
import { PageHeader } from "@/components/ui/PageHeader";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/design-tokens";

const DIFF_TYPE_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; border: string; icon: React.ComponentType<{ className?: string }> }
> = {
  added: { label: "Added", color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", icon: PlusCircle },
  removed: { label: "Removed", color: "text-rose-700", bg: "bg-rose-50", border: "border-rose-200", icon: MinusCircle },
  modified: { label: "Modified", color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200", icon: GitCompare },
  potentially_inconsistent: { label: "Inconsistent", color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200", icon: AlertTriangle },
  formatting_only: { label: "Formatting", color: "text-purple-700", bg: "bg-purple-50", border: "border-purple-200", icon: Paintbrush },
};

export default function ComparisonPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [baseDocId, setBaseDocId] = useState<string>("");
  const [targetDocId, setTargetDocId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<DocumentComparison | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocs() {
      try {
        const docs = await listDocuments();
        setDocuments(docs);
        if (docs.length >= 2) {
          setBaseDocId(docs[0].id);
          setTargetDocId(docs[1].id);
        } else if (docs.length === 1) {
          setBaseDocId(docs[0].id);
          setTargetDocId(docs[0].id);
        }
      } catch (e) {
        console.error("Failed to load documents", e);
      }
    }
    loadDocs();
  }, []);

  const handleRunComparison = async () => {
    if (!baseDocId || !targetDocId) {
      setError("Please select both a base and revised document.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await compareDocuments({
        base_document_id: baseDocId,
        target_document_id: targetDocId,
      });
      setComparison(res);
    } catch (err: unknown) {
      setError((err as Error).message || "Comparison failed. Check backend availability.");
    } finally {
      setLoading(false);
    }
  };

  const filteredDiffs =
    comparison?.differences.filter((d) => {
      if (activeCategory === "all") return true;
      return d.category === activeCategory;
    }) ?? [];

  return (
    <div className="space-y-6 select-none">
      {/* Page Header */}
      <PageHeader
        badge="Multi-Document Analysis"
        title="Document Comparison &"
        highlightedTitle="Diff Engine"
        description="Compare two versions of a document across content semantics, layout structures, and formatting details."
      />

      {/* Document Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Base Document */}
        <div className="md:col-span-5 aurora-glass-card p-5 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#1A1D26]" />
            <label className="text-xs font-bold text-[#1A1D26] uppercase tracking-wider">
              Base Document (Original)
            </label>
          </div>
          <select
            value={baseDocId}
            onChange={(e) => setBaseDocId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl text-xs md:text-sm bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} ({d.file_extension.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        {/* Center Comparison Arrow */}
        <div className="md:col-span-2 flex justify-center py-2">
          <div className="w-10 h-10 rounded-full bg-white/80 border border-[#DDE0E6] shadow-2xs flex items-center justify-center text-[#DC2626]">
            <GitCompare className="w-5 h-5" />
          </div>
        </div>

        {/* Target Document */}
        <div className="md:col-span-5 aurora-glass-card p-5 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#DC2626]" />
            <label className="text-xs font-bold text-[#1A1D26] uppercase tracking-wider">
              Target Document (Revised)
            </label>
          </div>
          <select
            value={targetDocId}
            onChange={(e) => setTargetDocId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl text-xs md:text-sm bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} ({d.file_extension.toUpperCase()})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorState title="Comparison Notice" message={error} />}

      {/* Run Action Bar */}
      <div className="flex items-center justify-between">
        <PrimaryButton
          size="md"
          onClick={handleRunComparison}
          disabled={loading || documents.length < 1}
          loading={loading}
          leftIcon={<Sparkles className="w-4 h-4" />}
        >
          Run Multi-Document Comparison
        </PrimaryButton>

        {comparison && (
          <div className="flex items-center gap-1.5 p-1 rounded-xl aurora-glass-subtle border border-[#DDE0E6]">
            {["all", "content", "structural", "formatting"].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer",
                  activeCategory === cat
                    ? "bg-[#171B2A] text-white shadow-2xs"
                    : "text-[#687080] hover:text-[#1A1D26]"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {!comparison ? (
        <EmptyState
          icon={GitCompare}
          title="Document Discrepancies"
          description="Select a base document and a target document to identify added, removed, modified, or inconsistent clauses and formatting discrepancies."
        />
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Summary Metric Chips */}
          {comparison.summary && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {[
                { label: "Added", val: comparison.summary.added, color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
                { label: "Removed", val: comparison.summary.removed, color: "text-rose-700 bg-rose-50 border-rose-200" },
                { label: "Modified", val: comparison.summary.modified, color: "text-blue-700 bg-blue-50 border-blue-200" },
                { label: "Inconsistent", val: comparison.summary.potentially_inconsistent, color: "text-amber-700 bg-amber-50 border-amber-200" },
                { label: "Formatting", val: comparison.summary.formatting_only, color: "text-purple-700 bg-purple-50 border-purple-200" },
              ].map((s) => (
                <div key={s.label} className={cn("p-3 rounded-xl border text-center", s.color)}>
                  <div className="text-xl font-black tabular-nums">{s.val}</div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#687080]">{s.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Differences List */}
          <div className="aurora-glass-card overflow-hidden">
            <div className="px-5 py-3.5 border-b border-[#E2E6EE] flex items-center justify-between">
              <span className="text-sm font-bold text-[#1A1D26]">
                Detected Differences ({filteredDiffs.length})
              </span>
            </div>

            <div className="divide-y divide-[#E2E6EE]/80">
              {filteredDiffs.map((diff: ComparisonDifference, idx: number) => {
                const conf = DIFF_TYPE_CONFIG[diff.diff_type] || DIFF_TYPE_CONFIG.modified;
                const Icon = conf.icon;

                return (
                  <div key={diff.id || idx} className="p-5 space-y-3 hover:bg-white/50 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-2.5">
                        <div className={cn("p-1.5 rounded-lg border shrink-0 mt-0.5", conf.bg, conf.border, conf.color)}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-[#1A1D26]">{diff.title}</h4>
                          <span className="text-[10px] font-mono text-[#8F96A3] uppercase tracking-wider">
                            Category: {diff.category}
                          </span>
                        </div>
                      </div>

                      <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-semibold border", conf.bg, conf.border, conf.color)}>
                        {conf.label}
                      </span>
                    </div>

                    <p className="text-xs text-[#687080] leading-relaxed pl-8">
                      {diff.explanation}
                    </p>

                    {/* Side-by-side or stacked content comparison */}
                    {(diff.base_content || diff.target_content) && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pl-8 text-xs">
                        {diff.base_content && (
                          <div className="p-3 rounded-xl bg-red-50/40 border border-red-200/60">
                            <span className="text-[10px] font-bold text-red-700 uppercase tracking-wider block mb-1">
                              Base (Original)
                            </span>
                            <p className="font-mono text-[11px] text-[#1A1D26] leading-relaxed">
                              {diff.base_content}
                            </p>
                          </div>
                        )}
                        {diff.target_content && (
                          <div className="p-3 rounded-xl bg-emerald-50/40 border border-emerald-200/60">
                            <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider block mb-1">
                              Target (Revised)
                            </span>
                            <p className="font-mono text-[11px] text-[#1A1D26] leading-relaxed">
                              {diff.target_content}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

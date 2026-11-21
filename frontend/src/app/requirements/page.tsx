"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  CheckSquare,
  FileText,
  Sparkles,
  RefreshCw,
  Plus,
  Trash2,
  FileCheck2,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import {
  listDocuments,
  assessRequirements,
  type RequirementAssessment,
  type RequirementResult,
} from "@/lib/api";
import type { Document } from "@/types/extraction";
import { PageHeader } from "@/components/ui/PageHeader";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/design-tokens";

export default function RequirementsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [requirementsList, setRequirementsList] = useState<string[]>([
    "Must enforce AES-256 encryption at rest and in transit.",
    "Must include an explicit confidentiality and non-disclosure clause.",
    "Must specify clear termination notice of at least 30 calendar days.",
    "Must contain corporate dispute resolution and governing law jurisdiction.",
  ]);
  const [newReqInput, setNewReqInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [assessment, setAssessment] = useState<RequirementAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocs() {
      try {
        const docs = await listDocuments();
        setDocuments(docs);
        if (docs.length > 0) setSelectedDocId(docs[0].id);
      } catch (e: any) {
        console.error("Failed to fetch documents", e);
      }
    }
    loadDocs();
  }, []);

  const handleAddRequirement = () => {
    if (!newReqInput.trim()) return;
    setRequirementsList((prev) => [...prev, newReqInput.trim()]);
    setNewReqInput("");
  };

  const handleRemoveRequirement = (idx: number) => {
    setRequirementsList((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleRunAssessment = async () => {
    if (!selectedDocId) {
      setError("Please select a target document.");
      return;
    }
    if (requirementsList.length === 0) {
      setError("Please enter at least one requirement.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await assessRequirements({
        target_document_id: selectedDocId,
        manual_requirements: requirementsList,
      });
      setAssessment(res);
    } catch (err: unknown) {
      setError((err as Error).message || "Assessment failed. Check backend connectivity.");
    } finally {
      setLoading(false);
    }
  };

  const summary = assessment?.summary;

  return (
    <div className="space-y-6 select-none">
      {/* Page Header */}
      <PageHeader
        badge="Compliance & Alignment"
        title="Document Requirements &"
        highlightedTitle="Checklist Verification"
        description="Audit target documents against business checklists or compliance frameworks. Every requirement is verified with supporting evidence excerpts."
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Config Panel */}
        <div className="lg:col-span-5 space-y-5">
          <div className="aurora-glass-card p-6 space-y-5">
            <h3 className="text-sm font-bold flex items-center gap-2 text-[#1A1D26]">
              <FileText className="w-4 h-4 text-[#DC2626]" />
              Target Document
            </h3>

            {documents.length === 0 ? (
              <div className="p-4 rounded-xl aurora-glass-subtle border border-[#DDE0E6] text-xs text-[#687080]">
                No documents found.{" "}
                <a href="/inspection" className="text-[#DC2626] font-semibold hover:underline">
                  Upload a document
                </a>{" "}
                in the Inspection Portal first.
              </div>
            ) : (
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs md:text-sm bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename} ({d.file_extension.toUpperCase()})
                  </option>
                ))}
              </select>
            )}

            {/* Requirements list */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-[#1A1D26]">
                  Active Checklist ({requirementsList.length})
                </label>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {requirementsList.map((req, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 p-3 rounded-xl aurora-glass-subtle border border-[#DDE0E6]/80 text-xs"
                  >
                    <span className="font-mono font-bold text-[#DC2626] shrink-0 mt-0.5">
                      {i + 1}.
                    </span>
                    <span className="flex-1 leading-relaxed text-[#1A1D26]">{req}</span>
                    <button
                      onClick={() => handleRemoveRequirement(i)}
                      className="text-[#9CA3AF] hover:text-[#DC2626] transition-colors cursor-pointer shrink-0 ml-1"
                      aria-label="Remove requirement"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2 mt-3">
                <input
                  type="text"
                  value={newReqInput}
                  onChange={(e) => setNewReqInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddRequirement()}
                  placeholder="Add custom rule and press Enter…"
                  className="flex-1 px-3.5 py-2 rounded-xl text-xs bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
                />
                <SecondaryButton size="sm" onClick={handleAddRequirement} leftIcon={<Plus className="w-3.5 h-3.5" />}>
                  Add
                </SecondaryButton>
              </div>
            </div>

            {error && <ErrorState title="Verification Notice" message={error} />}

            <PrimaryButton
              size="md"
              onClick={handleRunAssessment}
              disabled={loading || documents.length === 0}
              loading={loading}
              className="w-full"
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Run Requirements Assessment
            </PrimaryButton>
          </div>
        </div>

        {/* Right Results Panel */}
        <div className="lg:col-span-7 space-y-5">
          {!assessment ? (
            <EmptyState
              icon={CheckSquare}
              title="Assessment Results"
              description="Select a target document, review or customize the requirement rules, and click Run Assessment to verify compliance."
            />
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {/* Summary Bar */}
              {summary && (
                <div className="aurora-glass-card p-5">
                  <h3 className="text-sm font-bold mb-3 text-[#1A1D26]">Assessment Breakdown</h3>
                  <div className="grid grid-cols-5 gap-2">
                    {[
                      { label: "MET", value: summary.MET, color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
                      { label: "PARTIAL", value: summary.PARTIALLY_MET, color: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
                      { label: "MISSING", value: summary.MISSING, color: "text-rose-700", bg: "bg-rose-50 border-rose-200" },
                      { label: "AMBIGUOUS", value: summary.AMBIGUOUS, color: "text-purple-700", bg: "bg-purple-50 border-purple-200" },
                      { label: "UNVERIFIABLE", value: summary.NOT_VERIFIABLE, color: "text-gray-700", bg: "bg-gray-100 border-gray-200" },
                    ].map((s) => (
                      <div
                        key={s.label}
                        className={cn("text-center p-2.5 rounded-xl border text-xs", s.bg)}
                      >
                        <div className={cn("text-lg font-black tabular-nums", s.color)}>
                          {s.value}
                        </div>
                        <div className="text-[10px] font-bold uppercase tracking-wider text-[#687080]">
                          {s.label}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Results List */}
              <div className="aurora-glass-card overflow-hidden">
                <div className="px-5 py-3.5 border-b border-[#E2E6EE] flex items-center justify-between">
                  <span className="text-sm font-bold text-[#1A1D26]">
                    Requirement Findings ({assessment.results.length})
                  </span>
                  <span className="text-xs text-[#687080] font-mono">
                    Target: {documents.find((d) => d.id === selectedDocId)?.filename}
                  </span>
                </div>

                <div className="divide-y divide-[#E2E6EE]/80">
                  {assessment.results.map((res: RequirementResult, idx: number) => (
                    <div key={res.id || idx} className="p-5 space-y-3 hover:bg-white/50 transition-colors">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-2.5">
                          <span className="font-mono text-xs font-bold text-[#DC2626] shrink-0 mt-0.5">
                            #{idx + 1}
                          </span>
                          <span className="text-xs md:text-sm font-bold text-[#1A1D26]">
                            {res.requirement_text}
                          </span>
                        </div>
                        <StatusIndicator status={res.status} size="sm" />
                      </div>

                      <p className="text-xs text-[#687080] leading-relaxed pl-6">
                        {res.explanation}
                      </p>

                      {res.supporting_evidence && (
                        <div className="ml-6 p-3 rounded-xl bg-white/70 border border-[#DDE0E6] text-xs">
                          <div className="text-[11px] font-semibold text-[#8F96A3] uppercase tracking-wider mb-1">
                            Supporting Excerpt {res.page_number ? `(Page ${res.page_number})` : ""}
                          </div>
                          <blockquote className="italic text-[#1A1D26] font-serif border-l-2 border-[#DC2626] pl-2.5">
                            &ldquo;{res.supporting_evidence}&rdquo;
                          </blockquote>
                        </div>
                      )}

                      <div className="ml-6 flex items-center justify-between text-[11px] font-mono text-[#8F96A3]">
                        <span>Confidence: {Math.round(res.confidence * 100)}%</span>
                        {res.page_number && <span>Verified on Page {res.page_number}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

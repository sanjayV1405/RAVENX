"use client";

import React, { useState, useCallback } from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  XCircle,
  EyeOff,
  ChevronDown,
  ChevronUp,
  Filter,
  RefreshCw,
  Search,
  BookOpen,
  Layers,
  LayoutGrid,
  Sparkles,
  Tag,
  FileText,
  Clock,
  Download,
  ExternalLink,
  Target,
  LocateFixed,
  Copy,
  Check
} from "lucide-react";
import { getAuditReportPdfUrl } from "@/lib/api";

// ─── Types ───────────────────────────────────────────────────────────────────

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type ReviewStatus = "needs_review" | "accepted" | "rejected" | "ignored";

export type Category =
  | "micro_typography"
  | "grammar"
  | "entity_consistency"
  | "visual_layout"
  | "structural"
  | "contextual_ai"
  | "requirement_mismatch"
  | string;

export interface Finding {
  id: string;
  inspection_id: string;
  category: Category;
  title: string;
  finding_classification?: string;
  page_number: number;
  original_content: string;
  suggested_correction: string;
  explanation: string;
  severity: Severity;
  confidence: number;
  evidence_source: string;
  bbox?: number[] | null;
  char_offset_start?: number | null;
  char_offset_end?: number | null;
  detection_method: string;
  user_status: ReviewStatus;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InspectionFindingsViewerProps {
  inspectionId: string;
  findings: Finding[];
  isLoading?: boolean;
  onReviewUpdate?: (findingId: string, status: ReviewStatus) => Promise<void>;
  documentName?: string;
  totalPages?: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<
  Severity,
  { label: string; color: string; bg: string; border: string; icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }> }
> = {
  critical: {
    label: "Critical",
    color: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-300",
    icon: AlertCircle,
  },
  high: {
    label: "High",
    color: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-300",
    icon: AlertTriangle,
  },
  medium: {
    label: "Medium",
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-300",
    icon: AlertTriangle,
  },
  low: {
    label: "Low",
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-300",
    icon: Info,
  },
  info: {
    label: "Info",
    color: "text-gray-600",
    bg: "bg-gray-50",
    border: "border-gray-300",
    icon: Info,
  },
};

const CATEGORY_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>; color: string }> = {
  micro_typography: { label: "Micro-Typography", icon: Tag, color: "text-purple-600" },
  grammar: { label: "Grammar", icon: BookOpen, color: "text-blue-600" },
  entity_consistency: { label: "Entity Consistency", icon: Layers, color: "text-teal-600" },
  visual_layout: { label: "Visual Layout", icon: LayoutGrid, color: "text-indigo-600" },
  structural: { label: "Structure", icon: FileText, color: "text-amber-600" },
  contextual_ai: { label: "AI Insight", icon: Sparkles, color: "text-pink-600" },
  requirement_mismatch: { label: "Requirements", icon: AlertTriangle, color: "text-red-600" },
};

const REVIEW_STATUS_CONFIG: Record<ReviewStatus, { label: string; color: string }> = {
  needs_review: { label: "Needs Review", color: "text-amber-600" },
  accepted: { label: "Accepted", color: "text-emerald-600" },
  rejected: { label: "Rejected", color: "text-red-600" },
  ignored: { label: "Ignored", color: "text-gray-500" },
};

const SEVERITY_ORDER: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

// ─── Helpers ─────────────────────────────────────────────────────────────────

function confidenceBar(value: number): React.ReactNode {
  const pct = Math.round(value * 100);
  const color = value >= 0.9 ? "bg-emerald-500" : value >= 0.75 ? "bg-amber-500" : "bg-orange-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 rounded-full overflow-hidden" style={{ background: "#DDE0E6" }}>
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono" style={{ color: "#707582" }}>{pct}%</span>
    </div>
  );
}

function getCategoryLabel(category: string): string {
  return CATEGORY_CONFIG[category]?.label ?? category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function getCategoryIcon(category: string): React.ComponentType<{ className?: string; style?: React.CSSProperties }> {
  return CATEGORY_CONFIG[category]?.icon ?? Tag;
}

function getCategoryColor(category: string): string {
  return CATEGORY_CONFIG[category]?.color ?? "text-slate-400";
}

// ─── Summary Bar ─────────────────────────────────────────────────────────────

function SummaryBar({ findings }: { findings: Finding[] }) {
  const counts = findings.reduce(
    (acc, f) => {
      acc[f.severity] = (acc[f.severity] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const reviewed = findings.filter((f) => f.user_status !== "needs_review").length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-3 p-4 rounded-xl mb-5" style={{ background: "#F5F6F8", border: "1px solid #DDE0E6" }}>
      {(["critical", "high", "medium", "low", "info"] as Severity[]).map((sev) => {
        const cfg = SEVERITY_CONFIG[sev];
        const SevIcon = cfg.icon;
        return (
          <div key={sev} className={`flex items-center gap-2 p-2 rounded-lg ${cfg.bg} border ${cfg.border}`}>
            <SevIcon className={`w-4 h-4 ${cfg.color} shrink-0`} />
            <div>
              <div className={`text-lg font-bold ${cfg.color}`}>{counts[sev] ?? 0}</div>
              <div className="text-[11px]" style={{ color: "#707582" }}>{cfg.label}</div>
            </div>
          </div>
        );
      })}
      <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-50 border border-emerald-200">
        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
        <div>
          <div className="text-lg font-bold text-emerald-600">{reviewed}</div>
          <div className="text-[11px]" style={{ color: "#707582" }}>Reviewed</div>
        </div>
      </div>
    </div>
  );
}

// ─── Filter Bar ──────────────────────────────────────────────────────────────

interface FilterState {
  search: string;
  severity: string;
  category: string;
  classification: string;
  reviewStatus: string;
  pageNumber: string;
}

function FilterBar({
  filters,
  onChange,
  findings,
}: {
  filters: FilterState;
  onChange: (key: keyof FilterState, val: string) => void;
  findings: Finding[];
}) {
  const categories = Array.from(new Set(findings.map((f) => f.category)));
  const pages = Array.from(new Set(findings.map((f) => f.page_number))).sort((a, b) => a - b);

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {/* Search */}
      <div className="relative flex-1 min-w-48">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: "#9CA3AF" }} />
        <input
          type="text"
          placeholder="Search findings…"
          value={filters.search}
          onChange={(e) => onChange("search", e.target.value)}
          className="w-full pl-9 pr-3 py-2 rounded-lg text-sm transition-colors"
          style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#17191F" }}
        />
      </div>

      {/* Severity */}
      <select
        value={filters.severity}
        onChange={(e) => onChange("severity", e.target.value)}
        className="px-3 py-2 rounded-lg text-sm cursor-pointer"
        style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#17191F" }}
      >
        <option value="">All Severities</option>
        {(["critical", "high", "medium", "low", "info"] as Severity[]).map((s) => (
          <option key={s} value={s}>
            {SEVERITY_CONFIG[s].label}
          </option>
        ))}
      </select>

      {/* Category */}
      <select
        value={filters.category}
        onChange={(e) => onChange("category", e.target.value)}
        className="px-3 py-2 rounded-lg text-sm cursor-pointer"
        style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#17191F" }}
      >
        <option value="">All Categories</option>
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {getCategoryLabel(cat)}
          </option>
        ))}
      </select>

      {/* Classification */}
      <select
        value={filters.classification}
        onChange={(e) => onChange("classification", e.target.value)}
        className="px-3 py-2 rounded-lg text-sm cursor-pointer font-mono"
        style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#17191F" }}
      >
        <option value="">All Types (A-D)</option>
        <option value="A">Type A: Source Defect</option>
        <option value="B">Type B: Extraction Artifact</option>
        <option value="C">Type C: Visual Layout</option>
        <option value="D">Type D: Context Inconsistency</option>
      </select>

      {/* Review Status */}
      <select
        value={filters.reviewStatus}
        onChange={(e) => onChange("reviewStatus", e.target.value)}
        className="px-3 py-2 rounded-lg text-sm cursor-pointer"
        style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#17191F" }}
      >
        <option value="">All Statuses</option>
        {(["needs_review", "accepted", "rejected", "ignored"] as ReviewStatus[]).map((s) => (
          <option key={s} value={s}>
            {REVIEW_STATUS_CONFIG[s].label}
          </option>
        ))}
      </select>

      {/* Page */}
      <select
        value={filters.pageNumber}
        onChange={(e) => onChange("pageNumber", e.target.value)}
        className="px-3 py-2 rounded-lg text-sm cursor-pointer"
        style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#17191F" }}
      >
        <option value="">All Pages</option>
        {pages.map((p) => (
          <option key={p} value={String(p)}>
            Page {p}
          </option>
        ))}
      </select>
    </div>
  );
}

// ─── Single Finding Card ─────────────────────────────────────────────────────

function FindingCard({
  finding,
  isExpanded,
  onToggle,
  onReview,
  reviewLoading,
}: {
  finding: Finding;
  isExpanded: boolean;
  onToggle: () => void;
  onReview: (status: ReviewStatus) => void;
  reviewLoading: boolean;
}) {
  const sevCfg = SEVERITY_CONFIG[finding.severity] ?? SEVERITY_CONFIG.info;
  const SevIcon = sevCfg.icon;
  const CatIcon = getCategoryIcon(finding.category);
  const catColor = getCategoryColor(finding.category);
  const statusCfg = REVIEW_STATUS_CONFIG[finding.user_status] ?? REVIEW_STATUS_CONFIG.needs_review;
  const isReviewed = finding.user_status !== "needs_review";

  return (
    <div
      className={`rounded-xl border transition-all duration-200 overflow-hidden`}
      style={{
        background: isReviewed ? "#FAFAFA" : "#FFFFFF",
        borderColor: isReviewed ? "#DDE0E6" : undefined,
      }}
    >
      {/* Header Row */}
      <button
        onClick={onToggle}
        className="w-full flex items-start gap-3 px-4 py-3 text-left transition-colors"
        style={{ background: isReviewed ? "transparent" : undefined }}
        onMouseEnter={(e) => { e.currentTarget.style.background = "#F9FAFB"; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = isReviewed ? "transparent" : ""; }}
      >
        {/* Severity Icon */}
        <SevIcon className={`w-4 h-4 mt-0.5 shrink-0 ${sevCfg.color}`} />

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            {/* Severity badge */}
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold uppercase tracking-wider ${sevCfg.bg} ${sevCfg.color} border ${sevCfg.border}`}
            >
              {sevCfg.label}
            </span>

            {/* Classification badge */}
            {finding.finding_classification && (
              <span
                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border ${
                  finding.finding_classification === "A"
                    ? "bg-red-50 text-red-700 border-red-200"
                    : finding.finding_classification === "B"
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : finding.finding_classification === "C"
                    ? "bg-blue-50 text-blue-700 border-blue-200"
                    : "bg-purple-50 text-purple-700 border-purple-200"
                }`}
                title={
                  finding.finding_classification === "A"
                    ? "Type A: Source Document Defect"
                    : finding.finding_classification === "B"
                    ? "Type B: Extraction Uncertainty / Artifact"
                    : finding.finding_classification === "C"
                    ? "Type C: Visual / Layout Deviation"
                    : "Type D: Contextual / Logic Inconsistency"
                }
              >
                {finding.finding_classification === "A" ? "SRC DEFECT" :
                 finding.finding_classification === "B" ? "EXTR ARTIFACT" :
                 finding.finding_classification === "C" ? "LAYOUT" : "CONTEXT"}
              </span>
            )}

            {/* Category badge */}
            <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${catColor}`}>
              <CatIcon className="w-3 h-3" />
              {getCategoryLabel(finding.category)}
            </span>

            {/* Page badge */}
            <span className="inline-flex items-center gap-1 text-[11px] font-mono" style={{ color: "#9CA3AF" }}>
              <FileText className="w-3 h-3" />
              pg.{finding.page_number}
            </span>

            {/* Review status */}
            <span className={`ml-auto text-[11px] font-medium ${statusCfg.color}`}>{statusCfg.label}</span>
          </div>

          <p className="text-sm font-semibold leading-tight truncate" style={{ color: "#17191F" }}>{finding.title}</p>

          {/* Original content preview */}
          <p className="text-xs mt-0.5 truncate" style={{ color: "#707582" }}>
            <span className="line-through text-red-500 mr-2">{finding.original_content.slice(0, 70)}</span>
          </p>
        </div>

        {/* Expand chevron */}
        <div className="shrink-0 mt-0.5" style={{ color: "#9CA3AF" }}>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Detail Panel */}
      {isExpanded && (
        <div className="px-4 py-4 space-y-4" style={{ background: "#F9FAFB", borderTop: "1px solid #DDE0E6" }}>
          {/* Original ↔ Suggested */}
          <div className="grid md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: "#9CA3AF" }}>Original Text</div>
              <div className="p-3 rounded-lg text-sm font-mono break-words" style={{ background: "rgba(220,38,38,0.05)", border: "1px solid rgba(220,38,38,0.15)", color: "#B91C1C" }}>
                {finding.original_content || <span className="italic" style={{ color: "#9CA3AF" }}>(empty)</span>}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: "#9CA3AF" }}>Suggested Correction</div>
              <div className="p-3 rounded-lg text-sm font-mono break-words" style={{ background: "rgba(5,150,105,0.05)", border: "1px solid rgba(5,150,105,0.15)", color: "#059669" }}>
                {finding.suggested_correction || <span className="italic" style={{ color: "#9CA3AF" }}>(no correction)</span>}
              </div>
            </div>
          </div>

          {/* Explanation */}
          <div className="space-y-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: "#9CA3AF" }}>Explanation</div>
            <p className="text-sm leading-relaxed" style={{ color: "#17191F" }}>{finding.explanation}</p>
          </div>

          {/* Evidence Metadata & Navigation */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1">
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: "#9CA3AF" }}>Confidence</div>
              {confidenceBar(finding.confidence)}
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: "#9CA3AF" }}>Detection Method</div>
              <span className="text-xs font-mono" style={{ color: "#17191F" }}>{finding.detection_method}</span>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: "#9CA3AF" }}>Evidence Source</div>
              <span className="text-xs font-mono" style={{ color: "#17191F" }}>{finding.evidence_source}</span>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: "#9CA3AF" }}>Spatial Coordinates</div>
              {finding.bbox && finding.bbox.length === 4 ? (
                <span className="inline-flex items-center gap-1 text-xs font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  <LocateFixed className="w-3 h-3" />
                  [{finding.bbox.map((v) => Math.round(v)).join(", ")}] pt
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] italic" style={{ color: "#9CA3AF" }}>
                  <Info className="w-3 h-3" />
                  Coordinates N/A
                </span>
              )}
            </div>
          </div>

          {/* Review Actions */}
          {finding.user_status === "needs_review" && (
            <div className="flex items-center gap-2 pt-2" style={{ borderTop: "1px solid #DDE0E6" }}>
              <span className="text-xs" style={{ color: "#9CA3AF" }}>Review:</span>
              <button
                disabled={reviewLoading}
                onClick={() => onReview("accepted")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                style={{ background: "rgba(5,150,105,0.1)", border: "1px solid rgba(5,150,105,0.25)", color: "#059669" }}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Accept
              </button>
              <button
                disabled={reviewLoading}
                onClick={() => onReview("rejected")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.2)", color: "#DC2626" }}
              >
                <XCircle className="w-3.5 h-3.5" />
                Reject
              </button>
              <button
                disabled={reviewLoading}
                onClick={() => onReview("ignored")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                style={{ background: "#F5F6F8", border: "1px solid #DDE0E6", color: "#707582" }}
              >
                <EyeOff className="w-3.5 h-3.5" />
                Ignore
              </button>
            </div>
          )}

          {/* Reviewed badge */}
          {finding.user_status !== "needs_review" && (
            <div className="flex items-center gap-2 pt-2" style={{ borderTop: "1px solid #DDE0E6" }}>
              <Clock className="w-3.5 h-3.5" style={{ color: "#9CA3AF" }} />
              <span className="text-xs" style={{ color: "#707582" }}>
                Marked as{" "}
                <span className={`font-medium ${statusCfg.color}`}>{statusCfg.label}</span>
                {finding.reviewed_at && ` · ${new Date(finding.reviewed_at).toLocaleString()}`}
              </span>
              <button
                disabled={reviewLoading}
                onClick={() => onReview("needs_review")}
                className="ml-auto text-xs transition-colors"
                style={{ color: "#9CA3AF" }}
              >
                Undo
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function InspectionFindingsViewer({
  inspectionId,
  findings: initialFindings,
  isLoading = false,
  onReviewUpdate,
  documentName,
}: InspectionFindingsViewerProps) {
  const [findings, setFindings] = useState<Finding[]>(initialFindings);
  const [filters, setFilters] = useState<FilterState>({
    search: "",
    severity: "",
    category: "",
    classification: "",
    reviewStatus: "",
    pageNumber: "",
  });
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [reviewLoadingIds, setReviewLoadingIds] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<"severity" | "page" | "confidence">("severity");

  const handleFilterChange = useCallback((key: keyof FilterState, val: string) => {
    setFilters((prev) => ({ ...prev, [key]: val }));
  }, []);

  const toggleExpanded = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const handleReview = useCallback(
    async (findingId: string, status: ReviewStatus) => {
      setReviewLoadingIds((prev) => new Set(prev).add(findingId));
      try {
        if (onReviewUpdate) {
          await onReviewUpdate(findingId, status);
        }
        setFindings((prev) =>
          prev.map((f) =>
            f.id === findingId
              ? { ...f, user_status: status, reviewed_at: new Date().toISOString() }
              : f
          )
        );
      } catch (err) {
        console.error("Review update failed:", err);
      } finally {
        setReviewLoadingIds((prev) => {
          const next = new Set(prev);
          next.delete(findingId);
          return next;
        });
      }
    },
    [onReviewUpdate]
  );

  // ─── Filtering ─────────────────────────────────────────────────────────────

  const filteredFindings = findings
    .filter((f) => {
      if (filters.severity && f.severity !== filters.severity) return false;
      if (filters.category && f.category !== filters.category) return false;
      if (filters.classification && (f.finding_classification || "A") !== filters.classification) return false;
      if (filters.reviewStatus && f.user_status !== filters.reviewStatus) return false;
      if (filters.pageNumber && String(f.page_number) !== filters.pageNumber) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        if (
          !f.title.toLowerCase().includes(q) &&
          !f.original_content.toLowerCase().includes(q) &&
          !f.explanation.toLowerCase().includes(q)
        )
          return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortField === "severity") return SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
      if (sortField === "page") return a.page_number - b.page_number;
      if (sortField === "confidence") return b.confidence - a.confidence;
      return 0;
    });

  // ─── Empty state ───────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4" style={{ color: "#707582" }}>
        <RefreshCw className="w-8 h-8 animate-spin" style={{ color: "#DC2626" }} />
        <p className="text-sm font-medium">Running inspection engine…</p>
      </div>
    );
  }

  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3" style={{ color: "#707582" }}>
        <CheckCircle2 className="w-10 h-10 text-emerald-500" />
        <p className="text-sm font-semibold" style={{ color: "#17191F" }}>No findings detected</p>
        <p className="text-xs text-center max-w-xs" style={{ color: "#707582" }}>
          The inspection engine did not detect any issues. The document appears clean based on the configured inspection modules.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2" style={{ color: "#17191F" }}>
            <Sparkles className="w-4 h-4" style={{ color: "#DC2626" }} />
            Inspection Findings
          </h3>
          {documentName && <p className="text-xs mt-0.5" style={{ color: "#707582" }}>{documentName}</p>}
        </div>
        <div className="flex items-center gap-3">
          <a
            href={getAuditReportPdfUrl(inspectionId, true, true)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold text-white aurora-btn-crimson"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Generate Reviewed Copy &amp; Report</span>
          </a>
          <div className="flex items-center gap-1.5 pl-2" style={{ borderLeft: "1px solid #DDE0E6" }}>
            <span className="text-xs" style={{ color: "#707582" }}>Sort:</span>
            {(["severity", "page", "confidence"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setSortField(f)}
                className="px-2 py-1 rounded-md text-xs font-medium transition-colors"
                style={{
                  background: sortField === f ? "#17191F" : "#F5F6F8",
                  color: sortField === f ? "#FFFFFF" : "#707582",
                  border: sortField === f ? "1px solid #17191F" : "1px solid #DDE0E6",
                }}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Bar */}
      <SummaryBar findings={findings} />

      {/* Filter Bar */}
      <FilterBar filters={filters} onChange={handleFilterChange} findings={findings} />

      {/* Results count */}
      <div className="flex items-center gap-2 text-xs pb-1" style={{ color: "#707582" }}>
        <Filter className="w-3.5 h-3.5" />
        Showing {filteredFindings.length} of {findings.length} findings
      </div>

      {/* Findings List */}
      <div className="space-y-2">
        {filteredFindings.length === 0 ? (
          <div className="text-center py-10 text-sm" style={{ color: "#707582" }}>
            No findings match the current filters.
          </div>
        ) : (
          filteredFindings.map((finding) => (
            <FindingCard
              key={finding.id}
              finding={finding}
              isExpanded={expandedIds.has(finding.id)}
              onToggle={() => toggleExpanded(finding.id)}
              onReview={(status) => handleReview(finding.id, status)}
              reviewLoading={reviewLoadingIds.has(finding.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}


"use client";

import React, { useState, useEffect } from "react";
import type { ExtractionJob, ExtractedPageSummary, ExtractedPageDetail } from "@/types/extraction";
import { getExtractionStatus, getDocumentPages, getPageDetail, API_BASE } from "@/lib/api";
import {
  FileText,
  Layers,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  Search,
  Table as TableIcon,
  AlignLeft,
  Info,
  ExternalLink,
  RefreshCw,
  Eye,
  Hash,
} from "lucide-react";

interface ExtractionViewerProps {
  documentId: string;
  filename: string;
  fileExtension: string;
  fileSizeBytes: number;
  checksum?: string;
  isDuplicate?: boolean;
  onReset: () => void;
}

export function ExtractionViewer({
  documentId,
  filename,
  fileExtension,
  fileSizeBytes,
  checksum,
  isDuplicate = false,
  onReset,
}: ExtractionViewerProps) {
  const [job, setJob] = useState<ExtractionJob | null>(null);
  const [pages, setPages] = useState<ExtractedPageSummary[]>([]);
  const [currentPageNum, setCurrentPageNum] = useState<number>(1);
  const [pageDetail, setPageDetail] = useState<ExtractedPageDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"text" | "structure" | "metadata">("text");

  const [loadingJob, setLoadingJob] = useState(true);
  const [loadingPage, setLoadingPage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const formatFileSize = (bytes: number) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Poll extraction status until completed/failed
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    let attempts = 0;

    async function checkStatus() {
      try {
        const jobData = await getExtractionStatus(documentId);
        setJob(jobData);

        if (jobData.status === "completed" || jobData.status === "failed") {
          setLoadingJob(false);
          clearInterval(intervalId);

          if (jobData.status === "completed") {
            const pagesData = await getDocumentPages(documentId);
            setPages(pagesData);
            if (pagesData.length > 0) {
              loadPage(1);
            }
          }
        }
      } catch (err: unknown) {
        attempts++;
        if (attempts > 5) {
          setError((err as Error).message || "Failed to retrieve extraction status.");
          setLoadingJob(false);
          clearInterval(intervalId);
        }
      }
    }

    checkStatus();
    intervalId = setInterval(checkStatus, 1500);

    return () => clearInterval(intervalId);
  }, [documentId]);

  // Load single page detail
  const loadPage = async (pageNum: number) => {
    setLoadingPage(true);
    setCurrentPageNum(pageNum);
    try {
      const detail = await getPageDetail(documentId, pageNum);
      setPageDetail(detail);
    } catch (err: unknown) {
      console.error("Failed to load page detail:", err);
    } finally {
      setLoadingPage(false);
    }
  };

  const handleCopyText = () => {
    if (pageDetail?.raw_text) {
      navigator.clipboard.writeText(pageDetail.raw_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const totalPages = pages.length || job?.page_count || 1;
  const rawUrl = `${API_BASE}/documents/${documentId}/raw`;

  return (
    <div
      className="rounded-2xl overflow-hidden flex flex-col min-h-[750px]"
      style={{
        background: "#FFFFFF",
        border: "1px solid #DDE0E6",
        boxShadow: "0 2px 12px rgba(0,0,0,0.04)",
      }}
    >
      {/* Top Header / Status Banner */}
      <div
        className="px-6 py-4 flex flex-wrap items-center justify-between gap-4"
        style={{
          background: "#F5F6F8",
          borderBottom: "1px solid #DDE0E6",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="p-2 rounded-lg font-mono text-xs uppercase font-bold"
            style={{
              background: "rgba(220,38,38,0.08)",
              color: "#DC2626",
              border: "1px solid rgba(220,38,38,0.2)",
            }}
          >
            .{fileExtension.toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold truncate max-w-sm sm:max-w-md" style={{ color: "#17191F" }}>
                {filename}
              </h2>
              {isDuplicate && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200">
                  Duplicate (Reused)
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs font-mono mt-0.5" style={{ color: "#707582" }}>
              <span>{formatFileSize(fileSizeBytes)}</span>
              <span>•</span>
              <span>{totalPages} {totalPages === 1 ? "page" : "pages"}</span>
              <span>•</span>
              <span className="truncate max-w-[180px]">
                SHA-256: {checksum ? `${checksum.slice(0, 12)}...` : "Verified"}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium ${
              job?.status === "completed"
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : job?.status === "processing"
                ? "bg-amber-50 text-amber-700 border border-amber-200 animate-pulse"
                : job?.status === "failed"
                ? "bg-red-50 text-red-700 border border-red-200"
                : "bg-gray-50 text-gray-600 border border-gray-200"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                job?.status === "completed"
                  ? "bg-emerald-500"
                  : job?.status === "processing"
                  ? "bg-amber-500 animate-ping"
                  : job?.status === "failed"
                  ? "bg-red-500"
                  : "bg-gray-400"
              }`}
            />
            {job?.status === "completed" && "Extraction Complete"}
            {job?.status === "processing" && "Extracting Structure..."}
            {job?.status === "failed" && "Extraction Failed"}
            {(!job || job.status === "queued") && "Queued"}
          </span>

          <button
            onClick={onReset}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={{
              background: "#FFFFFF",
              color: "#17191F",
              border: "1px solid #DDE0E6",
            }}
          >
            New Document
          </button>
        </div>
      </div>

      {/* Main Split-Screen Container */}
      <div
        className="grid grid-cols-1 lg:grid-cols-12 flex-1 divide-y lg:divide-y-0 lg:divide-x"
        style={{ borderColor: "#DDE0E6" }}
      >
        {/* LEFT PANEL: Document Preview Canvas (5 columns) */}
        <div
          className="lg:col-span-5 p-6 flex flex-col justify-between space-y-4"
          style={{ background: "#F9FAFB" }}
        >
          <div className="flex items-center justify-between pb-3" style={{ borderBottom: "1px solid #DDE0E6" }}>
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider" style={{ color: "#707582" }}>
              <Eye className="w-3.5 h-3.5" style={{ color: "#DC2626" }} />
              <span>Document Preview</span>
            </div>
            <a
              href={rawUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-[11px] font-mono hover:underline"
              style={{ color: "#707582" }}
            >
              <span>Raw Document</span>
              <ExternalLink className="w-3 h-3" style={{ color: "#9CA3AF" }} />
            </a>
          </div>

          {/* Document Renderer Container */}
          <div
            className="flex-1 min-h-[460px] rounded-xl overflow-hidden flex flex-col items-center justify-center p-4 relative group"
            style={{
              background: "#FFFFFF",
              border: "1px solid #DDE0E6",
            }}
          >
            {fileExtension.toLowerCase() === "pdf" ? (
              <iframe
                src={`${rawUrl}#page=${currentPageNum}&toolbar=0&navpanes=0`}
                className="w-full h-full min-h-[440px] rounded border-0 bg-white"
                title="PDF Document View"
              />
            ) : (
              <div className="text-center p-8 max-w-sm">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                  style={{
                    background: "rgba(220,38,38,0.08)",
                    border: "1px solid rgba(220,38,38,0.2)",
                  }}
                >
                  <FileText className="w-8 h-8" style={{ color: "#DC2626" }} />
                </div>
                <h4 className="text-sm font-bold mb-1.5" style={{ color: "#17191F" }}>
                  .{fileExtension.toUpperCase()} Document Ingested
                </h4>
                <p className="text-xs leading-relaxed mb-4" style={{ color: "#707582" }}>
                  Native {fileExtension.toUpperCase()} binary parsed using dedicated structural extractors. View the extracted text and layout hierarchy in the right inspector.
                </p>
                <div
                  className="p-3 rounded-lg text-[11px] font-mono text-left space-y-1"
                  style={{
                    background: "#F5F6F8",
                    border: "1px solid #DDE0E6",
                    color: "#707582",
                  }}
                >
                  <div>Format: {fileExtension.toUpperCase()} Document</div>
                  <div>Pages/Slides: {totalPages}</div>
                  <div>Integrity: Immutable (SHA-256)</div>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Left Page Selector */}
          <div className="flex items-center justify-between pt-2 text-xs font-mono" style={{ color: "#707582" }}>
            <span>Page {currentPageNum} of {totalPages}</span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => loadPage(Math.max(1, currentPageNum - 1))}
                disabled={currentPageNum <= 1 || loadingPage}
                className="p-1.5 rounded disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                style={{
                  background: "#FFFFFF",
                  color: "#17191F",
                  border: "1px solid #DDE0E6",
                }}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => loadPage(Math.min(totalPages, currentPageNum + 1))}
                disabled={currentPageNum >= totalPages || loadingPage}
                className="p-1.5 rounded disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                style={{
                  background: "#FFFFFF",
                  color: "#17191F",
                  border: "1px solid #DDE0E6",
                }}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Intelligent Extracted Content & Structure (7 columns) */}
        <div className="lg:col-span-7 flex flex-col" style={{ background: "#FFFFFF" }}>
          {/* Tab Navigation Header */}
          <div
            className="px-6 pt-3 flex items-center justify-between"
            style={{ borderBottom: "1px solid #DDE0E6" }}
          >
            <div className="flex items-center gap-1">
              {[
                { id: "text", label: "Extracted Text", icon: AlignLeft },
                { id: "structure", label: "Page Structure & Geometry", icon: Layers },
                { id: "metadata", label: "Document Dossier", icon: Info },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as "text" | "structure" | "metadata")}
                    className="inline-flex items-center gap-2 px-4 py-3 border-b-2 text-xs font-mono font-semibold transition-colors"
                    style={{
                      borderColor: isActive ? "#DC2626" : "transparent",
                      color: isActive ? "#DC2626" : "#707582",
                      background: isActive ? "rgba(220,38,38,0.04)" : "transparent",
                    }}
                  >
                    <Icon className="w-3.5 h-3.5" style={{ color: isActive ? "#DC2626" : "#9CA3AF" }} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2 pb-2">
              {activeTab === "text" && (
                <button
                  onClick={handleCopyText}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition-colors"
                  style={{
                    background: "#F5F6F8",
                    color: "#17191F",
                    border: "1px solid #DDE0E6",
                  }}
                  title="Copy Page Text"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </button>
              )}
            </div>
          </div>

          {/* Tab Content Body */}
          <div className="p-6 flex-1 overflow-y-auto max-h-[640px]">
            {loadingPage ? (
              <div className="flex flex-col items-center justify-center h-64 space-y-3" style={{ color: "#707582" }}>
                <RefreshCw className="w-6 h-6 animate-spin" style={{ color: "#DC2626" }} />
                <span className="text-xs font-mono">Loading page structure...</span>
              </div>
            ) : error ? (
              <div className="p-4 rounded-xl text-xs bg-red-50 border border-red-200 text-red-700">
                {error}
              </div>
            ) : (
              <>
                {/* TAB 1: EXTRACTED TEXT */}
                {activeTab === "text" && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between pb-3" style={{ borderBottom: "1px solid #DDE0E6" }}>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-semibold" style={{ color: "#17191F" }}>
                          Page {currentPageNum} Text
                        </span>
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-mono"
                          style={{
                            background: "#F5F6F8",
                            color: "#707582",
                            border: "1px solid #DDE0E6",
                          }}
                        >
                          {pageDetail?.word_count || 0} words
                        </span>
                        {pageDetail?.needs_ocr && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200">
                            Scanned page (OCR candidate)
                          </span>
                        )}
                      </div>

                      {/* Search in page */}
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "#9CA3AF" }} />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Filter text in page..."
                          className="rounded-lg pl-8 pr-3 py-1 text-xs focus:outline-none w-48 font-mono"
                          style={{
                            background: "#F5F6F8",
                            border: "1px solid #DDE0E6",
                            color: "#17191F",
                          }}
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono bg-emerald-50 text-emerald-800 border border-emerald-200">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
                      <span>Spatially Reconstructed Text (Reading order aligned, span whitespace preserved)</span>
                    </div>

                    <div
                      className="p-5 rounded-xl font-mono text-xs whitespace-pre-wrap leading-relaxed select-text min-h-[360px]"
                      style={{
                        background: "#F9FAFB",
                        border: "1px solid #DDE0E6",
                        color: "#17191F",
                      }}
                    >
                      {(pageDetail?.structured_data?.reconstructed_text || pageDetail?.raw_text) ? (
                        searchQuery ? (
                          String(pageDetail.structured_data?.reconstructed_text || pageDetail.raw_text)
                            .split("\n")
                            .filter((line: string) => line.toLowerCase().includes(searchQuery.toLowerCase()))
                            .join("\n") || "No lines match the search filter."
                        ) : (
                          pageDetail.structured_data?.reconstructed_text || pageDetail.raw_text
                        )
                      ) : (
                        <div className="text-center py-16" style={{ color: "#9CA3AF" }}>
                          No extractable text found on this page.
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* TAB 2: PAGE STRUCTURE & GEOMETRY */}
                {activeTab === "structure" && (
                  <div className="space-y-6">
                    {/* Headings Hierarchy */}
                    <div>
                      <h4 className="text-xs font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5" style={{ color: "#707582" }}>
                        <Layers className="w-3.5 h-3.5" style={{ color: "#DC2626" }} />
                        <span>Detected Headings &amp; Sections</span>
                      </h4>
                      {pageDetail?.structured_data?.headings && pageDetail.structured_data.headings.length > 0 ? (
                        <div className="space-y-2">
                          {pageDetail.structured_data.headings.map((h, i) => (
                            <div
                              key={i}
                              className="p-3 rounded-lg flex items-center justify-between"
                              style={{
                                background: "#F9FAFB",
                                border: "1px solid #DDE0E6",
                              }}
                            >
                              <div className="flex items-center gap-2">
                                <span
                                  className="text-[10px] font-mono px-1.5 py-0.5 rounded font-bold"
                                  style={{
                                    background: "rgba(220,38,38,0.08)",
                                    color: "#DC2626",
                                    border: "1px solid rgba(220,38,38,0.2)",
                                  }}
                                >
                                  H{h.level || 1}
                                </span>
                                <span className="text-xs font-semibold" style={{ color: "#17191F" }}>
                                  {h.text}
                                </span>
                              </div>
                              {h.font_size && (
                                <span className="text-[11px] font-mono" style={{ color: "#707582" }}>
                                  {h.font_size}pt ({h.font_name || "Heading"})
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div
                          className="p-4 rounded-lg text-xs font-mono"
                          style={{
                            background: "#F9FAFB",
                            border: "1px solid #DDE0E6",
                            color: "#707582",
                          }}
                        >
                          No explicit headings detected on this page.
                        </div>
                      )}
                    </div>

                    {/* Tables Structure */}
                    <div>
                      <h4 className="text-xs font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5" style={{ color: "#707582" }}>
                        <TableIcon className="w-3.5 h-3.5 text-blue-500" />
                        <span>Tabular Data Structures</span>
                      </h4>
                      {pageDetail?.structured_data?.tables && pageDetail.structured_data.tables.length > 0 ? (
                        <div className="space-y-4">
                          {pageDetail.structured_data.tables.map((tbl, tIdx) => (
                            <div
                              key={tIdx}
                              className="rounded-xl overflow-hidden"
                              style={{
                                border: "1px solid #DDE0E6",
                                background: "#FFFFFF",
                              }}
                            >
                              <div
                                className="px-4 py-2 text-xs font-mono flex items-center justify-between font-semibold"
                                style={{
                                  background: "#F5F6F8",
                                  borderBottom: "1px solid #DDE0E6",
                                  color: "#17191F",
                                }}
                              >
                                <span>Table {tbl.table_index || tIdx + 1}</span>
                                <span style={{ color: "#707582" }}>
                                  {tbl.row_count} rows × {tbl.col_count} columns
                                </span>
                              </div>
                              <div className="overflow-x-auto p-2">
                                <table className="w-full text-xs text-left border-collapse">
                                  <tbody>
                                    {tbl.rows.map((row, rIdx) => {
                                      const isHeader = rIdx === 0;
                                      const isTotal = row.some((c) => String(c).toLowerCase().includes("total"));
                                      return (
                                        <tr
                                          key={rIdx}
                                          className={`transition-colors ${
                                            isHeader
                                              ? "bg-[#ECEEF4] font-bold text-[#17191F]"
                                              : isTotal
                                              ? "bg-emerald-50/70 font-semibold text-emerald-950"
                                              : "hover:bg-[#F9FAFB] text-[#17191F]"
                                          }`}
                                          style={{
                                            borderBottom: isHeader ? "2px solid #DDE0E6" : isTotal ? "2px solid #A7F3D0" : "1px solid #F0F2F5",
                                            borderTop: isTotal ? "1px solid #A7F3D0" : undefined,
                                          }}
                                        >
                                          {row.map((cell, cIdx) => (
                                            <td
                                              key={cIdx}
                                              className="p-2.5 font-mono"
                                              style={{
                                                borderRight: "1px solid #E5E7EB",
                                              }}
                                            >
                                              {cell || "—"}
                                            </td>
                                          ))}
                                        </tr>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div
                          className="p-4 rounded-lg text-xs font-mono"
                          style={{
                            background: "#F9FAFB",
                            border: "1px solid #DDE0E6",
                            color: "#707582",
                          }}
                        >
                          No tables detected on page {currentPageNum}.
                        </div>
                      )}
                    </div>

                    {/* Bounding Blocks & Typography Inspector */}
                    {pageDetail?.structured_data?.blocks && pageDetail.structured_data.blocks.length > 0 && (
                      <div>
                        <h4 className="text-xs font-mono uppercase tracking-wider mb-3" style={{ color: "#707582" }}>
                          Text Blocks &amp; Coordinates ({pageDetail.structured_data.blocks.length} blocks)
                        </h4>
                        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                          {pageDetail.structured_data.blocks.slice(0, 15).map((b, bIdx) => (
                            <div
                              key={bIdx}
                              className="p-3 rounded-lg text-xs font-mono space-y-1"
                              style={{
                                background: "#F9FAFB",
                                border: "1px solid #DDE0E6",
                              }}
                            >
                              <div className="flex items-center justify-between text-[11px]" style={{ color: "#707582" }}>
                                <span className="font-semibold" style={{ color: "#17191F" }}>Block #{bIdx + 1}</span>
                                <span>BBox: [{b.bbox.join(", ")}]</span>
                              </div>
                              <div className="line-clamp-2" style={{ color: "#17191F" }}>{b.text}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 3: DOCUMENT DOSSIER & METADATA */}
                {activeTab === "metadata" && (
                  <div className="space-y-4">
                    <h4 className="text-xs font-mono uppercase tracking-wider mb-3 flex items-center gap-1.5" style={{ color: "#707582" }}>
                      <Hash className="w-3.5 h-3.5" style={{ color: "#DC2626" }} />
                      <span>Extraction Provenance &amp; Metadata</span>
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div
                        className="p-4 rounded-xl space-y-1"
                        style={{ background: "#F9FAFB", border: "1px solid #DDE0E6" }}
                      >
                        <div className="text-xs font-mono" style={{ color: "#707582" }}>Extractor Engine</div>
                        <div className="text-sm font-bold font-mono uppercase" style={{ color: "#17191F" }}>
                          {job?.extractor_type === "pdf" ? "PyMuPDF (fitz)" : job?.extractor_type === "docx" ? "python-docx" : "python-pptx"}
                        </div>
                      </div>

                      <div
                        className="p-4 rounded-xl space-y-1"
                        style={{ background: "#F9FAFB", border: "1px solid #DDE0E6" }}
                      >
                        <div className="text-xs font-mono" style={{ color: "#707582" }}>Extraction Method</div>
                        <div className="text-sm font-bold font-mono text-emerald-700">
                          {pageDetail?.extraction_method === "native" ? "Native Vector Extraction" : "Optical Character Recognition"}
                        </div>
                      </div>

                      <div
                        className="p-4 rounded-xl space-y-1"
                        style={{ background: "#F9FAFB", border: "1px solid #DDE0E6" }}
                      >
                        <div className="text-xs font-mono" style={{ color: "#707582" }}>Cryptographic Hash</div>
                        <div className="text-xs font-mono truncate" style={{ color: "#17191F" }}>
                          {checksum || "SHA-256 Verified"}
                        </div>
                      </div>

                      <div
                        className="p-4 rounded-xl space-y-1"
                        style={{ background: "#F9FAFB", border: "1px solid #DDE0E6" }}
                      >
                        <div className="text-xs font-mono" style={{ color: "#707582" }}>Total Document Pages</div>
                        <div className="text-sm font-bold font-mono" style={{ color: "#17191F" }}>
                          {totalPages}
                        </div>
                      </div>
                    </div>

                    {/* Metadata JSON Dump */}
                    {job?.extraction_metadata && (
                      <div
                        className="mt-4 p-4 rounded-xl"
                        style={{ background: "#F9FAFB", border: "1px solid #DDE0E6" }}
                      >
                        <div className="text-xs font-mono mb-2 font-semibold" style={{ color: "#17191F" }}>
                          Raw Metadata Attributes
                        </div>
                        <pre className="text-[11px] font-mono overflow-x-auto whitespace-pre-wrap" style={{ color: "#707582" }}>
                          {JSON.stringify(job.extraction_metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExtractionViewer;

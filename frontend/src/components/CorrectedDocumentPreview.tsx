"use client";

import React, { useState } from "react";
import {
  Download,
  FileCheck,
  CheckCircle2,
  Lock,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  FileText,
  RefreshCw,
  Sparkles,
  Layers,
} from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";
import { getCorrectedDownloadUrl, getCorrectedPreviewUrl, getAuditReportPdfUrl, type CorrectedDocumentInfo } from "@/lib/api";

interface CorrectedDocumentPreviewProps {
  inspectionId: string;
  documentId: string;
  originalFilename: string;
  fileExtension: string;
  correctedInfo: CorrectedDocumentInfo;
  onReset: () => void;
}

export function CorrectedDocumentPreview({
  inspectionId,
  documentId,
  originalFilename,
  fileExtension,
  correctedInfo,
  onReset,
}: CorrectedDocumentPreviewProps) {
  const [downloading, setDownloading] = useState(false);
  const ext = fileExtension.toLowerCase().replace(".", "");

  const downloadUrl = getCorrectedDownloadUrl(inspectionId);
  const previewUrl = getCorrectedPreviewUrl(inspectionId);
  const auditReportUrl = getAuditReportPdfUrl(inspectionId);

  const handleDownload = () => {
    setDownloading(true);
    window.location.href = downloadUrl;
    setTimeout(() => setDownloading(false), 2000);
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Top Completion Glass Banner */}
      <div
        className="p-6 rounded-2xl relative overflow-hidden"
        style={{
          background: "linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,253,244,0.9) 100%)",
          border: "1px solid #BBF7D0",
          boxShadow: "0 8px 30px rgba(16, 185, 129, 0.08)",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-sm"
              style={{
                background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                color: "#FFFFFF",
              }}
            >
              <FileCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  CORRECTION SUCCESSFUL
                </span>
                <span className="text-xs font-mono text-emerald-700">
                  {correctedInfo.applied_findings_count} {correctedInfo.applied_findings_count === 1 ? "mistake" : "mistakes"} corrected
                </span>
              </div>
              <h2 className="text-lg font-bold mt-1 text-[#17191F]">
                {correctedInfo.corrected_filename}
              </h2>
              <p className="text-xs text-[#707582] mt-0.5">
                Generated native .{ext.toUpperCase()} document with preserved formatting and layout. Original file remains untouched.
              </p>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-2.5">
            <PrimaryButton
              size="md"
              onClick={handleDownload}
              loading={downloading}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Download Corrected Document
            </PrimaryButton>
            <a
              href={auditReportUrl}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2.5 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
              style={{
                background: "#FFFFFF",
                color: "#17191F",
                border: "1px solid #DDE0E6",
              }}
            >
              <FileText className="w-3.5 h-3.5 text-[#DC2626]" />
              <span>Audit Report (PDF)</span>
            </a>
            <button
              onClick={onReset}
              className="px-3 py-2.5 rounded-xl text-xs font-semibold text-[#707582] hover:text-[#17191F] transition-colors cursor-pointer"
            >
              New Document
            </button>
          </div>
        </div>

        {/* File Verification Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-emerald-100 text-xs font-mono">
          <div>
            <span className="text-[#707582]">File Size:</span>{" "}
            <span className="font-semibold text-[#17191F]">{formatFileSize(correctedInfo.file_size_bytes)}</span>
          </div>
          <div>
            <span className="text-[#707582]">Format:</span>{" "}
            <span className="font-semibold text-[#17191F]">.{ext.toUpperCase()} Document</span>
          </div>
          <div className="truncate">
            <span className="text-[#707582]">SHA-256:</span>{" "}
            <span className="font-semibold text-[#17191F]" title={correctedInfo.checksum}>
              {correctedInfo.checksum ? `${correctedInfo.checksum.slice(0, 10)}...` : "Verified"}
            </span>
          </div>
          <div>
            <span className="text-[#707582]">Integrity:</span>{" "}
            <span className="font-semibold text-emerald-700 flex items-center gap-1 inline-flex">
              <ShieldCheck className="w-3.5 h-3.5" /> Immutable
            </span>
          </div>
        </div>
      </div>

      {/* Main Split Layout: Live Preview & Changes Applied */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Document Preview (7 columns) */}
        <div
          className="lg:col-span-7 rounded-2xl p-5 flex flex-col space-y-4"
          style={{
            background: "#FFFFFF",
            border: "1px solid #DDE0E6",
            boxShadow: "0 2px 12px rgba(0,0,0,0.03)",
          }}
        >
          <div className="flex items-center justify-between pb-3 border-b border-[#DDE0E6]">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#707582]">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              <span>Corrected Document Preview</span>
            </div>
            <a
              href={previewUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs font-mono text-[#707582] hover:text-[#DC2626] hover:underline"
            >
              <span>Open in New Tab</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Document Renderer Container */}
          <div
            className="flex-1 min-h-[500px] rounded-xl overflow-hidden flex flex-col items-center justify-center relative"
            style={{
              background: "#F9FAFB",
              border: "1px solid #DDE0E6",
            }}
          >
            {ext === "pdf" ? (
              <iframe
                src={`${previewUrl}#toolbar=0`}
                className="w-full h-full min-h-[500px] rounded border-0 bg-white"
                title="Corrected PDF Document Preview"
              />
            ) : (
              <div className="p-8 text-center max-w-md space-y-4">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 shadow-sm"
                  style={{
                    background: "rgba(16, 185, 129, 0.1)",
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                  }}
                >
                  <FileText className="w-8 h-8" />
                </div>
                <div>
                  <h4 className="text-base font-bold text-[#17191F]">
                    Corrected .{ext.toUpperCase()} File Generated
                  </h4>
                  <p className="text-xs text-[#707582] mt-1 leading-relaxed">
                    All accepted corrections have been surgically applied to your editable .{ext.toUpperCase()} file.
                    Typography, slide layouts, paragraph styles, and tables are intact.
                  </p>
                </div>
                <PrimaryButton size="md" onClick={handleDownload} leftIcon={<Download className="w-4 h-4" />}>
                  Download .{ext.toUpperCase()} Now
                </PrimaryButton>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Applied Changes Ledger (5 columns) */}
        <div
          className="lg:col-span-5 rounded-2xl p-5 flex flex-col space-y-4"
          style={{
            background: "#FFFFFF",
            border: "1px solid #DDE0E6",
            boxShadow: "0 2px 12px rgba(0,0,0,0.03)",
          }}
        >
          <div className="flex items-center justify-between pb-3 border-b border-[#DDE0E6]">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#707582]">
              <Sparkles className="w-4 h-4 text-[#DC2626]" />
              <span>Applied Corrections ({correctedInfo.applied_findings_count})</span>
            </div>
            <span className="text-[11px] font-mono text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Verified
            </span>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto max-h-[520px] pr-1">
            {correctedInfo.correction_summary?.details && correctedInfo.correction_summary.details.length > 0 ? (
              correctedInfo.correction_summary.details.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl text-xs space-y-2"
                  style={{
                    background: "#F9FAFB",
                    border: "1px solid #DDE0E6",
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[#17191F] truncate max-w-[200px]">
                      {item.title}
                    </span>
                    {item.page_number && (
                      <span className="font-mono text-[10px] text-[#707582] bg-white px-1.5 py-0.5 rounded border border-[#DDE0E6]">
                        pg. {item.page_number}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1 border-t border-[#DDE0E6]/60">
                    <div className="bg-red-50/60 p-2 rounded text-red-900 border border-red-100">
                      <div className="text-[9px] uppercase text-red-500 font-bold mb-0.5">Original</div>
                      <div className="line-through truncate" title={item.original}>
                        {item.original}
                      </div>
                    </div>
                    <div className="bg-emerald-50/60 p-2 rounded text-emerald-950 border border-emerald-100">
                      <div className="text-[9px] uppercase text-emerald-600 font-bold mb-0.5">Corrected</div>
                      <div className="font-bold truncate" title={item.corrected}>
                        {item.corrected}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-xs text-[#707582] font-mono">
                {correctedInfo.applied_findings_count} corrections applied to document body.
              </div>
            )}
          </div>

          {/* Bottom Security Note */}
          <div
            className="p-3 rounded-xl flex items-center gap-2 text-xs font-mono"
            style={{
              background: "#F5F6F8",
              border: "1px solid #DDE0E6",
              color: "#707582",
            }}
          >
            <Lock className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span className="text-[11px]">
              Original source document remains bit-for-bit unchanged.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

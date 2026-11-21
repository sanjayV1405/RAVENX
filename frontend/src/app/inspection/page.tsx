"use client";

import React, { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadProgress } from "@/components/UploadProgress";
import InspectionFindingsViewer, { type Finding } from "@/components/InspectionFindingsViewer";
import { CorrectedDocumentPreview } from "@/components/CorrectedDocumentPreview";
import {
  uploadDocumentWithProgress,
  createInspection,
  getInspectionFindings,
  updateFindingStatus,
  generateCorrectedDocument,
  acceptAllFindings,
  rejectAllFindings,
  type InspectionResponse,
  type CorrectedDocumentInfo,
} from "@/lib/api";
import type { DocumentUploadResponse } from "@/types/extraction";
import {
  UploadCloud,
  FileText,
  AlertCircle,
  Play,
  CheckCircle2,
  Lock,
  Sparkles,
  RefreshCw,
  ScanSearch,
  ChevronRight,
  X,
  FileCheck,
  Check,
  Download,
  Wand2,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";
import { ErrorState } from "@/components/ui/ErrorState";
import { cn } from "@/lib/design-tokens";

interface UploadedFileInfo {
  name: string;
  size: number;
  type: string;
  fileObject: File;
}

type WorkflowStep = "upload" | "review" | "preview";

const steps = [
  { id: "upload", label: "1. Upload Document", icon: UploadCloud },
  { id: "review", label: "2. Review & Approve", icon: ScanSearch },
  { id: "preview", label: "3. Correct & Download", icon: FileCheck },
];

export default function DocumentCorrectionPage() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadedFileInfo | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "processing" | "completed" | "failed">("idle");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [abortController, setAbortController] = useState<{ abort: () => void } | null>(null);

  const [ingestedDoc, setIngestedDoc] = useState<DocumentUploadResponse | null>(null);
  const [workflowStep, setWorkflowStep] = useState<WorkflowStep>("upload");
  const [inspectionLoading, setInspectionLoading] = useState(false);
  const [inspectionResult, setInspectionResult] = useState<InspectionResponse | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [inspectionError, setInspectionError] = useState<string | null>(null);

  // Correction Generation State
  const [generatingCorrection, setGeneratingCorrection] = useState(false);
  const [correctedDocInfo, setCorrectedDocInfo] = useState<CorrectedDocumentInfo | null>(null);
  const [correctionError, setCorrectionError] = useState<string | null>(null);
  const [batchActionLoading, setBatchActionLoading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const validateAndSelectFile = (file: File) => {
    setUploadError(null);
    const validExtensions = ["pdf", "docx", "pptx"];
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !validExtensions.includes(ext)) {
      setUploadError(`Unsupported format (.${ext}). Only PDF, DOCX, and PPTX are supported.`);
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setUploadError("File exceeds 25 MB maximum upload limit.");
      return;
    }
    setSelectedFile({ name: file.name, size: file.size, type: file.type || ext, fileObject: file });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) validateAndSelectFile(e.dataTransfer.files[0]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) validateAndSelectFile(e.target.files[0]);
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) return;
    setUploadStatus("uploading");
    setUploadProgress(0);
    setUploadError(null);
    setInspectionError(null);

    try {
      // 1. Upload document
      const doc = await uploadDocumentWithProgress(
        selectedFile.fileObject,
        (percent) => {
          setUploadProgress(percent);
          if (percent >= 100) setUploadStatus("processing");
        },
        (ctrl) => setAbortController(ctrl)
      );
      setUploadStatus("completed");
      setIngestedDoc(doc);

      // 2. Automatically launch deep inspection analysis
      setInspectionLoading(true);
      const result = await createInspection({
        document_id: doc.id,
      });
      setInspectionResult(result);

      // 3. Fetch detected findings
      const fetchedFindings = await getInspectionFindings(result.id);
      const initialFindings = fetchedFindings.length ? fetchedFindings : (result.findings ?? []);
      setFindings(initialFindings);

      // Transition straight into review
      setWorkflowStep("review");
    } catch (err: unknown) {
      setUploadStatus("failed");
      setUploadError((err as Error).message || "Failed to process and analyze document.");
    } finally {
      setInspectionLoading(false);
    }
  };

  const handleCancelUpload = () => {
    if (abortController) abortController.abort();
    setUploadStatus("idle");
    setUploadProgress(0);
  };

  const handleReviewUpdate = useCallback(async (findingId: string, status: string) => {
    await updateFindingStatus(findingId, status);
    setFindings((prev) =>
      prev.map((f) => (f.id === findingId ? { ...f, user_status: status as any } : f))
    );
  }, []);

  const handleAcceptAll = async () => {
    if (!inspectionResult) return;
    setBatchActionLoading(true);
    try {
      await acceptAllFindings(inspectionResult.id);
      setFindings((prev) => prev.map((f) => ({ ...f, user_status: "accepted" })));
    } catch (err) {
      console.error("Batch accept failed:", err);
    } finally {
      setBatchActionLoading(false);
    }
  };

  const handleRejectAll = async () => {
    if (!inspectionResult) return;
    setBatchActionLoading(true);
    try {
      await rejectAllFindings(inspectionResult.id);
      setFindings((prev) => prev.map((f) => ({ ...f, user_status: "rejected" })));
    } catch (err) {
      console.error("Batch reject failed:", err);
    } finally {
      setBatchActionLoading(false);
    }
  };

  const handleGenerateCorrection = async () => {
    if (!inspectionResult) return;
    setGeneratingCorrection(true);
    setCorrectionError(null);

    try {
      // Check if any finding is accepted; if none are yet, accept all high-severity/medium findings
      const acceptedCount = findings.filter((f) => f.user_status === "accepted").length;
      if (acceptedCount === 0 && findings.length > 0) {
        // Automatically accept pending findings for convenience
        await acceptAllFindings(inspectionResult.id);
        setFindings((prev) => prev.map((f) => ({ ...f, user_status: "accepted" })));
      }

      // Generate the corrected document
      const corrInfo = await generateCorrectedDocument(inspectionResult.id);
      setCorrectedDocInfo(corrInfo);
      setWorkflowStep("preview");
    } catch (err: unknown) {
      setCorrectionError((err as Error).message || "Document correction failed.");
    } finally {
      setGeneratingCorrection(false);
    }
  };

  const handleReset = () => {
    setIngestedDoc(null);
    setSelectedFile(null);
    setUploadStatus("idle");
    setUploadProgress(0);
    setUploadError(null);
    setWorkflowStep("upload");
    setInspectionResult(null);
    setFindings([]);
    setInspectionError(null);
    setCorrectedDocInfo(null);
    setCorrectionError(null);
  };

  const stepIndex = steps.findIndex((s) => s.id === workflowStep);
  const acceptedCount = findings.filter((f) => f.user_status === "accepted").length;
  const rejectedCount = findings.filter((f) => f.user_status === "rejected").length;
  const pendingCount = findings.length - acceptedCount - rejectedCount;

  return (
    <div className="space-y-6 select-none">
      {/* Page Header */}
      <PageHeader
        badge="Document Correction Engine"
        title="Automated Document"
        highlightedTitle="Correction"
        description="Upload documents to detect defects, review suggested fixes side-by-side, and generate verified, layout-preserved corrected files."
        action={
          ingestedDoc && (
            <SecondaryButton
              size="sm"
              onClick={handleReset}
              leftIcon={<UploadCloud className="w-4 h-4 text-[#DC2626]" />}
            >
              Correct New Document
            </SecondaryButton>
          )
        }
      />

      {/* Step Indicator Bar */}
      <div className="p-3 rounded-2xl aurora-glass-card flex items-center justify-between overflow-x-auto">
        <div className="flex items-center gap-2 min-w-max">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isDone = idx < stepIndex;
            const isCurrent = idx === stepIndex;

            return (
              <React.Fragment key={step.id}>
                <div
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200",
                    isCurrent
                      ? "aurora-nav-active"
                      : isDone
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200/60"
                      : "bg-white/60 text-[#687080] border border-[#DDE0E6]/80"
                  )}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : (
                    <Icon className="w-4 h-4 shrink-0" />
                  )}
                  <span>{step.label}</span>
                </div>
                {idx < steps.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-[#CBD2DE] shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {workflowStep === "review" && (
          <div className="hidden sm:flex items-center gap-2">
            <span className="text-xs font-mono text-[#707582]">
              {acceptedCount} accepted • {findings.length} total
            </span>
          </div>
        )}
      </div>

      {/* STEP 1: Upload */}
      <AnimatePresence mode="wait">
        {workflowStep === "upload" && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-12 gap-6"
          >
            {/* Upload Dropzone Card */}
            <div className="lg:col-span-8 aurora-glass-card p-6 lg:p-8 space-y-6">
              <div>
                <h3 className="text-base font-bold text-[#1A1D26]">Upload Document to Correct</h3>
                <p className="text-xs text-[#687080] mt-0.5">
                  Select a PDF, DOCX, or PPTX file. Defects and inconsistencies will be detected automatically.
                </p>
              </div>

              {/* Drop Zone */}
              <div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 relative group",
                  dragActive
                    ? "border-[#DC2626] bg-red-50/30 shadow-inner"
                    : "border-[#DDE0E6] bg-white/40 hover:bg-white/80 hover:border-[#DC2626]/50"
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.pptx"
                  onChange={handleFileChange}
                  className="hidden"
                />

                <div className="w-14 h-14 rounded-2xl bg-red-50/80 border border-red-100 flex items-center justify-center mx-auto mb-4 text-[#DC2626] group-hover:scale-105 transition-transform shadow-2xs">
                  <UploadCloud className="w-7 h-7" />
                </div>

                <div className="text-sm md:text-base font-bold text-[#1A1D26] mb-1">
                  Drag and drop your document here
                </div>
                <div className="text-xs text-[#687080] mb-4">
                  or click to select from your computer
                </div>

                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[11px] font-mono bg-white/80 border border-[#DDE0E6] text-[#687080] shadow-2xs">
                  <span className="font-bold text-[#1A1D26]">PDF</span>
                  <span>•</span>
                  <span className="font-bold text-[#1A1D26]">DOCX</span>
                  <span>•</span>
                  <span className="font-bold text-[#1A1D26]">PPTX</span>
                  <span className="text-[#9CA3AF]">(Up to 25 MB)</span>
                </div>
              </div>

              {uploadStatus !== "idle" && (
                <UploadProgress
                  progress={uploadProgress}
                  status={uploadStatus}
                  fileName={selectedFile?.name || ""}
                  fileSize={selectedFile?.size || 0}
                  errorMessage={uploadError}
                  onCancel={handleCancelUpload}
                />
              )}

              {selectedFile && uploadStatus === "idle" && (
                <div className="flex items-center justify-between p-4 rounded-xl aurora-glass-subtle border border-[#DDE0E6]">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="px-2.5 py-1.5 rounded-lg font-mono uppercase text-xs font-bold bg-red-50 border border-red-100 text-[#DC2626]">
                      .{selectedFile.name.split(".").pop()}
                    </div>
                    <div className="overflow-hidden">
                      <div className="text-sm font-semibold truncate max-w-xs text-[#1A1D26]">
                        {selectedFile.name}
                      </div>
                      <div className="text-xs font-mono text-[#687080]">
                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="p-1.5 rounded-lg text-[#687080] hover:text-[#1A1D26] hover:bg-black/5 transition-colors cursor-pointer"
                      aria-label="Remove selected file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <PrimaryButton
                      size="md"
                      onClick={handleUploadAndAnalyze}
                      loading={inspectionLoading}
                      leftIcon={<Wand2 className="w-4 h-4" />}
                    >
                      Analyze &amp; Detect Defects
                    </PrimaryButton>
                  </div>
                </div>
              )}

              {uploadError && uploadStatus === "idle" && (
                <ErrorState title="Upload Notice" message={uploadError} />
              )}
            </div>

            {/* Workflow Promise Sidebar (4 columns) */}
            <div className="lg:col-span-4 aurora-glass-card p-6 lg:p-7 space-y-5">
              <div>
                <h3 className="text-sm font-bold text-[#1A1D26] flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#DC2626]" />
                  The RAVENX Promise
                </h3>
                <p className="text-xs text-[#687080] mt-1 leading-relaxed">
                  Fast, surgical document correction that preserves original layout, fonts, and images.
                </p>
              </div>

              <div className="space-y-3 pt-2">
                {[
                  { title: "1. Detect Mistakes", desc: "Spelling, grammar, table arithmetic, repeated words, and dates." },
                  { title: "2. Human-in-the-Loop Review", desc: "Approve or reject fixes side-by-side before anything changes." },
                  { title: "3. Surgical Document Generation", desc: "Original file is never altered. Generates clean output file." },
                  { title: "4. Full Format Preservation", desc: "PDF coordinates, Word styles, and PowerPoint shapes stay intact." },
                ].map((item, i) => (
                  <div key={i} className="p-3 rounded-xl bg-white/70 border border-[#DDE0E6] text-xs">
                    <div className="font-semibold text-[#1A1D26] mb-0.5">{item.title}</div>
                    <p className="text-[11px] text-[#707582] leading-relaxed">{item.desc}</p>
                  </div>
                ))}
              </div>

              <div className="pt-3 flex items-center justify-between text-[11px] font-mono border-t border-[#DDE0E6] text-[#9CA3AF]">
                <span className="flex items-center gap-1">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  Original File Immutable
                </span>
                <span>SHA-256 Verified</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* STEP 2: Review Findings & Generate Corrections */}
        {workflowStep === "review" && (
          <motion.div
            key="review"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Quick Actions & Decision Bar */}
            <div
              className="p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4"
              style={{
                background: "#FFFFFF",
                border: "1px solid #DDE0E6",
                boxShadow: "0 2px 10px rgba(0,0,0,0.03)",
              }}
            >
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-red-50 text-[#DC2626] border border-red-100">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#17191F]">
                    {ingestedDoc?.filename}
                  </h3>
                  <div className="flex items-center gap-2 text-xs font-mono text-[#707582] mt-0.5">
                    <span>{findings.length} detected issues</span>
                    <span>•</span>
                    <span className="text-emerald-700 font-semibold">{acceptedCount} accepted for correction</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2.5">
                <button
                  onClick={handleAcceptAll}
                  disabled={batchActionLoading}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100 transition-colors cursor-pointer"
                >
                  Accept All ({findings.length})
                </button>
                <button
                  onClick={handleRejectAll}
                  disabled={batchActionLoading}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  Reject All
                </button>
                <PrimaryButton
                  size="md"
                  onClick={handleGenerateCorrection}
                  loading={generatingCorrection}
                  leftIcon={<Sparkles className="w-4 h-4" />}
                >
                  Apply Corrections &amp; Generate File
                </PrimaryButton>
              </div>
            </div>

            {correctionError && (
              <ErrorState title="Correction Engine Notice" message={correctionError} />
            )}

            {/* Findings Viewer */}
            <div className="aurora-glass-card p-6">
              <InspectionFindingsViewer
                inspectionId={inspectionResult?.id || ""}
                findings={findings}
                isLoading={inspectionLoading}
                onReviewUpdate={handleReviewUpdate}
                documentName={ingestedDoc?.filename}
              />
            </div>
          </motion.div>
        )}

        {/* STEP 3: Preview & Download Corrected Document */}
        {workflowStep === "preview" && correctedDocInfo && ingestedDoc && (
          <motion.div
            key="preview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <CorrectedDocumentPreview
              inspectionId={inspectionResult?.id || ""}
              documentId={ingestedDoc.id}
              originalFilename={ingestedDoc.filename}
              fileExtension={ingestedDoc.file_extension}
              correctedInfo={correctedDocInfo}
              onReset={handleReset}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

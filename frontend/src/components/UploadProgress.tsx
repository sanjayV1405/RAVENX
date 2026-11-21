"use client";

import React from "react";
import { UploadCloud, CheckCircle2, AlertCircle, X, Loader2 } from "lucide-react";

interface UploadProgressProps {
  progress: number;
  status: "idle" | "uploading" | "processing" | "completed" | "failed";
  fileName: string;
  fileSize: number;
  errorMessage?: string | null;
  onCancel?: () => void;
}

export function UploadProgress({
  progress,
  status,
  fileName,
  fileSize,
  errorMessage,
  onCancel,
}: UploadProgressProps) {
  if (status === "idle") return null;

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div
      className="p-4 rounded-xl space-y-3"
      style={{
        background: "#F5F6F8",
        border: "1px solid #DDE0E6",
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{
              background: "#FFFFFF",
              border: "1px solid #DDE0E6",
            }}
          >
            {status === "uploading" && <UploadCloud className="w-4 h-4 text-[#DC2626] animate-pulse" />}
            {status === "processing" && <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />}
            {status === "completed" && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
            {status === "failed" && <AlertCircle className="w-4 h-4 text-red-600" />}
          </div>
          <div className="overflow-hidden">
            <div className="text-sm font-semibold truncate max-w-[240px]" style={{ color: "#17191F" }}>
              {fileName}
            </div>
            <div className="text-xs font-mono" style={{ color: "#707582" }}>
              {formatFileSize(fileSize)} •{" "}
              {status === "uploading" && `Uploading (${progress}%)`}
              {status === "processing" && "Extracting text & geometry..."}
              {status === "completed" && "Ingestion complete"}
              {status === "failed" && "Upload failed"}
            </div>
          </div>
        </div>

        {status === "uploading" && onCancel && (
          <button
            onClick={onCancel}
            className="p-1.5 rounded-md hover:bg-gray-200 transition-colors"
            style={{ color: "#707582" }}
            title="Cancel Upload"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div
        className="w-full h-2 rounded-full overflow-hidden"
        style={{ background: "#DDE0E6" }}
      >
        <div
          className={`h-full transition-all duration-200 ${
            status === "completed"
              ? "bg-emerald-500"
              : status === "failed"
              ? "bg-red-600"
              : "bg-gradient-to-r from-red-600 to-[#DC2626]"
          }`}
          style={{ width: `${status === "completed" ? 100 : progress}%` }}
        />
      </div>

      {/* Error message */}
      {status === "failed" && errorMessage && (
        <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}

export default UploadProgress;

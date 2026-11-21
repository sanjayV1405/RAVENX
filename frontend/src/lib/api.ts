// RAVENX AI Phase 3 — API Client Helper

import type { ExtractionJob, ExtractedPageSummary, ExtractedPageDetail, DocumentUploadResponse, Document } from "@/types/extraction";
import type { Finding } from "@/components/InspectionFindingsViewer";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new Error(
        (errorBody as { detail?: string }).detail ||
          `API error ${res.status}: ${res.statusText}`
      );
    }
    return res.json() as Promise<T>;
  } catch (err: any) {
    if (err.name === "TypeError" && err.message?.toLowerCase().includes("fetch")) {
      throw new Error(
        `Backend connection offline: Unable to reach RAVENX AI server at ${API_BASE}. Please ensure the backend is running on port 8000.`
      );
    }
    throw err;
  }
}

export async function checkBackendHealth(): Promise<{ status: string; latencyMs: number; ok: boolean }> {
  const start = performance.now();
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    const latencyMs = Math.max(4, Math.round(performance.now() - start));
    if (res.ok) {
      const data = await res.json();
      return { status: data.status || "healthy", latencyMs, ok: true };
    }
    return { status: "degraded", latencyMs, ok: false };
  } catch {
    return { status: "offline", latencyMs: 0, ok: false };
  }
}

export async function uploadDocumentWithProgress(
  file: File,
  onProgress: (percent: number) => void,
  setAbortController?: (controller: { abort: () => void }) => void
): Promise<DocumentUploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);

    if (setAbortController) {
      setAbortController({
        abort: () => xhr.abort(),
      });
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText) as DocumentUploadResponse;
          resolve(response);
        } catch (e) {
          reject(new Error("Invalid JSON response from server."));
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `Upload failed with status ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network connection error during document upload."));
    };

    xhr.onabort = () => {
      reject(new Error("Upload cancelled by user."));
    };

    xhr.open("POST", `${API_BASE}/documents/upload`);
    xhr.send(formData);
  });
}

export async function getExtractionStatus(docId: string): Promise<ExtractionJob> {
  return apiFetch<ExtractionJob>(`/documents/${docId}/extraction`);
}

export async function getDocumentPages(docId: string): Promise<ExtractedPageSummary[]> {
  return apiFetch<ExtractedPageSummary[]>(`/documents/${docId}/pages`);
}

export async function getPageDetail(
  docId: string,
  pageNum: number
): Promise<ExtractedPageDetail> {
  return apiFetch<ExtractedPageDetail>(`/documents/${docId}/pages/${pageNum}`);
}

export async function listDocuments(skip: number = 0, limit: number = 50): Promise<Document[]> {
  return apiFetch<Document[]>(`/documents?skip=${skip}&limit=${limit}`);
}

// ─── Inspection API (Phase 3) ─────────────────────────────────────────────────

export interface InspectionCreatePayload {
  document_id: string;
  ai_provider?: string;
  user_guidelines?: string;
}

export interface InspectionResponse {
  id: string;
  document_id: string;
  status: string;
  current_stage: string | null;
  progress_percentage: number;
  ai_provider: string;
  summary: Record<string, number> | null;
  error_message: string | null;
  findings: Finding[];
  created_at: string;
  updated_at: string;
}

export async function createInspection(payload: InspectionCreatePayload): Promise<InspectionResponse> {
  return apiFetch<InspectionResponse>("/inspections", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getInspection(inspectionId: string): Promise<InspectionResponse> {
  return apiFetch<InspectionResponse>(`/inspections/${inspectionId}`);
}

export async function listInspections(documentId?: string): Promise<InspectionResponse[]> {
  const qs = documentId ? `?document_id=${encodeURIComponent(documentId)}` : "";
  return apiFetch<InspectionResponse[]>(`/inspections${qs}`);
}

export async function getInspectionFindings(
  inspectionId: string,
  params?: { category?: string; severity?: string; user_status?: string; page_number?: number }
): Promise<Finding[]> {
  const qs = new URLSearchParams();
  if (params?.category) qs.set("category", params.category);
  if (params?.severity) qs.set("severity", params.severity);
  if (params?.user_status) qs.set("user_status", params.user_status);
  if (params?.page_number != null) qs.set("page_number", String(params.page_number));
  const q = qs.toString();
  return apiFetch<Finding[]>(`/inspections/${inspectionId}/findings${q ? `?${q}` : ""}`);
}

export async function updateFindingStatus(
  findingId: string,
  user_status: string
): Promise<Finding> {
  return apiFetch<Finding>(`/inspections/findings/${findingId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ user_status }),
  });
}

export function getAuditReportPdfUrl(
  inspectionId: string,
  includeExcerpts: boolean = true,
  includeAlignment: boolean = true
): string {
  const qs = new URLSearchParams({
    include_excerpts: String(includeExcerpts),
    include_alignment: String(includeAlignment),
  });
  return `${API_BASE}/inspections/${inspectionId}/report.pdf?${qs.toString()}`;
}

// ─── Real Document Correction API (Phase 6) ───────────────────────────────────

export interface CorrectedDocumentInfo {
  id: string;
  inspection_id: string;
  document_id: string;
  original_filename: string;
  corrected_filename: string;
  file_extension: string;
  file_size_bytes: number;
  checksum?: string;
  applied_findings_count: number;
  correction_summary?: {
    applied_count: number;
    total_accepted: number;
    details: Array<{
      finding_id: string;
      title: string;
      original: string;
      corrected: string;
      status: string;
      page_number?: number;
    }>;
  };
  download_url?: string;
  created_at: string;
  updated_at: string;
}

export async function generateCorrectedDocument(
  inspectionId: string,
  selectedFindingIds?: string[]
): Promise<CorrectedDocumentInfo> {
  return apiFetch<CorrectedDocumentInfo>(`/inspections/${inspectionId}/correct`, {
    method: "POST",
    body: JSON.stringify({ selected_finding_ids: selectedFindingIds }),
  });
}

export async function getCorrectedDocumentInfo(
  inspectionId: string
): Promise<CorrectedDocumentInfo> {
  return apiFetch<CorrectedDocumentInfo>(`/inspections/${inspectionId}/corrected`);
}

export function getCorrectedDownloadUrl(inspectionId: string): string {
  return `${API_BASE}/inspections/${inspectionId}/corrected/download`;
}

export function getCorrectedPreviewUrl(inspectionId: string): string {
  return `${API_BASE}/inspections/${inspectionId}/corrected/preview`;
}

export async function acceptAllFindings(
  inspectionId: string
): Promise<{ message: string; accepted_count: number }> {
  return apiFetch<{ message: string; accepted_count: number }>(`/inspections/${inspectionId}/accept-all`, {
    method: "POST",
  });
}

export async function rejectAllFindings(
  inspectionId: string
): Promise<{ message: string; rejected_count: number }> {
  return apiFetch<{ message: string; rejected_count: number }>(`/inspections/${inspectionId}/reject-all`, {
    method: "POST",
  });
}

// ─── Requirements Alignment API (Phase 4) ─────────────────────────────────────

export interface RequirementItem {
  id?: string;
  item_text: string;
  category?: string;
  importance?: string;
}

export interface RequirementSet {
  id: string;
  title: string;
  description?: string;
  source_type: string;
  items: RequirementItem[];
  created_at: string;
}

export interface RequirementResult {
  id: string;
  requirement_item_id?: string;
  requirement_text: string;
  status: "MET" | "PARTIALLY MET" | "MISSING" | "AMBIGUOUS" | "NOT VERIFIABLE";
  supporting_evidence?: string;
  source_document_name?: string;
  page_number?: number;
  bbox?: number[];
  explanation: string;
  confidence: number;
}

export interface RequirementAssessment {
  id: string;
  requirement_set_id: string;
  target_document_id: string;
  inspection_id?: string;
  status: string;
  summary?: {
    MET: number;
    PARTIALLY_MET: number;
    MISSING: number;
    AMBIGUOUS: number;
    NOT_VERIFIABLE: number;
    total: number;
  };
  results: RequirementResult[];
  created_at: string;
}

export async function createRequirementSet(payload: {
  title: string;
  description?: string;
  source_type?: string;
  items: { item_text: string; category?: string; importance?: string }[];
}): Promise<RequirementSet> {
  return apiFetch<RequirementSet>("/requirements/sets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listRequirementSets(): Promise<RequirementSet[]> {
  return apiFetch<RequirementSet[]>("/requirements/sets");
}

export async function assessRequirements(payload: {
  target_document_id: string;
  requirement_set_id?: string;
  manual_requirements?: string[];
  inspection_id?: string;
}): Promise<RequirementAssessment> {
  return apiFetch<RequirementAssessment>("/requirements/assess", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getRequirementAssessment(assessmentId: string): Promise<RequirementAssessment> {
  return apiFetch<RequirementAssessment>(`/requirements/assessments/${assessmentId}`);
}

// ─── Document Comparison API (Phase 4) ────────────────────────────────────────

export interface ComparisonDifference {
  id: string;
  comparison_id: string;
  category: "content" | "structural" | "formatting";
  diff_type: "added" | "removed" | "modified" | "potentially_inconsistent" | "formatting_only";
  title: string;
  base_page?: number;
  target_page?: number;
  base_content?: string;
  target_content?: string;
  explanation: string;
  significance: "high" | "medium" | "low";
}

export interface DocumentComparison {
  id: string;
  base_document_id: string;
  target_document_id: string;
  status: string;
  summary?: {
    added: number;
    removed: number;
    modified: number;
    potentially_inconsistent: number;
    formatting_only: number;
    total: number;
  };
  differences: ComparisonDifference[];
  created_at: string;
}

export async function compareDocuments(payload: {
  base_document_id: string;
  target_document_id: string;
}): Promise<DocumentComparison> {
  return apiFetch<DocumentComparison>("/comparisons", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getComparison(comparisonId: string): Promise<DocumentComparison> {
  return apiFetch<DocumentComparison>(`/comparisons/${comparisonId}`);
}

export async function listComparisons(): Promise<DocumentComparison[]> {
  return apiFetch<DocumentComparison[]>("/comparisons");
}

// ─── Audit History API (Phase 4) ──────────────────────────────────────────────

export interface AuditLogItem {
  id: string;
  entity_type: string;
  entity_id: string;
  event_type: string;
  actor: string;
  summary: string;
  details?: Record<string, any>;
  event_timestamp: string;
  created_at: string;
}

export async function getAuditHistory(params?: {
  entity_type?: string;
  entity_id?: string;
  limit?: number;
}): Promise<AuditLogItem[]> {
  const qs = new URLSearchParams();
  if (params?.entity_type) qs.set("entity_type", params.entity_type);
  if (params?.entity_id) qs.set("entity_id", params.entity_id);
  if (params?.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return apiFetch<AuditLogItem[]>(`/audit/history${q ? `?${q}` : ""}`);
}

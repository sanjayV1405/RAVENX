// RAVENX AI Phase 2 — Extraction Type Definitions

export interface Document {
  id: string;
  filename: string;
  file_extension: string;
  file_size_bytes: number;
  status: string;
  checksum?: string;
  storage_path?: string;
  page_count?: number | null;
  is_duplicate?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DocumentUploadResponse extends Document {
  is_duplicate: boolean;
}

export type ExtractionStatus = "queued" | "processing" | "completed" | "failed";
export type ExtractorType = "pdf" | "docx" | "pptx" | "ocr";

export interface ExtractionJob {
  id: string;
  document_id: string;
  status: ExtractionStatus;
  extractor_type: ExtractorType;
  page_count: number | null;
  error_message: string | null;
  extraction_metadata: Record<string, any> | null;
  created_at: string;
  updated_at?: string;
}

export interface ExtractedPageSummary {
  id?: string;
  extraction_job_id?: string;
  page_number: number;
  word_count: number;
  extraction_method: "native" | "ocr" | "ocr_pending";
  has_tables: boolean;
  needs_ocr?: boolean;
  ocr_confidence?: number | null;
  preview_snippet?: string | null;
}

export interface ExtractedPageDetail {
  id?: string;
  extraction_job_id?: string;
  page_number: number;
  raw_text: string;
  structured_data: {
    dimensions?: { width: number; height: number };
    word_count?: number;
    fonts?: string[];
    headings?: Array<{ text: string; level?: number; font_size?: number; font_name?: string; bbox?: number[] }>;
    blocks_count?: number;
    blocks?: Array<{
      bbox: number[];
      text: string;
      lines?: Array<{
        bbox: number[];
        spans: Array<{
          text: string;
          font: string;
          size: number;
          flags?: number;
          color?: number;
          bbox: number[];
        }>;
      }>;
    }>;
    tables?: Array<{
      table_index?: number;
      name?: string;
      bbox?: number[];
      row_count: number;
      col_count: number;
      rows: string[][];
    }>;
    paragraphs?: Array<{
      paragraph_index: number;
      text: string;
      style: string;
      is_heading: boolean;
      heading_level: number;
      runs: Array<{
        text: string;
        font_name?: string;
        font_size_pt?: number;
        bold?: boolean;
        italic?: boolean;
        underline?: boolean;
      }>;
    }>;
    shapes?: Array<{
      type: string;
      name: string;
      bbox: number[];
      text: string;
      paragraphs?: any[];
    }>;
    sections?: any[];
    [key: string]: any;
  } | null;
  word_count: number;
  has_tables: boolean;
  extraction_method: "native" | "ocr" | "ocr_pending";
  needs_ocr?: boolean;
  ocr_confidence?: number | null;
  created_at?: string;
}

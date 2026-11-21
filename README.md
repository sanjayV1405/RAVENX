# RAVENX AI

> **Tagline:** *Intelligence That Sees What Others Miss.*

RAVENX AI is an advanced document quality inspection platform designed to detect mistakes that ordinary spell-checkers and general-purpose LLMs overlook. It inspects micro-typography, punctuation, structural tables, layout bounds, cross-field entity consistency, and document requirements with cryptographic evidence and an absolute zero auto-edit guarantee.

---

## 🏛️ Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │          RAVENX AI Web Client          │
                      │  Next.js 15 App Router + Tailwind CSS  │
                      └──────────────────┬─────────────────────┘
                                         │ HTTP / REST (XHR Upload with Progress)
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          FastAPI Backend (v1)          │
                      │      Pydantic Settings + SQLAlchemy    │
                      └──────────────────┬─────────────────────┘
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
┌─────────────────────────────────┐                     ┌──────────────────────────────────┐
│    Modular 8-Stage Pipeline     │                     │     Storage & Data Persistence   │
├─────────────────────────────────┤                     ├──────────────────────────────────┤
│ 1. Document Ingestion & Hash    │                     │ • Supabase PostgreSQL (or SQLite)│
│ 2. Text & Structure Extraction  │                     │ • Supabase Storage (Immutable)   │
│    ├── PyMuPDF (PDF vectors)    │                     │ • SHA-256 Tamper Verification    │
│    ├── python-docx (Word)       │                     │ • Extraction Jobs & Pages Rel DB │
│    ├── python-pptx (PowerPoint) │                     └──────────────────────────────────┘
│    └── PaddleOCR (Scanned OCR)  │                                        ▲
│ 3. Grammar & Typo Inspection    │                                        │
│ 4. Visual Layout Inspection     │                                        │
│ 5. Contextual AI Reasoning      │                                        │
│ 6. Cross-Field Entity Check     │                                        │
│ 7. Validation & Deduplication   │                                        │
│ 8. Audit Dossier & Reporting    │ ───────────────────────────────────────┘
└─────────────────────────────────┘
```

---

## 🚀 Key Features Built in Phase 2: Real Document Ingestion & Intelligent Extraction

1. **Complete Ingestion & Upload Workflow**
   - **Interactive Drag-and-Drop Dropzone**: Supports `.pdf`, `.docx`, and `.pptx` up to 25 MB with strict client and server validation.
   - **Real-Time Progress Tracking**: Uploads use `XMLHttpRequest` with live percentage bars, animated states, and user-initiated upload cancellation.
   - **SHA-256 Cryptographic Deduplication**: Calculates checksums instantly. Re-uploading an identical document detects duplicates, protects disk storage, and links directly to existing extracted data.
   - **Filename Sanitization**: Sanitizes input strings against path-traversal attacks.

2. **Native Structural Document Extractors**
   - **PDF Engine (`PyMuPDF / fitz`)**: Extracts text blocks, visual coordinates (`[x0, y0, x1, y1]`), font names, font sizes, heading heuristics, page dimensions, word counts, and tabular geometries via `find_tables()`.
   - **DOCX Engine (`python-docx`)**: Extracts paragraph hierarchies, heading levels (`H1` to `H6`), runs with character styling (bold, italic, underline), section layouts, and embedded table cell grids.
   - **PPTX Engine (`python-pptx`)**: Extracts slide numbers, slide titles, text frames, shape positions/dimensions, font properties, and presentation tables.
   - **Scanned PDF Support (`PaddleOCR Engine`)**: Automatically flags candidate pages with sparse or missing text (`needs_ocr: true`) for OCR without falsely claiming OCR completed before installation.

3. **Split-Screen Extraction Results Viewer**
   - **Split-Screen Experience**:
     - **Left Panel (Document Preview)**: Embedded PDF preview via secure raw stream endpoint (`/api/v1/documents/{id}/raw`), visual canvas card for DOCX/PPTX, and page jump controls.
     - **Right Panel (Intelligent Inspector)**:
       - **Tab 1 ("Extracted Text")**: Complete page text, word count badge, copy-to-clipboard, text filtering, and scanned-page OCR badges.
       - **Tab 2 ("Page Structure & Geometry")**: Heading hierarchy tree, interactive tabular grids with row/column data, and text blocks with exact bounding coordinates.
       - **Tab 3 ("Document Dossier")**: Provenance metadata, extractor engine type, total pages, and cryptographic SHA-256 integrity hash.

4. **Normalized Relational Database Architecture**
   - **`ExtractionJob`**: Tracks execution state (`queued`, `processing`, `completed`, `failed`), extractor type, page count, error messages, and structured metadata.
   - **`ExtractedPage`**: Stores page-by-page raw text, structured block/table/font JSON, word count, table flags, and OCR confidence indicators.

---

## 📂 Project Directory Structure

```
RAVENX AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── documents.py         # Document upload, raw stream, and metadata routes
│   │   │       │   ├── extraction.py        # Extraction status, page list, and page detail routes
│   │   │       │   ├── health.py            # Health check endpoint
│   │   │       │   ├── inspections.py       # Inspection & finding review routes
│   │   │       │   └── settings.py          # Platform settings endpoint
│   │   │       └── api.py                   # Aggregator router
│   │   ├── core/
│   │   │   ├── config.py                    # Pydantic Settings
│   │   │   ├── exceptions.py                # Centralized domain exceptions
│   │   │   └── logging.py                   # Structured logger
│   │   ├── database/
│   │   │   ├── session.py                   # SQLAlchemy engine & session factory
│   │   │   └── supabase.py                  # Supabase storage & offline adapter
│   │   ├── document_processing/
│   │   │   ├── extractors/
│   │   │   │   ├── docx_extractor.py        # python-docx parser (headings, tables, runs)
│   │   │   │   ├── ocr_extractor.py         # PaddleOCR detection adapter
│   │   │   │   ├── pdf_extractor.py         # PyMuPDF parser (bboxes, fonts, tables)
│   │   │   │   └── pptx_extractor.py        # python-pptx parser (slides, shapes, tables)
│   │   │   ├── stages/
│   │   │   │   ├── extraction.py            # Stage 2: Real structural extraction & persistence
│   │   │   │   ├── ingestion.py             # Stage 1: Document ingestion & hash
│   │   │   │   ├── consistency.py           # Stage 6: Cross-field consistency
│   │   │   │   ├── contextual_ai.py         # Stage 5: Contextual AI reasoning
│   │   │   │   ├── deduplication.py         # Stage 7: Deduplication & scoring
│   │   │   │   ├── grammar.py               # Stage 3: Typographical linting
│   │   │   │   ├── reporting.py             # Stage 8: Audit dossier compilation
│   │   │   │   └── visual_layout.py         # Stage 4: Layout & geometry bounds
│   │   │   └── pipeline.py                  # Modular 8-stage orchestrator
│   │   ├── models/
│   │   │   ├── document.py                  # Document model with extraction jobs relationship
│   │   │   ├── extraction_job.py            # Extraction job model
│   │   │   ├── extracted_page.py            # Granular page structure model
│   │   │   ├── finding.py                   # Evidence-backed Finding model
│   │   │   └── inspection.py                # Inspection run model
│   │   ├── providers/                       # AI Reasoners (DeepSeek, Gemini)
│   │   ├── schemas/
│   │   │   ├── extraction.py                # Pydantic extraction schemas
│   │   │   ├── document.py                  # Document schemas
│   │   │   └── inspection.py                # Inspection schemas
│   │   ├── services/
│   │   │   ├── document_service.py          # Ingestion, local disk caching & retrieval
│   │   │   └── inspection_service.py        # Pipeline orchestrator service
│   │   ├── utils/
│   │   │   └── file_validators.py           # MIME, extension & SHA-256 utilities
│   │   └── main.py                          # FastAPI main entrypoint
│   ├── tests/
│   │   ├── fixtures/                        # Synthetic test documents
│   │   ├── create_fixtures.py               # Synthetic document generator
│   │   ├── test_extraction.py               # 16-test automated extraction test suite
│   │   └── test_pipeline.py                 # Smoke pipeline test
│   ├── uploads/                             # Local immutable storage cache
│   ├── requirements.txt                     # Backend dependencies
│   ├── .env.example                         # Environment template
│   └── .env                                 # Active development configuration
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/page.tsx           # Dashboard view
│   │   │   ├── inspection/page.tsx          # Real Ingestion & Split-Screen Inspection view
│   │   │   ├── settings/page.tsx            # Settings & profile view
│   │   │   ├── globals.css                  # Custom theme & styling
│   │   │   ├── layout.tsx                   # Root HTML layout & fonts
│   │   │   └── page.tsx                     # Landing page
│   │   ├── components/
│   │   │   ├── ExtractionViewer.tsx         # Split-screen Document & Structure Inspector
│   │   │   ├── UploadProgress.tsx           # XHR live progress bar with Cancel button
│   │   │   ├── BrandLogo.tsx                # Geometric Raven Emblem
│   │   │   ├── Footer.tsx                   # Enterprise footer
│   │   │   └── Navbar.tsx                   # App navigation bar
│   │   ├── lib/
│   │   │   ├── api.ts                       # Typed XHR and fetch client
│   │   │   └── utils.ts                     # Tailwind class merge helper
│   │   └── types/
│   │       └── extraction.ts                # TypeScript interfaces for extraction & pages
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.ts
├── .gitignore
└── README.md
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.10 or higher
- **npm**: v9+ or higher

---

### 1. Backend Setup

1. Open a terminal in the `backend` directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI backend server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   - **Backend Root**: [http://localhost:8000](http://localhost:8000)
   - **Interactive Swagger Documentation**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

### 2. Frontend Setup

1. Open another terminal in the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if needed):
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Or run the production build:
   ```bash
   npm run build
   npm run start
   ```

   - **Web Application**: [http://localhost:3000](http://localhost:3000)
   - **Inspection & Extraction Viewer**: [http://localhost:3000/inspection](http://localhost:3000/inspection)
   - **Dashboard**: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
   - **Settings**: [http://localhost:3000/settings](http://localhost:3000/settings)

---

## 🔬 Key Features Built in Phase 3: Advanced Intelligent Document Inspection Engine

1. **Module A — Micro-Typographical Intelligence (`MicroTypographyInspector`)**
   - **Concatenated place names & postal codes**: Detects patterns like `Tirupur641666` or `Coimbatore641001` with domain allowlisting (e.g. `SHA256`, `IPv4` protected).
   - **Accidental word concatenations**: Identifies `andthe`, `ofthe`, `withregard`, `inaccordance`, etc.
   - **Consecutive duplicate words**: Flags `the the`, `is is`, `in in`.
   - **Punctuation defects**: Identifies repeated punctuation (`,,`, `..`), spaces before punctuation (`word ,`), and multi-space gaps.
   - **High-frequency typos**: Deterministic detection for common misspellings (`recieve`, `definately`, `seperate`, etc.).
   - **Suspicious digit substitutions & leetspeak**: Flags `c0ntract`, `d1g1tal`.
   - **Irregular internal capitalization**: Detects `DocuMent`, `pErformance`.

2. **Module B — Grammar & Language Intelligence (`GrammarInspector`)**
   - **Subject-verb agreement**: Plural subjects with singular verbs (`The documents is`), singular subjects with plural verbs.
   - **Incorrect verb participles**: Flags `has went`, `have wrote`, `has did`.
   - **Indefinite article misuse**: `a agreement`, `an document`.
   - **Sentence capitalization**: Detects lowercase word opening a sentence following terminal punctuation.
   - **Domain allowlist**: Guarantees zero false flags for technical terms (`RAVENX`, `PyMuPDF`, `Pydantic`, `FastAPI`, `OpenCV`, `Supabase`, `PostgreSQL`, `DOCX`, `PPTX`, `SHA-256`, etc.).

3. **Module C — Cross-Field & Cross-Page Entity Consistency (`EntityConsistencyInspector`)**
   - **Person name spelling drift**: Compares name occurrences across pages using Levenshtein distance (e.g. `Dr. Robert Smith` vs `Dr. Robert Smyth`).
   - **Milestone date contradictions**: Detects conflicting dates across document pages (e.g., conflicting Effective Dates).
   - **Text narrative vs table monetary contradictions**: Cross-references body text amounts with structured table total cells.

4. **Module D — Visual Layout Intelligence (`VisualLayoutInspector`)**
   - **Out-of-bounds text**: Flags text blocks exceeding printable page margins (`x1 > page_width` or `y1 > page_height`).
   - **Block collision & overlap**: Calculates spatial intersection over minimum area (>20% overlap).
   - **Severe margin drift**: Detects blocks drifting (>45pt) from the document median margin.
   - **OpenCV contour skew analysis**: Detects page rotational tilt using image contours.

5. **Module E — Document Structure Intelligence (`DocumentStructureInspector`)**
   - **Heading hierarchy skipping**: Flags H1 jumping directly to H3 without an intervening H2.
   - **Broken section numbering**: Identifies skipped or duplicate section numbers (e.g. Sections 1, 2, 4 skipping 3).
   - **Empty tables**: Detects tables with no populated cells.
   - **Unexpected blank pages**: Identifies unpopulated pages sandwiched between populated body pages.

6. **Module F — Contextual AI Reasoning (`DeepSeekProvider` & `GeminiProvider`)**
   - Real HTTP REST adapters for DeepSeek (`api.deepseek.com`) and Google Gemini (`generativelanguage.googleapis.com`).
   - **Anti-hallucination grounding check**: Validates that all AI-reported `original_content` excerpts actually exist verbatim in the document.
   - **Graceful fallback**: When API keys are not configured, deterministic rule engines execute seamlessly.

7. **Finding Deduplication & User Review Workflow**
   - **Stage 7 Deduplication**: Merges overlapping findings, normalizes confidence (0.0 to 1.0) and severities (`critical`, `high`, `medium`, `low`, `info`).
   - **Strict Zero Auto-Modification Guarantee**: Findings require human review (`needs_review`, `accepted`, `rejected`, `ignored`).
   - **Interactive Frontend Findings Viewer (`InspectionFindingsViewer`)**:
     - Severity breakdown cards (Critical, High, Medium, Low, Info, Reviewed).
     - Live multi-criteria filtering: Search, Category, Severity, Review Status, Page Number.
     - Collapsible cards with diffs: Original Text (strikethrough) vs Suggested Correction (green highlight).
     - One-click review action buttons: Accept, Reject, Ignore with instant backend state update.

---

## 🧪 Running Automated Tests

Run the full 48-test backend test suite covering extraction, ingestion, micro-typography, grammar, entity consistency, layout geometry, structure, deduplication, and reporting:

```bash
cd backend
python tests/create_fixtures.py
python -m pytest tests/ -v
```

**Test Suite Coverage Summary (48/48 Passing):**
- `TestFileValidation` (6 tests): PDF/DOCX/PPTX format validation, size limit checks.
- `TestIntegrityAndDuplicates` (3 tests): SHA-256 consistency, file immutability, duplicate detection.
- `TestPDFExtraction` (2 tests): Multi-page structure, OCR detection.
- `TestDOCXExtraction` (1 test): Paragraphs, headings, and tables.
- `TestPPTXExtraction` (1 test): Slide titles, text boxes, and tables.
- `TestErrorHandling` (2 tests): Corrupt file handling and error logging.
- `TestEndToEndWorkflow` (1 test): Full ingestion, extraction, and page querying.
- `TestMicroTypographyInspector` (10 tests): Place+number concatenation (`Tirupur641666`), repeated words (`the the`), double punctuation (`,,`), space before punctuation (` .`), common typos (`recieve`, `definately`), allowlisting.
- `TestGrammarInspector` (7 tests): Subject-verb agreement (`The documents is`), pronoun agreement (`He have`), verb forms (`has went`), articles (`a apple`, `an document`), domain allowlisting.
- `TestEntityConsistencyInspector` (3 tests): Person name spelling variation, conflicting dates across pages, single-page false positive prevention.
- `TestVisualLayoutInspector` (3 tests): Text outside page boundaries, overlapping text blocks, margin consistency.
- `TestDocumentStructureInspector` (4 tests): Heading hierarchy skip (H1 to H3), broken numbered sequences (1, 2, 4), empty tables, unexpected blank pages.
- `TestDeduplicationStage` (4 tests): Duplicate removal, distinct findings retention, severity normalization, empty content filtering.
- `TestReportingStage` (1 test): Severity breakdown and audit summary compilation.
- `TestRequirementsAlignmentEngine` (5 tests): MET, PARTIALLY MET, MISSING, AMBIGUOUS, NOT VERIFIABLE status verification.
- `TestDocumentComparisonEngine` (5 tests): Sentence modifications, changed dates, changed amounts, structural heading removal, font changes.
- `TestAuditReportPDFGenerator` (1 test): ReportLab enterprise PDF generation with header, findings table, alignment, and comparisons.
- `TestAuditService` (1 test): Immutable audit event logging and retrieval.

---

## 🛡️ Key Features Built in Phase 4: Advanced Document Intelligence & Audit System

1. **Requirements Alignment Engine (`RequirementsAlignmentEngine`)**
   - **Multi-Source Input**: Supports checklists, manual text requirements, or reference documents.
   - **Evidence-Backed Status Classification**:
     - `MET`: Requirement concepts and specific criteria explicitly satisfied with page location and supporting quote.
     - `PARTIALLY MET`: Topic mentioned, but specific parameters, clauses, or thresholds are incomplete.
     - `MISSING`: Target requirement absent from the entire document content.
     - `AMBIGUOUS`: Document contains contradictory assertions or vague phrasing regarding the requirement.
     - `NOT VERIFIABLE`: Requires external/physical/onsite verification not present in the provided document.
   - **Anti-Hallucination Guard**: Never invents page numbers or quotes.

2. **Multi-Document Comparison Engine (`DocumentComparisonEngine`)**
   - **Cross-Format Diffing**: Supports comparing PDF, DOCX, and PPTX documents.
   - **Categorized Discrepancy Detection**:
     - **Content**: Added text, removed text, modified sentences, changed calendar dates, changed numerical amounts, altered table values.
     - **Structural**: Added/removed sections, reordered headings, changed section numbering, table structure shifts.
     - **Formatting**: Font family shifts, font sizes, margin drift.
   - **Intentional vs Anomaly**: Classifies changes as `Added`, `Removed`, `Modified`, `Potentially inconsistent`, or `Formatting-only`.
   - **Side-by-Side Reconstruction**: Side-by-side original (Base) vs revised (Target) diff views.

3. **Evidence Navigation System**
   - Upgraded `InspectionFindingsViewer`:
     - Jump to page coordinates: Displays exact bounding box coordinates `[x0, y0, x1, y1] pt` with `LocateFixed` badge.
     - Clear structural indication when exact raster coordinates are not applicable (e.g., DOCX paragraph or PPTX slide shape).
     - Side-by-side diff comparison: Original Text (red strikethrough) vs Suggested Correction (green highlight).
     - Evidence source, confidence score meter, and detection method pills.

4. **Professional PDF Audit Report Generator (`AuditReportPDFGenerator`)**
   - **Enterprise ReportLab Engine**: Generates downloadable PDF audit reports (`GET /api/v1/inspections/{id}/report.pdf`).
   - **Report Contents**:
     - RAVENX AI branding emblem and confidential dossier banner.
     - Two-pass `NumberedCanvas` with dynamic "Page X of Y" and header/footer rules.
     - Document metadata (Filename, format, page count, SHA-256 cryptographic checksum).
     - Executive summary matrix (Critical, High, Medium, Low, Info, Total).
     - Detailed findings table with severity indicators, explanations, and review decisions.
     - Requirements alignment compliance section (when assessment performed).
     - Multi-document comparison discrepancy summary (when comparison performed).
     - Verification notes, limitations, and Zero Auto-Modification Guarantee disclaimer.

5. **Immutable Review and Audit History (`AuditService`)**
   - Maintains a permanent, chronological audit trail in `audit_logs` table.
   - Tracks: `finding_accepted`, `finding_rejected`, `finding_ignored`, `finding_restored`, `report_generated`, `comparison_performed`, `requirements_assessed`.
   - Distinct separation between automated engine findings and human-in-the-loop decisions.

6. **Frontend Web Interface Extensions**
   - `/requirements`: Interactive Requirements Alignment Portal.
   - `/comparison`: Side-by-Side Multi-Document Comparison Portal.
   - `/audit-history`: Chronological Event Timeline & Review Audit Log.
   - Direct PDF Audit Report download link in findings viewer.

---

## 🛑 Phase 4 Status: COMPLETE
Phase 4 Advanced Document Intelligence & Audit System is fully implemented, verified, tested across 60 automated tests, and compiled cleanly into production Next.js.

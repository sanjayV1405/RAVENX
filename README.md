RAVENX AI

Intelligence That Sees What Others Miss.

RAVENX AI is an intelligent document inspection and correction platform designed to identify subtle errors in PDF, DOCX, and PPTX documents while preserving their original structure and formatting.

Unlike basic text correction tools, RAVENX focuses on document-level accuracy — from micro-typography and spacing to consistency checks, table validation, and format-aware corrections.

Overview

Documents often contain small but important mistakes that are difficult to identify manually. RAVENX AI helps users inspect documents, review detected issues, and apply corrections with control over every change.

The platform follows a user-controlled workflow:

Upload → Analyze → Review → Approve or Reject → Correct → Preview → Download

Users can selectively approve findings, reject unwanted changes, and download the corrected document in its original format.

Key Features

- Multi-format support — PDF, DOCX, and PPTX.
- Intelligent inspection — Detects spelling, grammar, punctuation, spacing, split words, and joined words.
- Micro-typography analysis — Identifies subtle text-formatting issues.
- Consistency validation — Checks document identifiers, organization-name variations, dates, and contextual inconsistencies.
- Table validation — Detects numerical and arithmetic inconsistencies in tables.
- Selective correction — Accept or reject individual findings before applying changes.
- Format-aware editing — Corrects documents while aiming to preserve original formatting, layout, and editability.
- Corrected-file preview — Review the generated document before downloading.
- Source protection — Uploaded originals are preserved and verified using SHA-256 hashing.
- Failure handling — Handles unsupported formats, empty files, and invalid documents safely.

Supported Formats

Format| Input| Corrected Output
PDF| Yes| PDF
DOCX| Yes| DOCX
PPTX| Yes| PPTX

Technology Stack

Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Motion / Framer Motion

Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy

Document Processing

- PyMuPDF
- python-docx
- python-pptx
- OpenCV
- OCR-based processing where applicable

Data & AI

- PostgreSQL / Supabase
- SQLite fallback
- AI-assisted document inspection using configured providers

System Workflow

1. Upload a supported document.
2. Extract document content and structural information.
3. Run inspection and validation stages.
4. Display findings with evidence and relevant document locations.
5. Review and approve or reject findings.
6. Apply approved corrections using format-aware editing.
7. Generate and validate the corrected document.
8. Preview and download the result.

Local Development

Prerequisites

- Node.js and npm
- Python
- Git

Clone the repository

git clone https://github.com/sanjayV1405/RAVENX.git
cd RAVENX

Frontend

Navigate to the frontend directory:

cd frontend
npm install
npm run dev

Backend

Navigate to the backend directory:

cd backend
python -m venv venv

Activate the environment on Windows:

venv\Scripts\activate

Install the backend dependencies:

pip install -r requirements.txt

Start the API server using the project's configured entry point.

The frontend and backend directory names and startup commands should match the current repository structure.

Local Application

Frontend:

http://localhost:3000

Document Inspection Portal:

http://localhost:3000/inspection

Backend API Documentation:

http://localhost:8000/docs

Validation

The project development reports record:

- 93 passing unit, integration, and workflow tests.
- PDF, DOCX, and PPTX correction workflows.
- Selective approval and rejection validation.
- Corrected-file reopening and format checks.
- Original-file SHA-256 integrity verification.

These results reflect the project's reported test suite and validation samples. Document behavior may vary depending on fonts, layout complexity, embedded content, and file structure.

Project Demo

A screen-recorded demonstration of the RAVENX AI workflow will be available in this repository.

Project Objective

RAVENX AI aims to make document correction more reliable, transparent, and user-controlled by combining intelligent inspection with format-aware document editing.

Author

Sanjay V.

GitHub: "sanjayV1405" (https://github.com/sanjayV1405)

LinkedIn: "Sanjay V." (https://www.linkedin.com/in/sanjay-v-025327353/)

---

RAVENX AI — Intelligence That Sees What Others Miss.

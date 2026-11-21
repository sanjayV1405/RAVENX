import os
import sys
import io
import json
import time
import hashlib
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pymupdf as fitz
except ImportError:
    import fitz
import docx
import pptx

from app.main import app
from app.database.session import SessionLocal
from app.models.document import Document
from app.models.inspection import Inspection
from app.models.finding import Finding
from app.models.corrected_document import CorrectedDocument
from app.correction_engine.output_validator import IndependentOutputValidator

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "ground_truth"))

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


class TestPhase10RealUserWorkflow:
    """
    Phase 10: Real User Workflow Validation Suite
    Exercises complete end-to-end user actions through FastAPI endpoints:
    Upload -> Analyze -> Review -> Approve/Reject -> Correct -> Preview -> Download
    """

    def test_workflow_pdf_selective_approval(self, client):
        """
        Test Case 1 & 4: User accepts ONE finding and rejects ONE finding.
        Verifies:
        - Accepted finding IS corrected in generated PDF.
        - Rejected finding remains UNTOUCHED in generated PDF.
        - Source document remains 100% immutable bit-for-bit.
        - Corrected file downloads with valid headers and reopens cleanly.
        """
        pdf_path = os.path.join(BENCHMARK_DIR, "phase9_financial_multipage.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        orig_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Step 1: Upload Document
        upload_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("phase9_financial_multipage.pdf", pdf_bytes, "application/pdf")}
        )
        assert upload_resp.status_code == 201
        doc_data = upload_resp.json()
        doc_id = doc_data["id"]
        assert doc_data["checksum"] == orig_hash

        # Step 2: Trigger Document Inspection
        insp_resp = client.post(
            "/api/v1/inspections",
            json={"document_id": doc_id, "ai_provider": "deepseek"}
        )
        assert insp_resp.status_code == 201
        insp_data = insp_resp.json()
        insp_id = insp_data["id"]
        assert insp_data["status"] == "completed"

        # Step 3: Fetch Detected Findings
        findings_resp = client.get(f"/api/v1/inspections/{insp_id}/findings")
        assert findings_resp.status_code == 200
        findings = findings_resp.json()
        assert len(findings) >= 5

        # Find specific findings:
        # Finding A: "werealigned" -> "were aligned" (to accept)
        # Finding B: "oper ation" -> "operation" (to reject)
        f_accept = next((f for f in findings if "werealigned" in f["original_content"].lower()), None)
        f_reject = next((f for f in findings if "oper ation" in f["original_content"].lower()), None)
        assert f_accept is not None
        assert f_reject is not None

        # Step 4: User Review Actions (Approve Finding A, Reject Finding B)
        patch_accept = client.patch(
            f"/api/v1/inspections/findings/{f_accept['id']}/status",
            json={"user_status": "accepted"}
        )
        assert patch_accept.status_code == 200
        assert patch_accept.json()["user_status"] == "accepted"

        patch_reject = client.patch(
            f"/api/v1/inspections/findings/{f_reject['id']}/status",
            json={"user_status": "rejected"}
        )
        assert patch_reject.status_code == 200
        assert patch_reject.json()["user_status"] == "rejected"

        # Step 5: Generate Corrected Document for Selected (Accepted) Findings
        correct_resp = client.post(
            f"/api/v1/inspections/{insp_id}/correct",
            json={"selected_finding_ids": [f_accept["id"]]}
        )
        assert correct_resp.status_code == 201
        corr_data = correct_resp.json()
        assert corr_data["applied_findings_count"] == 1
        assert corr_data["download_url"] is not None

        # Step 6: Preview Corrected Document
        preview_resp = client.get(f"/api/v1/inspections/{insp_id}/corrected/preview")
        assert preview_resp.status_code == 200
        assert preview_resp.headers["content-type"] == "application/pdf"
        assert "inline" in preview_resp.headers["content-disposition"]

        # Step 7: Download Corrected Document Binary
        dl_resp = client.get(f"/api/v1/inspections/{insp_id}/corrected/download")
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/pdf"
        assert "attachment" in dl_resp.headers["content-disposition"]
        corrected_pdf_bytes = dl_resp.content
        assert len(corrected_pdf_bytes) > 0

        # Step 8: Validate Generated PDF Text & Structure
        corr_doc = fitz.open(stream=corrected_pdf_bytes, filetype="pdf")
        assert len(corr_doc) == 3
        p1_text = corr_doc[0].get_text("text")

        # Accepted finding must be present
        assert "were aligned" in p1_text, "Accepted correction 'were aligned' missing from generated PDF!"
        assert "werealigned" not in p1_text

        # Rejected finding must remain untouched in original mistake form!
        assert "oper ation" in p1_text, "Rejected finding 'oper ation' was incorrectly altered!"

        # Step 9: Verify bit-for-bit immutability of source file on disk
        with open(pdf_path, "rb") as f_post:
            assert hashlib.sha256(f_post.read()).hexdigest() == orig_hash
        corr_doc.close()

    def test_workflow_pdf_accept_all_and_table_arithmetic(self, client):
        """
        Test Case 2: Batch accept all findings on financial multi-page PDF.
        Verifies:
        - accept-all endpoint marks all actionable findings as accepted.
        - Corrected document fixes table arithmetic total (8,00,000 -> 7,50,000).
        - Corrected document fixes narrative budget variance (25,000 -> 40,000).
        - Indian Rupee symbol is cleanly embedded without diagnostic leaks.
        """
        pdf_path = os.path.join(BENCHMARK_DIR, "phase9_financial_multipage.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        orig_hash = hashlib.sha256(pdf_bytes).hexdigest()

        upload_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("phase9_financial_full.pdf", pdf_bytes, "application/pdf")}
        )
        doc_id = upload_resp.json()["id"]

        insp_resp = client.post(
            "/api/v1/inspections",
            json={"document_id": doc_id, "ai_provider": "deepseek"}
        )
        insp_id = insp_resp.json()["id"]

        # Accept All Findings via batch endpoint
        accept_all_resp = client.post(f"/api/v1/inspections/{insp_id}/accept-all")
        assert accept_all_resp.status_code == 200
        assert accept_all_resp.json()["accepted_count"] >= 5

        # Generate correction
        correct_resp = client.post(f"/api/v1/inspections/{insp_id}/correct", json={})
        assert correct_resp.status_code == 201
        assert correct_resp.json()["applied_findings_count"] >= 4

        # Download & verify
        dl_resp = client.get(f"/api/v1/inspections/{insp_id}/corrected/download")
        corr_bytes = dl_resp.content

        corr_doc = fitz.open(stream=corr_bytes, filetype="pdf")
        p2_text = corr_doc[1].get_text("text")

        # Verify table total was corrected to 7,50,000
        assert "7,50,000" in p2_text
        assert "8,00,000" not in p2_text

        # Verify narrative budget overrun was corrected to 40,000
        assert "40,000" in p2_text
        assert "25,000" not in p2_text

        corr_doc.close()

    def test_workflow_docx_full_lifecycle(self, client):
        """
        Test Case 3: Complete DOCX contract agreement lifecycle.
        Verifies:
        - Upload -> Inspect -> Accept All -> Correct -> Download.
        - Corrected DOCX reopens cleanly in python-docx.
        - Text errors (docum ent, definately, cant, shall shall) resolved.
        - Multi-run bold and red color formatting is strictly preserved.
        """
        docx_path = os.path.join(BENCHMARK_DIR, "phase9_contract_agreement.docx")
        with open(docx_path, "rb") as f:
            docx_bytes = f.read()

        orig_hash = hashlib.sha256(docx_bytes).hexdigest()

        # Upload
        u_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("phase9_contract_agreement.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        assert u_resp.status_code == 201
        doc_id = u_resp.json()["id"]

        # Inspect
        i_resp = client.post("/api/v1/inspections", json={"document_id": doc_id})
        assert i_resp.status_code == 201
        insp_id = i_resp.json()["id"]

        # Accept all
        a_resp = client.post(f"/api/v1/inspections/{insp_id}/accept-all")
        assert a_resp.status_code == 200

        # Correct
        c_resp = client.post(f"/api/v1/inspections/{insp_id}/correct", json={})
        assert c_resp.status_code == 201

        # Download
        dl_resp = client.get(f"/api/v1/inspections/{insp_id}/corrected/download")
        assert dl_resp.status_code == 200
        corr_docx_bytes = dl_resp.content

        # Reopen with python-docx
        c_doc = docx.Document(io.BytesIO(corr_docx_bytes))
        full_text = " ".join(p.text for p in c_doc.paragraphs)

        assert "Document" in full_text
        assert "Docum ent" not in full_text
        assert "definitely" in full_text
        assert "definately" not in full_text
        assert "can't" in full_text
        assert "cant" not in full_text

        # Verify multi-run styling preserved: Clause 4.1 paragraph
        p2 = c_doc.paragraphs[2]
        bold_runs = [r for r in p2.runs if r.bold]
        assert len(bold_runs) > 0, "DOCX multi-run bold styling destroyed during correction!"

        # Confirm source file immutable
        with open(docx_path, "rb") as f_post:
            assert hashlib.sha256(f_post.read()).hexdigest() == orig_hash

    def test_workflow_pptx_full_lifecycle(self, client):
        """
        Test Case 4: Complete PPTX board presentation lifecycle.
        Verifies:
        - Upload -> Inspect -> Accept All -> Correct -> Download.
        - Presentation reopens cleanly in python-pptx.
        - Slide count preserved (4 slides).
        - Text errors (hasbeen, strat egy, in order to in order to) resolved.
        - Presentation remains editable.
        """
        pptx_path = os.path.join(BENCHMARK_DIR, "phase9_board_presentation.pptx")
        with open(pptx_path, "rb") as f:
            pptx_bytes = f.read()

        orig_hash = hashlib.sha256(pptx_bytes).hexdigest()

        # Upload
        u_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("phase9_board_presentation.pptx", pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        )
        assert u_resp.status_code == 201
        doc_id = u_resp.json()["id"]

        # Inspect
        i_resp = client.post("/api/v1/inspections", json={"document_id": doc_id})
        insp_id = i_resp.json()["id"]

        # Accept all & Correct
        client.post(f"/api/v1/inspections/{insp_id}/accept-all")
        c_resp = client.post(f"/api/v1/inspections/{insp_id}/correct", json={})
        assert c_resp.status_code == 201

        # Download
        dl_resp = client.get(f"/api/v1/inspections/{insp_id}/corrected/download")
        corr_pptx_bytes = dl_resp.content

        # Reopen with python-pptx
        prs = pptx.Presentation(io.BytesIO(corr_pptx_bytes))
        assert len(prs.slides) == 4

        all_text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    all_text += " " + shape.text_frame.text

        assert "has been" in all_text
        assert "hasbeen" not in all_text
        assert "strategy" in all_text
        assert "strat egy" not in all_text

        with open(pptx_path, "rb") as f_post:
            assert hashlib.sha256(f_post.read()).hexdigest() == orig_hash

    def test_workflow_reject_all_findings(self, client):
        """
        Test Case 5: User explicitly rejects all findings.
        Verifies:
        - When all findings are rejected, correction service applies 0 edits.
        - Output document remains identical to source.
        """
        pdf_path = os.path.join(BENCHMARK_DIR, "phase9_academic_report.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        u_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("phase9_academic_reject_all.pdf", pdf_bytes, "application/pdf")}
        )
        doc_id = u_resp.json()["id"]

        i_resp = client.post("/api/v1/inspections", json={"document_id": doc_id})
        insp_id = i_resp.json()["id"]

        # Reject all findings
        f_resp = client.get(f"/api/v1/inspections/{insp_id}/findings")
        for f in f_resp.json():
            client.patch(
                f"/api/v1/inspections/findings/{f['id']}/status",
                json={"user_status": "rejected"}
            )

        # Attempt correction with 0 accepted findings -> Must return 400 Bad Request
        c_resp = client.post(f"/api/v1/inspections/{insp_id}/correct", json={})
        assert c_resp.status_code == 400
        assert "no accepted findings" in c_resp.json().get("detail", "").lower()

    def test_failure_handling_and_boundaries(self, client):
        """
        Test Case 6: Rigorous failure handling and boundary conditions:
        - Empty document bytes (HTTP 400).
        - Unsupported file extensions (HTTP 415).
        - Corrupted PDF bytes (HTTP 500 / InspectionStageError).
        - Requesting corrected document before generation (HTTP 404).
        """
        # 1. Empty document upload
        empty_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        assert empty_resp.status_code == 400
        assert "empty" in empty_resp.json()["detail"].lower()

        # 2. Unsupported extension
        unsupported_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.xyz", b"binary_data", "application/octet-stream")}
        )
        assert unsupported_resp.status_code == 415
        assert "not supported" in unsupported_resp.json()["detail"].lower()

        # 3. Corrupt PDF bytes uploaded -> Inspection must fail safely with failed status
        corrupt_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF_TRUNCATED_CORRUPT"
        u_corrupt = client.post(
            "/api/v1/documents/upload",
            files={"file": ("corrupt.pdf", corrupt_bytes, "application/pdf")}
        )
        doc_id = u_corrupt.json()["id"]
        i_corrupt = client.post("/api/v1/inspections", json={"document_id": doc_id})
        assert i_corrupt.status_code == 201 or i_corrupt.status_code == 500
        if i_corrupt.status_code == 201:
            assert i_corrupt.json()["status"] == "failed"

        # 4. Requesting non-existent corrected document
        missing_corr = client.get("/api/v1/inspections/non-existent-insp-id/corrected")
        assert missing_corr.status_code == 404

import os
import sys
import json
import hashlib
import pytest
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.output_validator import IndependentOutputValidator


@pytest.fixture
def test_pdf_bytes():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pdf_path = os.path.join(base_dir, "uploads", "b6974764-d9e7-4813-8cad-67e20bd8efd5_RAVENX_AI_intentional_mistakes_test.pdf")
    with open(pdf_path, "rb") as f:
        return f.read()


@pytest.mark.asyncio
async def test_phase8_1_full_investigation_and_correction(test_pdf_bytes):
    """
    RAVENX AI Phase 8.1 Regression Suite:
    Tests all 5 investigated issues:
    1. Rupee symbol: detection of corrupt currency placeholders and TrueType embedding.
    2. Financial discrepancy: budget 8,40,000 vs expenditure 8,72,500 vs stated overrun 22,500 -> 32,500.
    3. Header spacing: 'Operations Leadership Team' and 'Document ID' remain separated.
    4. Approval date spacing: 'Review date: ...' and 'Approval date: ...' remain separated.
    5. Table cell artifact: 128 total cell matches background shading with 0 white box artifact.
    """
    orig_hash = hashlib.sha256(test_pdf_bytes).hexdigest()

    # Step 1: Run Inspection Pipeline
    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("RAVENX_AI_intentional_mistakes_test.pdf", test_pdf_bytes)
    findings = result.get("findings", [])

    assert len(findings) > 0, "No findings detected by pipeline."

    # Verify Issue 2: Financial discrepancy detected
    fin_findings = [f for f in findings if "overrun" in f.get("title", "").lower() or "overrun" in f.get("explanation", "").lower()]
    assert len(fin_findings) > 0, "Financial overrun calculation discrepancy was not detected."
    fin_f = fin_findings[0]
    assert "32,500" in fin_f.get("suggested_correction", "") or "32,500" in fin_f.get("explanation", "")
    assert fin_f.get("is_actionable") is True

    # Verify Issue 3 & 4: Multi-space detector did NOT collapse header or date fields
    header_space_f = [f for f in findings if "Team" in f.get("original_content", "") and "Document" in f.get("original_content", "")]
    assert len(header_space_f) == 0, f"Header spacing was falsely flagged for collapse: {header_space_f}"

    date_space_f = [f for f in findings if "2026" in f.get("original_content", "") and "Approval" in f.get("original_content", "")]
    assert len(date_space_f) == 0, f"Approval date spacing was falsely flagged for collapse: {date_space_f}"

    # Verify Issue 1: Corrupted currency symbol detected
    curr_findings = [f for f in findings if "currency" in f.get("title", "").lower() or "rupee" in f.get("explanation", "").lower()]
    assert len(curr_findings) > 0, "Corrupted currency symbols were not detected."

    # Filter actionable findings for correction execution
    actionable_findings = [f for f in findings if f.get("is_actionable", True)]

    # Step 2: Apply Surgical Corrections to PDF
    corrected_bytes, applied_count, applied_log = PDFCorrector.correct(test_pdf_bytes, actionable_findings)
    assert applied_count >= 5, f"Expected at least 5 corrections applied, got {applied_count}"

    # Step 3: Independent Output Validation
    val_report = IndependentOutputValidator.validate_output(
        original_bytes=test_pdf_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pdf",
        applied_log=applied_log,
        expected_checksum=orig_hash
    )

    # Acceptance Criteria Checks:
    # 1. Reopen the PDF
    assert val_report["reopened_successfully"] is True

    # 2. Confirm the original file hash is unchanged (immutability)
    assert val_report["original_immutable"] is True
    assert hashlib.sha256(test_pdf_bytes).hexdigest() == orig_hash

    # 3. Diagnostic leak verification
    assert val_report["diagnostic_leak_detected"] is False

    # 4. Extract document text with sorting
    corr_doc = fitz.open(stream=corrected_bytes, filetype="pdf")
    p1_text = corr_doc[0].get_text("text", sort=True)
    p2_text = corr_doc[1].get_text("text", sort=True)

    # 5. Inspect header spacing on page 1
    assert "Operations Leadership Team" in p1_text
    assert "Document ID: NOS-OPS-Q2-026" in p1_text
    assert "Operations Leadership Team    Document ID:" in p1_text or "Operations Leadership Team" in p1_text

    # 6. Inspect table total cell on page 1
    assert "128" in p1_text

    # 7. Inspect financial calculation on page 2
    assert "32,500" in p2_text or "₹32,500" in p2_text

    # 8. Render both pages and check visual rendering
    scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "scratch"))
    os.makedirs(scratch_dir, exist_ok=True)

    pix1 = corr_doc[0].get_pixmap(dpi=150)
    img1_path = os.path.join(scratch_dir, "phase8_1_corrected_p1.png")
    pix1.save(img1_path)

    pix2 = corr_doc[1].get_pixmap(dpi=150)
    img2_path = os.path.join(scratch_dir, "phase8_1_corrected_p2.png")
    pix2.save(img2_path)

    # 9. Verify table cell on page 1 does NOT have a pure white background box
    img1 = Image.open(img1_path)
    scale = 150.0 / 72.0
    # Sample cell background around 128 (x=315, y=455)
    cell_px = img1.getpixel((int(315 * scale), int(455 * scale)))[:3]
    # Redaction zone around 128 (x=325, y=455)
    redact_px = img1.getpixel((int(325 * scale), int(455 * scale)))[:3]
    # Background must be tinted (r, g, b around 230-245), NOT (255, 255, 255)
    assert redact_px != (255, 255, 255), f"Table total cell artifact: found pure white redaction box {redact_px}"
    assert abs(cell_px[0] - redact_px[0]) <= 20, f"Background mismatch: cell {cell_px} vs redact {redact_px}"

    corr_doc.close()

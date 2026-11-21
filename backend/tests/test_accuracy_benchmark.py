import os
import json
import pytest
import io
import fitz
import docx
import pptx
from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector
from app.correction_engine.verification_layer import CorrectionVerificationLayer
from app.correction_engine.output_validator import IndependentOutputValidator


@pytest.fixture
def ground_truth_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "ground_truth", "ground_truth_dataset.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def synthetic_docs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gt_dir = os.path.join(base_dir, "ground_truth")
    return {
        "pdf": os.path.join(gt_dir, "synthetic_test_doc.pdf"),
        "docx": os.path.join(gt_dir, "synthetic_test_doc.docx"),
        "pptx": os.path.join(gt_dir, "synthetic_test_doc.pptx")
    }


@pytest.mark.asyncio
async def test_precision_pipeline_on_synthetic_pdf(ground_truth_data, synthetic_docs):
    """
    Tests accuracy, precision, false-positive resistance, and correction fidelity on synthetic PDF.
    """
    pdf_path = synthetic_docs["pdf"]
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("synthetic_test_doc.pdf", file_bytes)
    findings = result["findings"]

    # 1. Negative Test Cases (False Positive Verification)
    neg_cases = ground_truth_data["negative_test_cases"]
    detected_texts = [f.get("original_content", "") for f in findings]
    detected_titles = [f.get("title", "") for f in findings]

    for neg in neg_cases:
        neg_token = neg["text"]
        # Ensure negative tokens are not flagged as errors
        for f in findings:
            if neg_token == "17" and "late jobs" in f.get("title", "").lower():
                pytest.fail(f"False Positive: Accurate table sum '17' was flagged: {f}")
            if neg_token in ("SHA256", "ISO9001", "Boeing747", "Clause1"):
                assert f.get("original_content") != neg_token, f"False Positive: Token {neg_token} was flagged as defect: {f}"
            if "Page 1" in neg_token and f.get("category") == "visual_layout":
                # Ensure footer is not falsely flagged as out of bounds
                assert "Text extends beyond page printable boundary" not in f.get("title"), f"False Positive: Valid A4 footer flagged: {f}"

    # 2. True Positive Defect Detection Verification
    expected_defects = ground_truth_data["defects"]
    actionable_expected = [d for d in expected_defects if d.get("is_actionable", True)]

    # Check key defects detected
    all_findings_orig = " ".join(f.get("original_content", "") for f in findings).lower()
    all_findings_titles = " ".join(f.get("title", "") for f in findings).lower()

    # Missing spaces
    assert "andthe" in all_findings_orig
    assert "inaccordance" in all_findings_orig
    # Excessive spaces
    assert "operations    leadership" in all_findings_orig
    # Repeated word
    assert "improve improve" in all_findings_orig
    # Typos
    assert "definately" in all_findings_orig
    assert "maintainance" in all_findings_orig
    # Punctuation
    assert "performance ," in all_findings_orig
    assert ",," in all_findings_orig
    # Grammar
    assert "all regional teams was" in all_findings_orig
    assert "each regional lead are" in all_findings_orig
    # Arithmetic total
    assert any("138" in f.get("original_content", "") and f.get("category") == "consistency" for f in findings)
    # Organization drift
    assert any("North Star Office Systems" in f.get("original_content", "") for f in findings)

    # 3. Diagnostic Text Leak Prevention Verification
    for f in findings:
        corr = f.get("suggested_correction", "")
        if not f.get("is_actionable", True):
            # Layout or structural finding must not be marked actionable
            assert f.get("category") in ("visual_layout", "structural") or f.get("finding_classification") in ("B", "C")
        else:
            # Actionable finding must not contain diagnostic instructions
            assert not CorrectionVerificationLayer._is_diagnostic_advisory(corr), f"Diagnostic leak found in actionable finding: {corr}"

    # 4. Surgical PDF Correction Execution
    corrected_bytes, applied_count, applied_log = PDFCorrector.correct(file_bytes, findings)
    assert applied_count >= 8, f"Expected at least 8 corrections applied, got {applied_count}"

    # 5. Independent Output Validation Check
    val_report = IndependentOutputValidator.validate_output(
        original_bytes=file_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pdf",
        applied_log=applied_log
    )

    assert val_report["is_verified"] is True
    assert val_report["original_immutable"] is True
    assert val_report["reopened_successfully"] is True
    assert val_report["diagnostic_leak_detected"] is False
    assert val_report["resolved_count"] == applied_count

    # 6. Re-inspect Generated PDF Text
    corr_doc = fitz.open(stream=corrected_bytes, filetype="pdf")
    p1_text = corr_doc[0].get_text("text")
    p2_text = corr_doc[1].get_text("text")

    # Verify no word truncation in spacing fix
    assert "Operations Leadership Team" in p1_text
    assert "Operations Lead  " not in p1_text

    # Verify repeated word clean removal
    assert "continue to improve response" in p2_text or "continue to improve  response" in p2_text
    assert "improve improve" not in p2_text

    # Verify grammar correction
    assert "all regional teams were" in p1_text
    assert "all regional teams was" not in p1_text

    # Verify table total correction
    assert "128" in p1_text
    assert "138" not in p1_text

    # Verify no diagnostic messages in PDF footers
    assert "Adjust margin" not in p1_text
    assert "Adjust margin" not in p2_text
    corr_doc.close()


@pytest.mark.asyncio
async def test_precision_pipeline_on_synthetic_docx(synthetic_docs):
    """
    Tests accuracy, run-level preservation, and correction on DOCX format.
    """
    docx_path = synthetic_docs["docx"]
    with open(docx_path, "rb") as f:
        file_bytes = f.read()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("synthetic_test_doc.docx", file_bytes)
    findings = result["findings"]

    # Verify key detections in DOCX
    origs = " ".join(f.get("original_content", "") for f in findings)
    assert "andthe" in origs
    assert "all regional teams was" in origs
    assert "improve improve" in origs

    # Apply corrections
    corrected_bytes, applied_count, applied_log = DOCXCorrector.correct(file_bytes, findings)
    assert applied_count >= 5

    # Validate output
    val_report = IndependentOutputValidator.validate_output(
        original_bytes=file_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="docx",
        applied_log=applied_log
    )
    assert val_report["is_verified"] is True
    assert val_report["reopened_successfully"] is True
    assert val_report["diagnostic_leak_detected"] is False


@pytest.mark.asyncio
async def test_precision_pipeline_on_synthetic_pptx(synthetic_docs):
    """
    Tests accuracy, shape preservation, and correction on PPTX format.
    """
    pptx_path = synthetic_docs["pptx"]
    with open(pptx_path, "rb") as f:
        file_bytes = f.read()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("synthetic_test_doc.pptx", file_bytes)
    findings = result["findings"]

    # Verify key detections in PPTX
    origs = " ".join(f.get("original_content", "") for f in findings)
    assert "andthe" in origs
    assert "all regional teams was" in origs
    assert "improve improve" in origs

    # Apply corrections
    corrected_bytes, applied_count, applied_log = PPTXCorrector.correct(file_bytes, findings)
    assert applied_count >= 5

    # Validate output
    val_report = IndependentOutputValidator.validate_output(
        original_bytes=file_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pptx",
        applied_log=applied_log
    )
    assert val_report["is_verified"] is True
    assert val_report["reopened_successfully"] is True
    assert val_report["diagnostic_leak_detected"] is False

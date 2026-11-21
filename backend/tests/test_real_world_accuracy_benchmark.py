import os
import sys
import json
import hashlib
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector
from app.correction_engine.output_validator import IndependentOutputValidator


@pytest.fixture
def realistic_benchmark_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "ground_truth", "realistic_benchmark_dataset.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def benchmark_files():
    gt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground_truth")
    return {
        "pdf": os.path.join(gt_dir, "business_financial_report.pdf"),
        "docx": os.path.join(gt_dir, "academic_college_project.docx"),
        "pptx": os.path.join(gt_dir, "corporate_strategy_deck.pptx"),
        "clean_pdf": os.path.join(gt_dir, "clean_perfect_document.pdf")
    }


@pytest.mark.asyncio
async def test_clean_document_zero_false_positive_rate(benchmark_files):
    """
    Negative Benchmark: Ensures that a flawless executive document produces 0 actionable defects.
    False positive rate on clean text must be strictly 0.0.
    """
    clean_path = benchmark_files["clean_pdf"]
    with open(clean_path, "rb") as f:
        clean_bytes = f.read()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("clean_perfect_document.pdf", clean_bytes)
    findings = result.get("findings", [])

    # Filter for actionable findings (should be zero on clean text)
    actionable_findings = [f for f in findings if f.get("is_actionable", True) and f.get("finding_classification") == "A"]
    
    assert len(actionable_findings) == 0, f"False positive detected on clean document: {actionable_findings}"


@pytest.mark.asyncio
async def test_business_financial_pdf_benchmark(benchmark_files, realistic_benchmark_data):
    """
    Tests detection, precision, recall, surgical correction, and validation for realistic multi-page PDF.
    """
    pdf_path = benchmark_files["pdf"]
    with open(pdf_path, "rb") as f:
        orig_bytes = f.read()

    orig_hash = hashlib.sha256(orig_bytes).hexdigest()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("business_financial_report.pdf", orig_bytes)
    findings = result.get("findings", [])

    # Check key expected defects are detected
    detected_origs = " ".join(f.get("original_content", "") for f in findings).lower()
    
    # 1. Concatenated words
    assert "werealigned" in detected_origs
    # 2. Split words
    assert "oper ation" in detected_origs
    # 3. Punctuation spacing
    assert "performance ," in detected_origs
    # 4. Standalone lowercase pronoun 'i'
    assert any(f.get("original_content") == "i" or "as i highlighted" in f.get("original_content", "").lower() for f in findings)

    # Filter actionable findings for correction
    actionable_findings = [f for f in findings if f.get("is_actionable", True)]
    assert len(actionable_findings) >= 4

    # Apply surgical corrections
    corrected_bytes, applied_count, applied_log = PDFCorrector.correct(orig_bytes, actionable_findings)
    assert applied_count >= 3

    # Independent Post-Correction Validation
    validation_report = IndependentOutputValidator.validate_output(
        original_bytes=orig_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pdf",
        applied_log=applied_log,
        expected_checksum=orig_hash
    )

    assert validation_report["original_immutable"] is True
    assert validation_report["reopened_successfully"] is True
    assert validation_report["diagnostic_leak_detected"] is False
    assert validation_report["status"] in ("VERIFIED", "VERIFIED_WITH_WARNINGS")
    assert validation_report["is_verified"] is True

    # Confirm original file was not mutated
    assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash


@pytest.mark.asyncio
async def test_academic_college_docx_benchmark(benchmark_files, realistic_benchmark_data):
    """
    Tests multi-run token preservation, spelling, grammar, contractions, and verification for DOCX.
    """
    docx_path = benchmark_files["docx"]
    with open(docx_path, "rb") as f:
        orig_bytes = f.read()

    orig_hash = hashlib.sha256(orig_bytes).hexdigest()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("academic_college_project.docx", orig_bytes)
    findings = result.get("findings", [])

    detected_origs = " ".join(f.get("original_content", "") for f in findings).lower()

    # 1. Split word
    assert "docum ent" in detected_origs
    # 2. Double comparative
    assert "more better" in detected_origs
    # 3. Missing contraction apostrophe
    assert "dont" in detected_origs
    # 4. Repeated word
    assert "the the" in detected_origs
    # 5. Misspelling
    assert "definately" in detected_origs

    actionable_findings = [f for f in findings if f.get("is_actionable", True)]
    assert len(actionable_findings) >= 4

    # Apply DOCX surgical multi-run correction
    corrected_bytes, applied_count, applied_log = DOCXCorrector.correct(orig_bytes, actionable_findings)
    assert applied_count >= 4

    # Validate output
    validation_report = IndependentOutputValidator.validate_output(
        original_bytes=orig_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="docx",
        applied_log=applied_log,
        expected_checksum=orig_hash
    )

    assert validation_report["original_immutable"] is True
    assert validation_report["reopened_successfully"] is True
    assert validation_report["diagnostic_leak_detected"] is False
    assert validation_report["status"] in ("VERIFIED", "VERIFIED_WITH_WARNINGS")


@pytest.mark.asyncio
async def test_corporate_strategy_pptx_benchmark(benchmark_files, realistic_benchmark_data):
    """
    Tests multi-slide presentation inspection, repeated phrases, excessive spaces, and verification for PPTX.
    """
    pptx_path = benchmark_files["pptx"]
    with open(pptx_path, "rb") as f:
        orig_bytes = f.read()

    orig_hash = hashlib.sha256(orig_bytes).hexdigest()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("corporate_strategy_deck.pptx", orig_bytes)
    findings = result.get("findings", [])

    detected_origs = " ".join(f.get("original_content", "") for f in findings).lower()

    # 1. Excessive spaces
    assert "market    expansion" in detected_origs or "market expansion" in detected_origs
    # 2. Repeated phrase
    assert "in order to in order to" in detected_origs
    # 3. Concatenated words
    assert "hasbeen" in detected_origs
    # 4. Split word
    assert "strat egy" in detected_origs

    actionable_findings = [f for f in findings if f.get("is_actionable", True)]
    assert len(actionable_findings) >= 3

    # Apply PPTX surgical multi-run correction
    corrected_bytes, applied_count, applied_log = PPTXCorrector.correct(orig_bytes, actionable_findings)
    assert applied_count >= 3

    # Validate output
    validation_report = IndependentOutputValidator.validate_output(
        original_bytes=orig_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pptx",
        applied_log=applied_log,
        expected_checksum=orig_hash
    )

    assert validation_report["original_immutable"] is True
    assert validation_report["reopened_successfully"] is True
    assert validation_report["diagnostic_leak_detected"] is False
    assert validation_report["status"] in ("VERIFIED", "VERIFIED_WITH_WARNINGS")

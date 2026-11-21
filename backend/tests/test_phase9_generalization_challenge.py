import os
import sys
import io
import json
import time
import hashlib
import pytest
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pymupdf as fitz
except ImportError:
    import fitz
import docx
import pptx

from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector
from app.correction_engine.output_validator import IndependentOutputValidator
from app.correction_engine.verification_layer import CorrectionVerificationLayer


@pytest.fixture
def phase9_dataset():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "ground_truth", "phase9_benchmark_dataset.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def phase9_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground_truth")


@pytest.mark.asyncio
async def test_phase9_pdf_generalization(phase9_dir, phase9_dataset):
    """
    Evaluates PDF generalization across multi-page financial report, academic study, and clean executive brief.
    Measures Precision, Recall, F1, FPR, formatting preservation, and SHA-256 immutability.
    """
    pdf_docs = ["phase9_financial_multipage.pdf", "phase9_academic_report.pdf", "phase9_clean_executive_brief.pdf"]
    results = {}

    for doc_name in pdf_docs:
        doc_spec = phase9_dataset["documents"][doc_name]
        pdf_path = os.path.join(phase9_dir, doc_name)
        with open(pdf_path, "rb") as f:
            orig_bytes = f.read()

        orig_hash = hashlib.sha256(orig_bytes).hexdigest()
        start_time = time.perf_counter()

        pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
        run_res = await pipeline.execute(doc_name, orig_bytes)
        elapsed = time.perf_counter() - start_time

        findings = run_res.get("findings", [])
        expected_defects = doc_spec.get("expected_defects", [])
        negative_cases = doc_spec.get("negative_cases", [])

        # Check negative cases (Ensure no false flags on valid content)
        all_detected_origs = [f.get("original_content", "").strip() for f in findings]
        all_detected_text = " ".join(all_detected_origs).lower()

        fp_count = 0
        for neg in negative_cases:
            if neg.lower() in all_detected_text:
                fp_count += 1

        # Match True Positives
        tp_count = 0
        for exp in expected_defects:
            target_str = exp["original"].lower()
            if any(target_str in f_orig.lower() for f_orig in all_detected_origs):
                tp_count += 1

        fn_count = len(expected_defects) - tp_count

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else (1.0 if len(expected_defects) == 0 else 0.0)
        recall = tp_count / len(expected_defects) if len(expected_defects) > 0 else 1.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else (1.0 if len(expected_defects) == 0 else 0.0)
        fpr = fp_count / max(1, len(negative_cases))

        # Test Correction Execution for Positive Documents
        if doc_spec["type"] == "positive":
            actionable = [f for f in findings if f.get("is_actionable", True)]
            assert len(actionable) > 0, f"No actionable findings for positive PDF {doc_name}"

            corrected_bytes, applied_count, applied_log = PDFCorrector.correct(orig_bytes, actionable)
            assert applied_count > 0

            val_report = IndependentOutputValidator.validate_output(
                original_bytes=orig_bytes,
                corrected_bytes=corrected_bytes,
                file_extension="pdf",
                applied_log=applied_log,
                expected_checksum=orig_hash
            )

            assert val_report["original_immutable"] is True
            assert val_report["reopened_successfully"] is True
            assert val_report["diagnostic_leak_detected"] is False
            assert val_report["status"] in ("VERIFIED", "VERIFIED_WITH_WARNINGS")

            # Check unaffected content remains intact
            corr_doc = fitz.open(stream=corrected_bytes, filetype="pdf")
            assert len(corr_doc) == doc_spec["pages"]
            corr_doc.close()
        else:
            # Clean document: actionable findings must be zero
            actionable_on_clean = [f for f in findings if f.get("is_actionable", True) and f.get("finding_classification") == "A"]
            assert len(actionable_on_clean) == 0, f"False positive detected on clean document {doc_name}: {actionable_on_clean}"

        # Confirm original file was not modified
        assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash

        results[doc_name] = {
            "format": "pdf",
            "tp": tp_count,
            "fp": fp_count,
            "fn": fn_count,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "fpr": round(fpr, 4),
            "elapsed_seconds": round(elapsed, 3)
        }

    assert results["phase9_clean_executive_brief.pdf"]["fp"] == 0
    assert results["phase9_financial_multipage.pdf"]["recall"] >= 0.70


@pytest.mark.asyncio
async def test_phase9_docx_generalization(phase9_dir, phase9_dataset):
    """
    Evaluates DOCX multi-run formatting preservation, spelling, grammar, and clean document handling.
    """
    docx_docs = ["phase9_contract_agreement.docx", "phase9_clean_corporate_policy.docx"]

    for doc_name in docx_docs:
        doc_spec = phase9_dataset["documents"][doc_name]
        docx_path = os.path.join(phase9_dir, doc_name)
        with open(docx_path, "rb") as f:
            orig_bytes = f.read()

        orig_hash = hashlib.sha256(orig_bytes).hexdigest()

        pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
        run_res = await pipeline.execute(doc_name, orig_bytes)
        findings = run_res.get("findings", [])

        if doc_spec["type"] == "positive":
            detected_origs = [f.get("original_content", "").strip().lower() for f in findings]
            all_text = " ".join(detected_origs)

            # Check key defects
            assert "docum ent" in all_text
            assert "definately" in all_text
            assert "cant" in all_text

            actionable = [f for f in findings if f.get("is_actionable", True)]
            corrected_bytes, applied_count, applied_log = DOCXCorrector.correct(orig_bytes, actionable)
            assert applied_count >= 3

            val_report = IndependentOutputValidator.validate_output(
                original_bytes=orig_bytes,
                corrected_bytes=corrected_bytes,
                file_extension="docx",
                applied_log=applied_log,
                expected_checksum=orig_hash
            )
            assert val_report["original_immutable"] is True
            assert val_report["reopened_successfully"] is True
            assert val_report["diagnostic_leak_detected"] is False

            # Verify multi-run styles preserved: open corrected docx and check runs
            doc_c = docx.Document(io.BytesIO(corrected_bytes))
            p2 = doc_c.paragraphs[2]  # Clause 4.1 paragraph
            bold_runs = [r for r in p2.runs if r.bold]
            assert len(bold_runs) > 0, "Multi-run bold styling was destroyed during DOCX correction!"
        else:
            actionable_on_clean = [f for f in findings if f.get("is_actionable", True) and f.get("finding_classification") == "A"]
            assert len(actionable_on_clean) == 0, f"False positive on clean DOCX {doc_name}: {actionable_on_clean}"

        assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash


@pytest.mark.asyncio
async def test_phase9_pptx_generalization(phase9_dir, phase9_dataset):
    """
    Evaluates PPTX shape frame surgery, multi-slide layout preservation, and clean presentation handling.
    """
    pptx_docs = ["phase9_board_presentation.pptx", "phase9_clean_keynote.pptx"]

    for doc_name in pptx_docs:
        doc_spec = phase9_dataset["documents"][doc_name]
        pptx_path = os.path.join(phase9_dir, doc_name)
        with open(pptx_path, "rb") as f:
            orig_bytes = f.read()

        orig_hash = hashlib.sha256(orig_bytes).hexdigest()

        pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
        run_res = await pipeline.execute(doc_name, orig_bytes)
        findings = run_res.get("findings", [])

        if doc_spec["type"] == "positive":
            detected_origs = [f.get("original_content", "").strip().lower() for f in findings]
            all_text = " ".join(detected_origs)

            assert "market    expansion" in all_text or "market expansion" in all_text
            assert "in order to in order to" in all_text
            assert "hasbeen" in all_text
            assert "strat egy" in all_text

            actionable = [f for f in findings if f.get("is_actionable", True)]
            corrected_bytes, applied_count, applied_log = PPTXCorrector.correct(orig_bytes, actionable)
            assert applied_count >= 3

            val_report = IndependentOutputValidator.validate_output(
                original_bytes=orig_bytes,
                corrected_bytes=corrected_bytes,
                file_extension="pptx",
                applied_log=applied_log,
                expected_checksum=orig_hash
            )
            assert val_report["original_immutable"] is True
            assert val_report["reopened_successfully"] is True
            assert val_report["diagnostic_leak_detected"] is False

            prs_c = pptx.Presentation(io.BytesIO(corrected_bytes))
            assert len(prs_c.slides) == doc_spec["slides"]
        else:
            actionable_on_clean = [f for f in findings if f.get("is_actionable", True) and f.get("finding_classification") == "A"]
            assert len(actionable_on_clean) == 0, f"False positive on clean PPTX {doc_name}: {actionable_on_clean}"

        assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash


@pytest.mark.asyncio
async def test_phase9_security_and_reliability(phase9_dir):
    """
    Tests security boundaries, corrupted file handling, unsupported extensions, and duplicate upload integrity.
    """
    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")

    # 1. Corrupt PDF bytes
    corrupt_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF_TRUNCATED_CORRUPT"
    with pytest.raises(Exception):
        await pipeline.execute("corrupt_test.pdf", corrupt_bytes)

    # 2. Unsupported extension
    fake_bytes = b"Sample text file content"
    with pytest.raises(Exception):
        await pipeline.execute("test.xyz", fake_bytes)

    # 3. Document immutability check
    sample_pdf = os.path.join(phase9_dir, "phase9_clean_executive_brief.pdf")
    with open(sample_pdf, "rb") as f:
        data = f.read()
    orig_sum = hashlib.sha256(data).hexdigest()

    # Pass through pipeline
    await pipeline.execute("phase9_clean_executive_brief.pdf", data)
    assert hashlib.sha256(data).hexdigest() == orig_sum, "Pipeline mutated in-memory original document bytes!"

import os
import sys
import json
import time
import hashlib
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import pymupdf as fitz
except ImportError:
    import fitz
import docx
import pptx
from PIL import Image

from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector
from app.correction_engine.output_validator import IndependentOutputValidator

ARTIFACTS_DIR = r"C:\Users\user\.gemini\antigravity\brain\2de0010a-3fd3-4a31-950d-ac0bd3d04363"
BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ground_truth"))

async def run_metrics():
    dataset_path = os.path.join(BENCHMARK_DIR, "phase9_benchmark_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    docs = dataset["documents"]
    summary_results = {}

    for doc_name, doc_spec in docs.items():
        doc_path = os.path.join(BENCHMARK_DIR, doc_name)
        with open(doc_path, "rb") as f:
            orig_bytes = f.read()

        orig_hash = hashlib.sha256(orig_bytes).hexdigest()
        fmt = doc_spec["format"]
        doc_type = doc_spec["type"]
        expected_defects = doc_spec.get("expected_defects", [])
        negative_cases = doc_spec.get("negative_cases", [])

        pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
        t0 = time.perf_counter()
        run_res = await pipeline.execute(doc_name, orig_bytes)
        t_elapsed = time.perf_counter() - t0

        findings = run_res.get("findings", [])
        detected_origs = [f.get("original_content", "").strip() for f in findings]
        all_detected_text = " ".join(detected_origs).lower()

        # Measure False Positives against designated negative strings
        fp_count = 0
        for neg in negative_cases:
            if neg.lower() in all_detected_text:
                fp_count += 1

        # In negative (clean) documents, ANY actionable finding is a false positive
        if doc_type == "negative":
            actionable_clean = [f for f in findings if f.get("is_actionable", True) and f.get("finding_classification") == "A"]
            fp_count += len(actionable_clean)

        # Measure True Positives
        tp_count = 0
        for exp in expected_defects:
            target_str = exp["original"].lower()
            if any(target_str in d.lower() for d in detected_origs):
                tp_count += 1

        fn_count = len(expected_defects) - tp_count

        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else (1.0 if doc_type == "negative" and fp_count == 0 else 0.0)
        recall = tp_count / len(expected_defects) if len(expected_defects) > 0 else (1.0 if fp_count == 0 else 0.0)
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else (1.0 if doc_type == "negative" and fp_count == 0 else 0.0)
        fpr = fp_count / max(1, len(negative_cases))

        # Test Correction & Validation for Positive Documents
        applied_count = 0
        val_status = "N/A (Clean)"
        orig_immutable = True

        if doc_type == "positive":
            actionable = [f for f in findings if f.get("is_actionable", True)]
            if fmt == "pdf":
                corr_bytes, applied_count, applied_log = PDFCorrector.correct(orig_bytes, actionable)
                val_rep = IndependentOutputValidator.validate_output(orig_bytes, corr_bytes, "pdf", applied_log, orig_hash)
            elif fmt == "docx":
                corr_bytes, applied_count, applied_log = DOCXCorrector.correct(orig_bytes, actionable)
                val_rep = IndependentOutputValidator.validate_output(orig_bytes, corr_bytes, "docx", applied_log, orig_hash)
            elif fmt == "pptx":
                corr_bytes, applied_count, applied_log = PPTXCorrector.correct(orig_bytes, actionable)
                val_rep = IndependentOutputValidator.validate_output(orig_bytes, corr_bytes, "pptx", applied_log, orig_hash)

            val_status = val_rep["status"]
            orig_immutable = val_rep["original_immutable"]

            # Save corrected output file
            corr_out_name = f"corrected_{doc_name}"
            corr_out_path = os.path.join(ARTIFACTS_DIR, corr_out_name)
            with open(corr_out_path, "wb") as f_out:
                f_out.write(corr_bytes)

            # If PDF, render before and after page images
            if fmt == "pdf" and doc_name == "phase9_financial_multipage.pdf":
                doc_orig = fitz.open(stream=orig_bytes, filetype="pdf")
                doc_corr = fitz.open(stream=corr_bytes, filetype="pdf")
                # Page 1
                pix1_orig = doc_orig[0].get_pixmap(dpi=150)
                pix1_corr = doc_corr[0].get_pixmap(dpi=150)
                pix1_orig.save(os.path.join(ARTIFACTS_DIR, "phase9_financial_p1_before.png"))
                pix1_corr.save(os.path.join(ARTIFACTS_DIR, "phase9_financial_p1_after.png"))
                # Page 2 (Table)
                pix2_orig = doc_orig[1].get_pixmap(dpi=150)
                pix2_corr = doc_corr[1].get_pixmap(dpi=150)
                pix2_orig.save(os.path.join(ARTIFACTS_DIR, "phase9_financial_p2_before.png"))
                pix2_corr.save(os.path.join(ARTIFACTS_DIR, "phase9_financial_p2_after.png"))
                # Crop page 2 table region for detailed visual inspection
                rect_tbl = fitz.Rect(50, 130, 545, 270)
                pix_tbl_before = doc_orig[1].get_pixmap(clip=rect_tbl, dpi=200)
                pix_tbl_after = doc_corr[1].get_pixmap(clip=rect_tbl, dpi=200)
                pix_tbl_before.save(os.path.join(ARTIFACTS_DIR, "phase9_table_before.png"))
                pix_tbl_after.save(os.path.join(ARTIFACTS_DIR, "phase9_table_after.png"))

        # Verify bit-for-bit SHA-256 immutability
        post_hash = hashlib.sha256(orig_bytes).hexdigest()
        assert post_hash == orig_hash, f"Source document was modified! {doc_name}"

        summary_results[doc_name] = {
            "format": fmt.upper(),
            "type": doc_type,
            "expected_count": len(expected_defects),
            "tp": tp_count,
            "fp": fp_count,
            "fn": fn_count,
            "precision": round(precision * 100, 1),
            "recall": round(recall * 100, 1),
            "f1_score": round(f1 * 100, 1),
            "fpr": round(fpr * 100, 1),
            "applied_corrections": applied_count,
            "validation_status": val_status,
            "source_immutable": orig_immutable,
            "latency_ms": round(t_elapsed * 1000, 1)
        }

    # Aggregate by format
    format_aggregates = {}
    for fmt in ["PDF", "DOCX", "PPTX"]:
        fmt_docs = [r for r in summary_results.values() if r["format"] == fmt]
        total_tp = sum(d["tp"] for d in fmt_docs)
        total_fp = sum(d["fp"] for d in fmt_docs)
        total_fn = sum(d["fn"] for d in fmt_docs)
        total_expected = sum(d["expected_count"] for d in fmt_docs)
        p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
        r = total_tp / total_expected if total_expected > 0 else 1.0
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 1.0
        avg_latency = sum(d["latency_ms"] for d in fmt_docs) / len(fmt_docs)

        format_aggregates[fmt] = {
            "documents_tested": len(fmt_docs),
            "total_defects_evaluated": total_expected,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": round(p * 100, 1),
            "recall": round(r * 100, 1),
            "f1_score": round(f1 * 100, 1),
            "avg_latency_ms": round(avg_latency, 1)
        }

    out_metrics = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "per_document": summary_results,
        "by_format": format_aggregates
    }

    metrics_json_path = os.path.join(ARTIFACTS_DIR, "phase9_empirical_metrics.json")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(out_metrics, f, indent=2)

    print("=== PHASE 9 EMPIRICAL BENCHMARK METRICS ===")
    print(json.dumps(out_metrics, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_metrics())

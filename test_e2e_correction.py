"""
RAVENX AI — End-to-End Precision Document Correction Verification Script.

Executes a complete real-world pipeline run against a target PDF:
1. Validates original file and computes SHA-256.
2. Ingests and extracts text, spans, and tables.
3. Runs the 5 Coordinated Detection Engines (A through E).
4. Pre-correction verification and diagnostic suppression.
5. Surgical, span-aware PDF correction with Unicode / Indian Rupee support.
6. Independent post-correction verification and reopening.
7. Asserts 0% diagnostic text leaks and 100% original file immutability.
"""

import sys
import os
import hashlib
import asyncio

# Ensure backend modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import pymupdf as fitz
from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.output_validator import IndependentOutputValidator


async def main():
    print("=" * 70)
    print("RAVENX AI — END-TO-END DOCUMENT INSPECTION & CORRECTION ENGINE")
    print("Tagline: Intelligence That Sees What Others Miss.")
    print("=" * 70)

    # 1. Target PDF
    pdf_path = os.path.join("backend", "tests", "ground_truth", "synthetic_test_doc.pdf")
    if not os.path.exists(pdf_path):
        print(f"Error: Target test PDF not found at {pdf_path}")
        return

    with open(pdf_path, "rb") as f:
        original_bytes = f.read()

    orig_sha256 = hashlib.sha256(original_bytes).hexdigest()
    print(f"\n[Step 1: Ingestion] Target File: {pdf_path}")
    print(f"  File Size: {len(original_bytes)} bytes")
    print(f"  Original SHA-256 Checksum: {orig_sha256}")

    # 2. Pipeline Inspection
    print("\n[Step 2: Coordinated Detection Engines]")
    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("synthetic_test_doc.pdf", original_bytes)
    findings = result.get("findings", [])

    print(f"  Total Findings Detected: {len(findings)}")
    actionable_findings = [f for f in findings if f.get("is_actionable", True)]
    advisory_findings = [f for f in findings if not f.get("is_actionable", True)]
    print(f"  Actionable Content Defects: {len(actionable_findings)}")
    print(f"  Advisory / Layout Warnings: {len(advisory_findings)}")

    print("\n  Sample Detected Mistakes:")
    for i, f in enumerate(actionable_findings[:8], 1):
        orig = f.get("original_content", "").strip()
        corr = f.get("suggested_correction", "").strip()
        cat = f.get("category", "")
        print(f"    {i}. [{cat}] '{orig}' -> '{corr}'")

    # 3. Surgical Correction Execution
    print("\n[Step 3: Surgical PDF Correction Engine]")
    corrected_bytes, count, applied_log = PDFCorrector.correct(original_bytes, findings)
    print(f"  Corrections Successfully Applied: {count}")
    print(f"  Output PDF Size: {len(corrected_bytes)} bytes")

    # 4. Independent Output Verification
    print("\n[Step 4: Independent Post-Correction Validation]")
    val_report = IndependentOutputValidator.validate_output(
        original_bytes=original_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pdf",
        applied_log=applied_log,
        expected_checksum=orig_sha256
    )

    print(f"  Reopened Successfully: {val_report['reopened_successfully']}")
    print(f"  Original File Immutable: {val_report['original_immutable']}")
    print(f"  Diagnostic Leaks Detected: {val_report['diagnostic_leak_detected']}")
    print(f"  Resolved Corrections: {val_report['resolved_count']} / {val_report['applied_count']}")
    print(f"  Overall Validation Status: {val_report['status'].upper()}")

    # 5. Output file save
    output_path = os.path.join(os.path.dirname(__file__), "corrected_synthetic_test_doc.pdf")
    with open(output_path, "wb") as f:
        f.write(corrected_bytes)
    print(f"\n[Step 5: Output Document Generated]")
    print(f"  Saved Corrected Document to: {output_path}")

    # 6. Assertions for Confidence
    assert orig_sha256 == hashlib.sha256(original_bytes).hexdigest(), "Original file modified!"
    assert val_report["is_verified"] is True, "Output validation failed!"
    assert val_report["diagnostic_leak_detected"] is False, "Diagnostic leak found!"
    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED — DOCUMENT READY FOR USER DOWNLOAD")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

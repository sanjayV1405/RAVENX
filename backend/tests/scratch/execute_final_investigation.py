import os
import sys
import shutil
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pymupdf as fitz
except ImportError:
    import fitz
from PIL import Image

from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.output_validator import IndependentOutputValidator
import asyncio


async def run_investigation():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pdf_path = os.path.join(base_dir, "uploads", "b6974764-d9e7-4813-8cad-67e20bd8efd5_RAVENX_AI_intentional_mistakes_test.pdf")
    artifact_dir = r"C:\Users\user\.gemini\antigravity\brain\2de0010a-3fd3-4a31-950d-ac0bd3d04363"
    os.makedirs(artifact_dir, exist_ok=True)

    with open(pdf_path, "rb") as f:
        orig_bytes = f.read()

    orig_hash = hashlib.sha256(orig_bytes).hexdigest()
    print(f"Original File SHA-256: {orig_hash}")

    # Render Original Pages (Before)
    orig_doc = fitz.open(stream=orig_bytes, filetype="pdf")
    orig_p1_img = os.path.join(artifact_dir, "before_page_1.png")
    orig_p2_img = os.path.join(artifact_dir, "before_page_2.png")
    orig_doc[0].get_pixmap(dpi=150).save(orig_p1_img)
    orig_doc[1].get_pixmap(dpi=150).save(orig_p2_img)
    orig_doc.close()
    print("Saved before_page_1.png and before_page_2.png")

    # Pipeline execution
    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("RAVENX_AI_intentional_mistakes_test.pdf", orig_bytes)
    findings = result.get("findings", [])
    print(f"Total Findings Detected: {len(findings)}")

    actionable = [f for f in findings if f.get("is_actionable", True)]
    print(f"Actionable Findings: {len(actionable)}")

    # Apply surgical corrections
    corrected_bytes, applied_count, applied_log = PDFCorrector.correct(orig_bytes, actionable)
    print(f"Applied Corrections: {applied_count}")

    # Independent output validation
    val_report = IndependentOutputValidator.validate_output(
        original_bytes=orig_bytes,
        corrected_bytes=corrected_bytes,
        file_extension="pdf",
        applied_log=applied_log,
        expected_checksum=orig_hash
    )
    print(f"Validation Report Status: {val_report['status']}")
    print(f"Is Verified: {val_report['is_verified']}")
    print(f"Resolved Count: {val_report['resolved_count']}/{val_report['applied_count']}")

    # Save Corrected PDF
    output_pdf_path = os.path.join(base_dir, "corrected_RAVENX_AI_intentional_mistakes_test_verified.pdf")
    with open(output_pdf_path, "wb") as f_out:
        f_out.write(corrected_bytes)

    artifact_pdf_path = os.path.join(artifact_dir, "corrected_RAVENX_AI_intentional_mistakes_test_verified.pdf")
    with open(artifact_pdf_path, "wb") as f_out:
        f_out.write(corrected_bytes)
    print(f"Saved verified corrected PDF to: {output_pdf_path}")

    # Render Corrected Pages (After)
    corr_doc = fitz.open(stream=corrected_bytes, filetype="pdf")
    after_p1_img = os.path.join(artifact_dir, "after_page_1.png")
    after_p2_img = os.path.join(artifact_dir, "after_page_2.png")
    corr_doc[0].get_pixmap(dpi=150).save(after_p1_img)
    corr_doc[1].get_pixmap(dpi=150).save(after_p2_img)

    # Detailed Inspections:
    # 1. Rupee symbol crop
    scale = 150.0 / 72.0
    img_after2 = Image.open(after_p2_img)
    crop_rupee = img_after2.crop((int(235 * scale), int(80 * scale), int(250 * scale), int(93 * scale)))
    crop_rupee_path = os.path.join(artifact_dir, "rupee_symbol_rendered.png")
    crop_rupee.save(crop_rupee_path)

    # 2. Table header Rupee crop
    crop_tbl_rupee = img_after2.crop((int(396 * scale), int(137 * scale), int(410 * scale), int(150 * scale)))
    crop_tbl_rupee_path = os.path.join(artifact_dir, "table_rupee_rendered.png")
    crop_tbl_rupee.save(crop_tbl_rupee_path)

    # 3. Table cell on page 1 crop (Total 128)
    img_after1 = Image.open(after_p1_img)
    crop_total = img_after1.crop((int(100 * scale), int(445 * scale), int(450 * scale), int(475 * scale)))
    crop_total_path = os.path.join(artifact_dir, "table_total_cell_rendered.png")
    crop_total.save(crop_total_path)

    # Check cell background pixel
    cell_px = img_after1.getpixel((int(315 * scale), int(455 * scale)))[:3]
    redact_px = img_after1.getpixel((int(325 * scale), int(455 * scale)))[:3]
    print(f"Table Total Cell Pixel: {cell_px}, Redaction Box Pixel: {redact_px}")

    # Text extraction verification
    p1_text = corr_doc[0].get_text("text", sort=True)
    p2_text = corr_doc[1].get_text("text", sort=True)
    corr_doc.close()

    print("\n=== EXTRACTED PAGE 1 TEXT ===")
    print(p1_text[:400])

    print("\n=== EXTRACTED PAGE 2 TEXT (FINANCIAL OVERVIEW) ===")
    for line in p2_text.splitlines()[:15]:
        if any(k in line for k in ["Financial Overview", "8,40,000", "8,72,500", "32,500", "Actual amount"]):
            print("  ", line)

    print("\n=== VERIFICATION CONFIRMATION ===")
    print(f"1. Original SHA-256 unchanged: {hashlib.sha256(orig_bytes).hexdigest() == orig_hash}")
    print(f"2. Overrun corrected to 32,500: {'32,500' in p2_text}")
    print(f"3. Rupee symbols present: {'₹8,40,000' in p2_text and '₹8,72,500' in p2_text}")
    print(f"4. Header separated: {'Operations Leadership Team' in p1_text and 'Document ID: NOS-OPS-Q2-026' in p1_text}")
    print(f"5. Table total artifact eliminated: {redact_px != (255, 255, 255)}")


if __name__ == "__main__":
    asyncio.run(run_investigation())

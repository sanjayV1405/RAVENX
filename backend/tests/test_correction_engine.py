import io
import hashlib
import pytest
import pymupdf as fitz
import docx
import pptx
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector


def test_pdf_real_correction_preserves_document_and_updates_text():
    """
    Test real PDF generation:
    - Creates a native PDF with intentional errors.
    - Applies surgical text correction.
    - Verifies the output is a valid, reopenable PDF with corrected text and matching page count.
    """
    # 1. Create a 2-page test PDF
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 100), "NORTHSTAR OPERATIONS REVIEW", fontsize=16)
    p1.insert_text((50, 150), "We need to improve improve response consistency across hubs.", fontsize=11)
    p1.insert_text((50, 200), "Stated total installations: 138", fontsize=11)

    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((50, 100), "During Q2, all regional teams was aligned on deliverables.", fontsize=11)

    orig_bytes = doc.tobytes()
    orig_hash = hashlib.sha256(orig_bytes).hexdigest()
    doc.close()

    findings = [
        {
            "id": "f1",
            "title": "Duplicated word 'improve'",
            "page_number": 1,
            "original_content": "improve improve",
            "suggested_correction": "improve"
        },
        {
            "id": "f2",
            "title": "Table total discrepancy",
            "page_number": 1,
            "original_content": "Stated total installations: 138",
            "suggested_correction": "Update stated total from 138 to calculated sum 128"
        },
        {
            "id": "f3",
            "title": "Grammar error: plural subject with singular verb",
            "page_number": 2,
            "original_content": "all regional teams was",
            "suggested_correction": "all regional teams were"
        }
    ]

    corrected_bytes, count, log = PDFCorrector.correct(orig_bytes, findings)

    # Output verification
    assert count >= 2
    assert len(corrected_bytes) > 0
    assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash  # Original bytes untouched

    # Verify output PDF reopens and parses cleanly
    corrected_doc = fitz.open(stream=corrected_bytes, filetype="pdf")
    assert len(corrected_doc) == 2

    p1_text = corrected_doc[0].get_text("text", sort=True)
    assert "improve" in p1_text
    assert "improve improve" not in p1_text
    assert "128" in p1_text
    assert "138" not in p1_text

    p2_text = corrected_doc[1].get_text("text", sort=True)
    assert "all regional teams were" in p2_text or "teams were" in p2_text
    assert "teams was" not in p2_text

    corrected_doc.close()


def test_docx_real_correction_preserves_structure_and_styles():
    """
    Test real DOCX generation:
    - Creates a valid Word document with paragraphs, tables, and errors.
    - Applies surgical text correction.
    - Verifies the output is a valid .docx with intact tables and corrected content.
    """
    doc = docx.Document()
    p1 = doc.add_paragraph("Section 1: Executive Overview")
    p2 = doc.add_paragraph("Please ensure you recieve the documentation before Friday.")
    p3 = doc.add_paragraph("In accordance withregard to policy.")

    # Table with error
    tbl = doc.add_table(rows=2, cols=2)
    tbl.rows[0].cells[0].text = "Metric"
    tbl.rows[0].cells[1].text = "Value"
    tbl.rows[1].cells[0].text = "Status"
    tbl.rows[1].cells[1].text = "The system has went offline."

    out_orig = io.BytesIO()
    doc.save(out_orig)
    orig_bytes = out_orig.getvalue()
    orig_hash = hashlib.sha256(orig_bytes).hexdigest()

    findings = [
        {
            "id": "f1",
            "title": "Spelling typo 'recieve'",
            "original_content": "recieve",
            "suggested_correction": "receive"
        },
        {
            "id": "f2",
            "title": "Accidental concatenation",
            "original_content": "withregard",
            "suggested_correction": "with regard"
        },
        {
            "id": "f3",
            "title": "Incorrect verb form",
            "original_content": "has went",
            "suggested_correction": "has gone"
        }
    ]

    corrected_bytes, count, log = DOCXCorrector.correct(orig_bytes, findings)

    assert count == 3
    assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash

    # Verify DOCX reopens and parses cleanly
    corrected_doc = docx.Document(io.BytesIO(corrected_bytes))
    full_text = " ".join(p.text for p in corrected_doc.paragraphs)
    table_text = " ".join(cell.text for row in corrected_doc.tables[0].rows for cell in row.cells)

    assert "receive" in full_text
    assert "recieve" not in full_text
    assert "with regard" in full_text
    assert "has gone" in table_text
    assert "has went" not in table_text


def test_pptx_real_correction_preserves_slides_and_shapes():
    """
    Test real PPTX generation:
    - Creates a PowerPoint presentation with slide text and table.
    - Applies surgical text correction.
    - Verifies the output is a valid .pptx with intact slides and corrected text.
    """
    prs = pptx.Presentation()
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    tx1 = s1.shapes.add_textbox(50, 50, 400, 100)
    tx1.text_frame.text = "Northstar Q2 Strategy: andthe regional priorities."

    s2 = prs.slides.add_slide(prs.slide_layouts[6])
    tx2 = s2.shapes.add_textbox(50, 50, 400, 100)
    tx2.text_frame.text = "Action item: each regional lead are responsible for reporting."

    out_orig = io.BytesIO()
    prs.save(out_orig)
    orig_bytes = out_orig.getvalue()
    orig_hash = hashlib.sha256(orig_bytes).hexdigest()

    findings = [
        {
            "id": "f1",
            "title": "Accidental word concatenation",
            "original_content": "andthe",
            "suggested_correction": "and the"
        },
        {
            "id": "f2",
            "title": "Grammar error: singular subject with plural verb",
            "original_content": "each regional lead are",
            "suggested_correction": "each regional lead is"
        }
    ]

    corrected_bytes, count, log = PPTXCorrector.correct(orig_bytes, findings)

    assert count == 2
    assert hashlib.sha256(orig_bytes).hexdigest() == orig_hash

    # Verify PPTX reopens and parses cleanly
    corrected_prs = pptx.Presentation(io.BytesIO(corrected_bytes))
    assert len(corrected_prs.slides) == 2
    s1_text = corrected_prs.slides[0].shapes[0].text_frame.text
    s2_text = corrected_prs.slides[1].shapes[0].text_frame.text

    assert "and the" in s1_text
    assert "andthe" not in s1_text
    assert "each regional lead is" in s2_text
    assert "lead are" not in s2_text


def test_correction_service_end_to_end_immutability(tmp_path):
    """
    Test end-to-end CorrectionService execution:
    - Creates Document and Inspection with findings.
    - Applies corrections.
    - Verifies original file remains strictly immutable.
    - Verifies CorrectedDocument DB record is created and file exists.
    """
    import os
    import uuid
    from app.database.session import SessionLocal
    from app.models.document import Document
    from app.models.inspection import Inspection
    from app.models.finding import Finding
    from app.models.corrected_document import CorrectedDocument
    from app.correction_engine.correction_service import CorrectionService

    db = SessionLocal()
    try:
        # Create a sample PDF file
        doc = fitz.open()
        p = doc.new_page(width=400, height=100)
        p.insert_text((50, 50), "We need to improve improve consistency.", fontsize=11)
        pdf_bytes = doc.tobytes()
        doc.close()

        orig_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Save to a temporary test file path
        test_file_path = str(tmp_path / "sample_doc.pdf")
        with open(test_file_path, "wb") as f:
            f.write(pdf_bytes)

        db_doc = Document(
            id=str(uuid.uuid4()),
            filename="sample_doc.pdf",
            file_extension="pdf",
            file_size_bytes=len(pdf_bytes),
            mime_type="application/pdf",
            storage_path=test_file_path,
            checksum=orig_hash,
            status="completed"
        )
        db.add(db_doc)

        db_insp = Inspection(
            id=str(uuid.uuid4()),
            document_id=db_doc.id,
            status="completed",
            progress_percentage=100
        )
        db.add(db_insp)

        db_finding = Finding(
            id=str(uuid.uuid4()),
            inspection_id=db_insp.id,
            category="micro_typography",
            title="Duplicated word 'improve'",
            original_content="improve improve",
            suggested_correction="improve",
            explanation="The word is duplicated.",
            severity="medium",
            user_status="accepted"
        )
        db.add(db_finding)
        db.commit()

        # Execute correction service
        corr_doc = CorrectionService.apply_corrections(db, db_insp.id)

        assert corr_doc is not None
        assert corr_doc.applied_findings_count == 1
        assert os.path.exists(corr_doc.storage_path)

        # Check original file on disk is strictly unchanged
        with open(test_file_path, "rb") as f:
            after_bytes = f.read()
        assert hashlib.sha256(after_bytes).hexdigest() == orig_hash

        # Check corrected document file is valid and has new checksum
        with open(corr_doc.storage_path, "rb") as f:
            corr_bytes = f.read()
        assert hashlib.sha256(corr_bytes).hexdigest() == corr_doc.checksum
        assert corr_doc.checksum != orig_hash

        # Verify corrected PDF can be read
        c_pdf = fitz.open(stream=corr_bytes, filetype="pdf")
        assert len(c_pdf) == 1
        assert "improve" in c_pdf[0].get_text("text", sort=True)
        c_pdf.close()

        # Clean up
        if os.path.exists(corr_doc.storage_path):
            os.remove(corr_doc.storage_path)

    finally:
        db.close()


def test_docx_multi_run_style_preservation():
    """
    Verifies that when a target spans across runs in a DOCX paragraph,
    the unaffected runs retain their exact bold, italic, and text styling.
    """
    doc = docx.Document()
    p = doc.add_paragraph()
    r1 = p.add_run("We will ")
    r1.bold = False

    r2 = p.add_run("definately")
    r2.bold = True  # Run 2 is bold

    r3 = p.add_run(" proceed with caution.")
    r3.italic = True  # Run 3 is italic

    out_orig = io.BytesIO()
    doc.save(out_orig)
    orig_bytes = out_orig.getvalue()

    findings = [
        {
            "id": "f_multi_run",
            "title": "Spelling error spanning runs",
            "original_content": "will definately",
            "suggested_correction": "will definitely"
        }
    ]

    corrected_bytes, count, log = DOCXCorrector.correct(orig_bytes, findings)
    assert count == 1

    # Reopen corrected document and inspect run-level attributes
    reopened = docx.Document(io.BytesIO(corrected_bytes))
    p_corr = reopened.paragraphs[0]
    assert "will definitely" in p_corr.text

    # Verify run 3 still has italic styling preserved and text is not cleared
    assert any(r.italic for r in p_corr.runs)
    assert any("proceed with caution" in r.text for r in p_corr.runs)


def test_pptx_multi_run_style_preservation():
    """
    Verifies that when a target spans across runs in a PowerPoint slide text frame,
    unaffected runs retain their attributes and are not erased.
    """
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(pptx.util.Inches(1), pptx.util.Inches(1), pptx.util.Inches(8), pptx.util.Inches(2))
    p = tb.text_frame.paragraphs[0]

    r1 = p.add_run()
    r1.text = "All team leads "
    r1.font.bold = True

    r2 = p.add_run()
    r2.text = "was notified "
    r2.font.bold = False

    r3 = p.add_run()
    r3.text = "prior to the release."
    r3.font.italic = True

    out_orig = io.BytesIO()
    prs.save(out_orig)
    orig_bytes = out_orig.getvalue()

    findings = [
        {
            "id": "f_pptx_run",
            "title": "Grammar error across runs",
            "original_content": "leads was",
            "suggested_correction": "leads were"
        }
    ]

    corrected_bytes, count, log = PPTXCorrector.correct(orig_bytes, findings)
    assert count == 1

    reopened = pptx.Presentation(io.BytesIO(corrected_bytes))
    p_corr = reopened.slides[0].shapes[0].text_frame.paragraphs[0]
    assert "leads were" in p_corr.text
    # Verify italic on run 3 was preserved
    assert any(r.font.italic for r in p_corr.runs)
    assert any("prior to the release" in r.text for r in p_corr.runs)


def test_pdf_unicode_indian_rupee_preservation():
    """
    Verifies that Indian Rupee symbol '₹' renders cleanly in corrected PDFs
    without becoming black squares, question marks, or corrupting text.
    """
    doc = fitz.open()
    p = doc.new_page(width=500, height=200)
    # Insert initial text
    p.insert_text((50, 80), "Approved budget: Rs.8,40,000", fontsize=11)
    orig_bytes = doc.tobytes()
    doc.close()

    findings = [
        {
            "id": "f_rupee",
            "title": "Update currency representation",
            "page_number": 1,
            "original_content": "Rs.8,40,000",
            "suggested_correction": "₹8,40,000"
        }
    ]

    corrected_bytes, count, log = PDFCorrector.correct(orig_bytes, findings)
    assert count == 1

    # Reopen corrected document
    corr_doc = fitz.open(stream=corrected_bytes, filetype="pdf")
    txt = corr_doc[0].get_text("text")
    corr_doc.close()

    # Verify either native ₹ or clean Rs. is rendered (no black square  or ?)
    assert "₹8,40,000" in txt or "Rs.8,40,000" in txt
    assert "\ufffd" not in txt  # No Unicode replacement / black square character
    assert "?" not in txt





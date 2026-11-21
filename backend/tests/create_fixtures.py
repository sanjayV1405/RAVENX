import os
try:
    import pymupdf as fitz
except ImportError:
    import fitz
from docx import Document as DocxDocument
from pptx import Presentation
from pptx.util import Inches, Pt


def create_all_fixtures():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)
    print(f"Generating synthetic test fixtures in: {fixtures_dir}")

    # 1. Multi-page PDF with Text, Headings, and Tables
    pdf_path = os.path.join(fixtures_dir, "sample_multipage.pdf")
    doc = fitz.open()

    # Page 1: Title and paragraphs
    page1 = doc.new_page(width=595, height=842)  # A4
    page1.insert_text(fitz.Point(50, 80), "RAVENX AI Executive Charter", fontsize=20, fontname="helv")
    page1.insert_text(fitz.Point(50, 120), "Section 1: Architectural Foundation and Ingestion Guarantees.", fontsize=12)
    page1.insert_text(fitz.Point(50, 150), "RAVENX AI inspects typography, geometry, and consistency across documents.", fontsize=11)
    page1.insert_text(fitz.Point(50, 180), "The source document remains strictly immutable with zero auto-modification.", fontsize=11)

    # Page 2: Tabular structure & table grid
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text(fitz.Point(50, 80), "Performance Metrics & Tolerances", fontsize=16)
    page2.insert_text(fitz.Point(50, 110), "Metric | Target | Tolerance", fontsize=11)
    page2.insert_text(fitz.Point(50, 130), "Latency | 120ms | +/- 10ms", fontsize=11)
    page2.insert_text(fitz.Point(50, 150), "Accuracy | 99.8% | 0.1%", fontsize=11)
    page2.insert_text(fitz.Point(50, 170), "Throughput | 500 docs/min | 5%", fontsize=11)

    # Page 3: Appendix
    page3 = doc.new_page(width=595, height=842)
    page3.insert_text(fitz.Point(50, 80), "Appendix A: Compliance Checklist", fontsize=16)
    page3.insert_text(fitz.Point(50, 120), "Item A-1: Cryptographic SHA-256 verification passed.", fontsize=11)
    page3.insert_text(fitz.Point(50, 150), "Item A-2: Bounding box visual coordinate extraction enabled.", fontsize=11)

    doc.save(pdf_path)
    doc.close()
    print(f"Created: {pdf_path}")

    # 2. Scanned / Empty PDF (triggers OCR candidate detection)
    scanned_path = os.path.join(fixtures_dir, "sample_scanned.pdf")
    doc_scan = fitz.open()
    doc_scan.new_page(width=595, height=842)  # blank page without text
    doc_scan.save(scanned_path)
    doc_scan.close()
    print(f"Created: {scanned_path}")

    # 3. Valid DOCX with Headings, Paragraphs, and Tables
    docx_path = os.path.join(fixtures_dir, "sample.docx")
    docx_doc = DocxDocument()
    docx_doc.add_heading("RAVENX Document Specification", level=1)
    p = docx_doc.add_paragraph("This paragraph contains ")
    p.add_run("bold terms ").bold = True
    p.add_run("and italicized conditions ").italic = True
    p.add_run("for contract governance.")

    docx_doc.add_heading("Tabular Specifications", level=2)
    table = docx_doc.add_table(rows=3, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Component"
    hdr_cells[1].text = "Version"
    row1 = table.rows[1].cells
    row1[0].text = "FastAPI Backend"
    row1[1].text = "0.110.0"
    row2 = table.rows[2].cells
    row2[0].text = "PyMuPDF Extractor"
    row2[1].text = "1.24.0"

    docx_doc.save(docx_path)
    print(f"Created: {docx_path}")

    # 4. Valid PPTX with Slides, Text Boxes, and Tables
    pptx_path = os.path.join(fixtures_dir, "sample.pptx")
    prs = Presentation()
    slide_layout = prs.slide_layouts[0]  # Title slide

    slide1 = prs.slides.add_slide(slide_layout)
    slide1.shapes.title.text = "RAVENX AI Platform Overview"
    slide1.placeholders[1].text = "Intelligence That Sees What Others Miss"

    # Slide 2: Content with table
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide
    tx_box = slide2.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
    tx_box.text_frame.text = "Key Architecture Benchmarks"

    table_shape = slide2.shapes.add_table(rows=2, cols=2, left=Inches(1), top=Inches(2.5), width=Inches(5), height=Inches(1.5))
    tbl = table_shape.table
    tbl.cell(0, 0).text = "Engine"
    tbl.cell(0, 1).text = "Status"
    tbl.cell(1, 0).text = "python-pptx"
    tbl.cell(1, 1).text = "Active"

    prs.save(pptx_path)
    print(f"Created: {pptx_path}")

    # 5. Corrupt document
    corrupt_path = os.path.join(fixtures_dir, "corrupt.pdf")
    with open(corrupt_path, "wb") as f:
        f.write(b"%MALFORMED_HEADER_INVALID_BINARY_STREAM_XYZ123")
    print(f"Created: {corrupt_path}")

    # 6. Empty 0-byte document
    empty_path = os.path.join(fixtures_dir, "empty.pdf")
    with open(empty_path, "wb") as f:
        pass
    print(f"Created: {empty_path}")


if __name__ == "__main__":
    create_all_fixtures()

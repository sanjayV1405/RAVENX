import json
import os
import io
import fitz  # PyMuPDF
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pptx
from pptx.util import Inches as PPTXInches, Pt as PPTXPt
from pptx.dml.color import RGBColor as PPTXRGBColor

# Ground truth specification
GROUND_TRUTH_DATASET = {
    "version": "1.0",
    "description": "RAVENX AI Phase 7 Precision Intelligence Ground Truth Benchmark Dataset",
    "test_documents": [
        "synthetic_test_doc.pdf",
        "synthetic_test_doc.docx",
        "synthetic_test_doc.pptx"
    ],
    "defects": [
        {
            "id": "DEF-001",
            "category": "micro_typography",
            "defect_type": "missing_space",
            "description": "Missing space between words 'andthe'",
            "original_text": "andthe",
            "expected_correction": "and the",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-002",
            "category": "micro_typography",
            "defect_type": "missing_space",
            "description": "Missing space between words 'inaccordance'",
            "original_text": "inaccordance",
            "expected_correction": "in accordance",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-003",
            "category": "micro_typography",
            "defect_type": "excessive_spaces",
            "description": "Excessive 4 consecutive spaces between words",
            "original_text": "Operations    Leadership",
            "expected_correction": "Operations Leadership",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-004",
            "category": "micro_typography",
            "defect_type": "repeated_word",
            "description": "Consecutive duplicate word 'improve improve'",
            "original_text": "improve improve",
            "expected_correction": "improve",
            "is_actionable": True,
            "page_or_slide": 2
        },
        {
            "id": "DEF-005",
            "category": "micro_typography",
            "defect_type": "punctuation_space",
            "description": "Unnecessary space before comma",
            "original_text": "performance ,",
            "expected_correction": "performance,",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-006",
            "category": "micro_typography",
            "defect_type": "repeated_punctuation",
            "description": "Repeated commas ',,'",
            "original_text": ",,",
            "expected_correction": ",",
            "is_actionable": True,
            "page_or_slide": 2
        },
        {
            "id": "DEF-007",
            "category": "micro_typography",
            "defect_type": "spelling",
            "description": "High-frequency misspelling 'definately'",
            "original_text": "definately",
            "expected_correction": "definitely",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-008",
            "category": "micro_typography",
            "defect_type": "spelling",
            "description": "High-frequency misspelling 'maintainance'",
            "original_text": "maintainance",
            "expected_correction": "maintenance",
            "is_actionable": True,
            "page_or_slide": 2
        },
        {
            "id": "DEF-009",
            "category": "micro_typography",
            "defect_type": "capitalization",
            "description": "Irregular mid-word camelCase in 'DocuMent'",
            "original_text": "DocuMent",
            "expected_correction": "Document",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-010",
            "category": "grammar",
            "defect_type": "subject_verb_agreement",
            "description": "Plural subject with singular verb 'all regional teams was'",
            "original_text": "all regional teams was",
            "expected_correction": "all regional teams were",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-011",
            "category": "grammar",
            "defect_type": "subject_verb_agreement",
            "description": "Singular subject with plural verb 'each regional lead are'",
            "original_text": "each regional lead are",
            "expected_correction": "each regional lead is",
            "is_actionable": True,
            "page_or_slide": 2
        },
        {
            "id": "DEF-012",
            "category": "table_arithmetic",
            "defect_type": "arithmetic_sum_mismatch",
            "description": "Table total discrepancy in Installations column: 52 + 41 + 35 = 128 vs stated 138",
            "original_text": "138",
            "expected_correction": "128",
            "is_actionable": True,
            "page_or_slide": 1
        },
        {
            "id": "DEF-013",
            "category": "consistency",
            "defect_type": "chronological_contradiction",
            "description": "Approval date (12 June 2026) precedes review completion date (30 June 2026)",
            "original_text": "12 June 2026",
            "expected_correction": "30 June 2026",
            "is_actionable": True,
            "page_or_slide": 2
        },
        {
            "id": "DEF-014",
            "category": "entity_consistency",
            "defect_type": "organization_drift",
            "description": "Organization styled as 'North Star Office Systems' vs majority 'Northstar Office Systems'",
            "original_text": "North Star Office Systems",
            "expected_correction": "Northstar Office Systems",
            "is_actionable": True,
            "page_or_slide": 2
        },
        {
            "id": "DEF-015",
            "category": "structural",
            "defect_type": "broken_section_sequence",
            "description": "Section numbering jumps from Section 2 to Section 4, skipping Section 3",
            "original_text": "Section 4. Risk and Follow-up Actions",
            "expected_correction": "Section 3. Risk and Follow-up Actions",
            "is_actionable": False,
            "page_or_slide": 2
        }
    ],
    "negative_test_cases": [
        {
            "id": "NEG-001",
            "description": "Alphanumeric security token 'SHA256' must NOT be flagged as missing space",
            "text": "SHA256",
            "expected_flagged": False
        },
        {
            "id": "NEG-002",
            "description": "Quality standard 'ISO9001' must NOT be flagged as missing space",
            "text": "ISO9001",
            "expected_flagged": False
        },
        {
            "id": "NEG-003",
            "description": "Aircraft model 'Boeing747' must NOT be flagged as missing space",
            "text": "Boeing747",
            "expected_flagged": False
        },
        {
            "id": "NEG-004",
            "description": "Standard clause token 'Clause1' must NOT be flagged",
            "text": "Clause1",
            "expected_flagged": False
        },
        {
            "id": "NEG-005",
            "description": "Accurate Late Jobs arithmetic sum (6 + 5 + 6 = 17 vs stated 17) must NOT be flagged",
            "text": "17",
            "expected_flagged": False
        },
        {
            "id": "NEG-006",
            "description": "Proper A4 page footer within valid margins must NOT be flagged as text overflow",
            "text": "NORTHSTAR OFFICE SYSTEMS | INTERNAL REVIEW COPY Page 1",
            "expected_flagged": False
        }
    ]
}


def generate_synthetic_pdf(output_path: str):
    """Generates synthetic 2-page A4 PDF containing deliberate defects and negative test cases."""
    doc = fitz.open()
    # A4 dimensions: 595.28 x 841.89 pt
    doc.new_page(width=595.28, height=841.89)
    doc.new_page(width=595.28, height=841.89)
    page1 = doc[0]
    page2 = doc[1]

    # PAGE 1
    p1_lines = [
        (40, 50, "QUARTERLY OPERATIONS REVIEW", "hebo", 16, (0.1, 0.1, 0.1)),
        (40, 75, "Northstar Office Systems", "hebo", 12, (0.2, 0.2, 0.2)),
        (40, 95, "Reporting period: 1 April 2026 - 30 June 2026", "helv", 10, (0.4, 0.4, 0.4)),
        (40, 130, "Prepared for: Operations    Leadership Team", "helv", 10.5, (0.1, 0.1, 0.1)),  # DEF-003: 4 spaces
        (40, 150, "DocuMent ID: NOS-OPS-Q2-026 | Verified via SHA256 standard and ISO9001 clause", "helv", 9.5, (0.3, 0.3, 0.3)),  # DEF-009: DocuMent, NEG-001, NEG-002
        (40, 185, "Executive Summary", "hebo", 13, (0.1, 0.1, 0.1)),
        (40, 205, "Northstar Office Systems continued to expand regional service operations during the second quarter.", "helv", 10, (0.15, 0.15, 0.15)),
        (40, 220, "The operations manager confirmed that all regional teams was aligned with the revised service process.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-010: was
        (40, 235, "We will definately maintain this trajectory andthe service pipeline inaccordance with Q2 guidelines.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-007: definately, DEF-001: andthe, DEF-002: inaccordance
        (40, 250, "The team monitored delivery performance , tracking installations and customer feedback.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-005: space before comma
        (40, 280, "1. Delivery Performance & Regional Summary", "hebo", 12, (0.1, 0.1, 0.1)),
        (40, 435, "Note: Clause1 specifications and Boeing747 delivery protocols apply.", "helv", 9, (0.4, 0.4, 0.4)),  # NEG-003, NEG-004
        # Footer at y=810 (valid A4 margin)
        (40, 810, "NORTHSTAR OFFICE SYSTEMS | INTERNAL REVIEW COPY                                Page 1", "helv", 8.5, (0.5, 0.5, 0.5))  # NEG-006
    ]

    # Draw table bounding box and grid dividers on Page 1
    page1.draw_rect(fitz.Rect(40, 300, 460, 420), color=(0.8, 0.8, 0.8), width=0.5)
    page1.draw_line(fitz.Point(40, 325), fitz.Point(460, 325), color=(0.7, 0.7, 0.7), width=1.0)
    page1.draw_line(fitz.Point(40, 350), fitz.Point(460, 350), color=(0.85, 0.85, 0.85), width=0.5)
    page1.draw_line(fitz.Point(40, 375), fitz.Point(460, 375), color=(0.85, 0.85, 0.85), width=0.5)
    page1.draw_line(fitz.Point(40, 400), fitz.Point(460, 400), color=(0.7, 0.7, 0.7), width=1.0)
    page1.draw_line(fitz.Point(180, 300), fitz.Point(180, 420), color=(0.85, 0.85, 0.85), width=0.5)
    page1.draw_line(fitz.Point(320, 300), fitz.Point(320, 420), color=(0.85, 0.85, 0.85), width=0.5)

    # Insert table cell texts
    page1.insert_text(fitz.Point(50, 318), "Region", fontname="hebo", fontsize=10, color=(0.1, 0.1, 0.1))
    page1.insert_text(fitz.Point(200, 318), "Installations", fontname="hebo", fontsize=10, color=(0.1, 0.1, 0.1))
    page1.insert_text(fitz.Point(340, 318), "Late jobs", fontname="hebo", fontsize=10, color=(0.1, 0.1, 0.1))

    page1.insert_text(fitz.Point(50, 342), "Coimbatore", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(200, 342), "52", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(340, 342), "6", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))

    page1.insert_text(fitz.Point(50, 367), "Erode", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(200, 367), "41", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(340, 367), "5", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))

    page1.insert_text(fitz.Point(50, 392), "Salem", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(200, 392), "35", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
    page1.insert_text(fitz.Point(340, 392), "6", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))

    page1.insert_text(fitz.Point(50, 415), "Total", fontname="hebo", fontsize=10, color=(0.1, 0.1, 0.1))
    page1.insert_text(fitz.Point(200, 415), "138", fontname="hebo", fontsize=10, color=(0.1, 0.1, 0.1))  # DEF-012 (138 vs 128), NEG-005 (17)
    page1.insert_text(fitz.Point(340, 415), "17", fontname="hebo", fontsize=10, color=(0.1, 0.1, 0.1))

    for x, y, text, font, size, col in p1_lines:
        page1.insert_text(fitz.Point(x, y), text, fontname=font, fontsize=size, color=col)

    # PAGE 2
    p2_lines = [
        (40, 50, "2. Operational Risk & Customer Quality", "hebo", 13, (0.1, 0.1, 0.1)),
        (40, 75, "The support desk handled 486 requests during the reporting period.", "helv", 10, (0.15, 0.15, 0.15)),
        (40, 95, "Customer feedback was collected through email,, phone calls and field visits.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-006: ,,
        (40, 115, "The team will continue to improve improve response consistency and documentation quality.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-004: improve improve
        (40, 135, "Regular maintainance schedules must be preserved across all enterprise hardware hubs.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-008: maintainance
        (40, 170, "Section 4. Risk and Follow-up Actions", "hebo", 12, (0.1, 0.1, 0.1)),  # DEF-015: jumped from Sec 2 to Sec 4
        (40, 195, "The review identified three operational risks: spare parts, asset records, and weekend support.", "helv", 10, (0.15, 0.15, 0.15)),
        (40, 215, "Each regional lead are responsible for submitting an action plan by mid-July.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-011: are
        (40, 250, "Company reference: This report was prepared by North Star Office Systems for official audit.", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-014: North Star Office Systems
        (40, 275, "Review date: 30 June 2026", "helv", 10, (0.15, 0.15, 0.15)),
        (40, 295, "Approval date: 12 June 2026", "helv", 10, (0.15, 0.15, 0.15)),  # DEF-013: 12 June precedes 30 June
        (40, 330, "End of Report.", "hebo", 11, (0.1, 0.1, 0.1)),
        # Footer at y=810 (valid A4 margin)
        (40, 810, "NORTHSTAR OFFICE SYSTEMS | INTERNAL REVIEW COPY                                Page 2", "helv", 8.5, (0.5, 0.5, 0.5))
    ]

    for x, y, text, font, size, col in p2_lines:
        page2.insert_text(fitz.Point(x, y), text, fontname=font, fontsize=size, color=col)

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()


def generate_synthetic_docx(output_path: str):
    """Generates synthetic Word document with identical defects."""
    doc = docx.Document()

    # Title & Metadata
    h = doc.add_heading("QUARTERLY OPERATIONS REVIEW", level=1)
    p_sub = doc.add_paragraph("Northstar Office Systems | Reporting period: 1 April 2026 - 30 June 2026")
    p_meta = doc.add_paragraph("Prepared for: Operations    Leadership Team")  # DEF-003
    p_meta2 = doc.add_paragraph("DocuMent ID: NOS-OPS-Q2-026 | Verified via SHA256 standard and ISO9001 clause")  # DEF-009, NEG-001, NEG-002

    # Executive Summary
    doc.add_heading("Executive Summary", level=2)
    doc.add_paragraph("Northstar Office Systems continued to expand regional service operations during the second quarter.")
    doc.add_paragraph("The operations manager confirmed that all regional teams was aligned with the revised service process.")  # DEF-010
    doc.add_paragraph("We will definately maintain this trajectory andthe service pipeline inaccordance with Q2 guidelines.")  # DEF-007, DEF-001, DEF-002
    doc.add_paragraph("The team monitored delivery performance , tracking installations and customer feedback.")  # DEF-005

    # Table 1
    doc.add_heading("1. Delivery Performance & Regional Summary", level=2)
    table = doc.add_table(rows=5, cols=3)
    table.style = 'Table Grid'
    headers = ["Region", "Installations", "Late jobs"]
    for i, title in enumerate(headers):
        table.rows[0].cells[i].text = title

    data = [
        ["Coimbatore", "52", "6"],
        ["Erode", "41", "5"],
        ["Salem", "35", "6"],
        ["Total", "138", "17"]  # DEF-012 (138 vs 128), NEG-005 (17)
    ]
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            table.rows[r_idx + 1].cells[c_idx].text = val

    doc.add_paragraph("Note: Clause1 specifications and Boeing747 delivery protocols apply.")  # NEG-003, NEG-004

    # Operational Quality
    doc.add_heading("2. Operational Risk & Customer Quality", level=2)
    doc.add_paragraph("Customer feedback was collected through email,, phone calls and field visits.")  # DEF-006
    doc.add_paragraph("The team will continue to improve improve response consistency and documentation quality.")  # DEF-004
    doc.add_paragraph("Regular maintainance schedules must be preserved across all enterprise hardware hubs.")  # DEF-008

    # Broken section
    doc.add_heading("Section 4. Risk and Follow-up Actions", level=2)  # DEF-015
    doc.add_paragraph("Each regional lead are responsible for submitting an action plan by mid-July.")  # DEF-011
    doc.add_paragraph("Company reference: This report was prepared by North Star Office Systems for official audit.")  # DEF-014
    doc.add_paragraph("Review date: 30 June 2026")
    doc.add_paragraph("Approval date: 12 June 2026")  # DEF-013

    # Footer
    section = doc.sections[0]
    footer = section.footer
    f_p = footer.paragraphs[0]
    f_p.text = "NORTHSTAR OFFICE SYSTEMS | INTERNAL REVIEW COPY"

    doc.save(output_path)


def generate_synthetic_pptx(output_path: str):
    """Generates synthetic PowerPoint presentation with identical defects."""
    prs = pptx.Presentation()
    # 16:9 widescreen layout
    prs.slide_width = PPTXInches(13.33)
    prs.slide_height = PPTXInches(7.5)
    blank_layout = prs.slide_layouts[6]

    # SLIDE 1
    s1 = prs.slides.add_slide(blank_layout)
    tb1 = s1.shapes.add_textbox(PPTXInches(1.0), PPTXInches(0.8), PPTXInches(11.3), PPTXInches(5.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "QUARTERLY OPERATIONS REVIEW"
    p.font.bold = True
    p.font.size = PPTXPt(24)

    p2 = tf1.add_paragraph()
    p2.text = "Prepared for: Operations    Leadership Team | DocuMent ID: NOS-OPS-Q2-026"  # DEF-003, DEF-009
    p2.font.size = PPTXPt(14)

    p3 = tf1.add_paragraph()
    p3.text = "The operations manager confirmed that all regional teams was aligned with process."  # DEF-010
    p3.font.size = PPTXPt(14)

    p4 = tf1.add_paragraph()
    p4.text = "We will definately maintain this trajectory andthe service pipeline inaccordance with rules."  # DEF-007, DEF-001, DEF-002
    p4.font.size = PPTXPt(14)

    p5 = tf1.add_paragraph()
    p5.text = "Delivery performance , with SHA256 security and ISO9001 compliance."  # DEF-005, NEG-001, NEG-002
    p5.font.size = PPTXPt(14)

    # Add table to Slide 1
    table_shape = s1.shapes.add_table(5, 3, PPTXInches(1.0), PPTXInches(3.8), PPTXInches(7.0), PPTXInches(2.2))
    table = table_shape.table
    table.cell(0, 0).text = "Region"
    table.cell(0, 1).text = "Installations"
    table.cell(0, 2).text = "Late jobs"
    rows_data = [
        ("Coimbatore", "52", "6"),
        ("Erode", "41", "5"),
        ("Salem", "35", "6"),
        ("Total", "138", "17")  # DEF-012, NEG-005
    ]
    for r_i, (c0, c1, c2) in enumerate(rows_data):
        table.cell(r_i + 1, 0).text = c0
        table.cell(r_i + 1, 1).text = c1
        table.cell(r_i + 1, 2).text = c2

    # SLIDE 2
    s2 = prs.slides.add_slide(blank_layout)
    tb2 = s2.shapes.add_textbox(PPTXInches(1.0), PPTXInches(0.8), PPTXInches(11.3), PPTXInches(5.5))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    sp1 = tf2.paragraphs[0]
    sp1.text = "OPERATIONAL RISK & CUSTOMER QUALITY"
    sp1.font.bold = True
    sp1.font.size = PPTXPt(24)

    sp2 = tf2.add_paragraph()
    sp2.text = "Customer feedback collected through email,, phone calls and field visits."  # DEF-006
    sp2.font.size = PPTXPt(14)

    sp3 = tf2.add_paragraph()
    sp3.text = "The team will continue to improve improve response consistency and documentation quality."  # DEF-004
    sp3.font.size = PPTXPt(14)

    sp4 = tf2.add_paragraph()
    sp4.text = "Regular maintainance schedules must be preserved across all enterprise hardware hubs."  # DEF-008
    sp4.font.size = PPTXPt(14)

    sp5 = tf2.add_paragraph()
    sp5.text = "Section 4. Risk and Follow-up Actions"  # DEF-015
    sp5.font.bold = True
    sp5.font.size = PPTXPt(18)

    sp6 = tf2.add_paragraph()
    sp6.text = "Each regional lead are responsible for submitting an action plan by mid-July."  # DEF-011
    sp6.font.size = PPTXPt(14)

    sp7 = tf2.add_paragraph()
    sp7.text = "Report prepared by North Star Office Systems for official audit."  # DEF-014
    sp7.font.size = PPTXPt(14)

    sp8 = tf2.add_paragraph()
    sp8.text = "Review date: 30 June 2026 | Approval date: 12 June 2026"  # DEF-013
    sp8.font.size = PPTXPt(14)

    prs.save(output_path)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "ground_truth_dataset.json")
    pdf_path = os.path.join(base_dir, "synthetic_test_doc.pdf")
    docx_path = os.path.join(base_dir, "synthetic_test_doc.docx")
    pptx_path = os.path.join(base_dir, "synthetic_test_doc.pptx")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(GROUND_TRUTH_DATASET, f, indent=2)
    print(f"Saved ground truth dataset JSON to {json_path}")

    generate_synthetic_pdf(pdf_path)
    print(f"Generated synthetic PDF at {pdf_path}")

    generate_synthetic_docx(docx_path)
    print(f"Generated synthetic DOCX at {docx_path}")

    generate_synthetic_pptx(pptx_path)
    print(f"Generated synthetic PPTX at {pptx_path}")


if __name__ == "__main__":
    main()

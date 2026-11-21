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

REALISTIC_BENCHMARK_DATASET = {
    "version": "2.0",
    "description": "RAVENX AI Phase 8 Real-World Accuracy Engine Ground Truth Benchmark Dataset",
    "documents": {
        "business_financial_report.pdf": {
            "format": "pdf",
            "type": "positive",
            "pages": 3,
            "defects": [
                {
                    "id": "BFR-001",
                    "category": "micro_typography",
                    "defect_type": "concatenated_words",
                    "original_text": "werealigned",
                    "expected_correction": "were aligned",
                    "page": 1,
                    "is_actionable": True
                },
                {
                    "id": "BFR-002",
                    "category": "micro_typography",
                    "defect_type": "split_word",
                    "original_text": "oper ation",
                    "expected_correction": "operation",
                    "page": 1,
                    "is_actionable": True
                },
                {
                    "id": "BFR-003",
                    "category": "micro_typography",
                    "defect_type": "punctuation_space",
                    "original_text": "Quarterly Performance ,",
                    "expected_correction": "Quarterly Performance,",
                    "page": 1,
                    "is_actionable": True
                },
                {
                    "id": "BFR-004",
                    "category": "micro_typography",
                    "defect_type": "standalone_i",
                    "original_text": "as i highlighted",
                    "expected_correction": "as I highlighted",
                    "page": 1,
                    "is_actionable": True
                },
                {
                    "id": "BFR-005",
                    "category": "table_arithmetic",
                    "defect_type": "sum_discrepancy",
                    "original_text": "Total Expenses: ₹80,000",
                    "expected_correction": "Total Expenses: ₹70,000",
                    "page": 2,
                    "is_actionable": True
                },
                {
                    "id": "BFR-006",
                    "category": "entity_consistency",
                    "defect_type": "organization_drift",
                    "original_text": "Apex Globel Ltd",
                    "expected_correction": "Apex Global Ltd",
                    "page": 3,
                    "is_actionable": True
                }
            ]
        },
        "academic_college_project.docx": {
            "format": "docx",
            "type": "positive",
            "pages": 1,
            "defects": [
                {
                    "id": "ACP-001",
                    "category": "micro_typography",
                    "defect_type": "split_word",
                    "original_text": "Docum ent",
                    "expected_correction": "Document",
                    "is_actionable": True
                },
                {
                    "id": "ACP-002",
                    "category": "grammar",
                    "defect_type": "double_comparative",
                    "original_text": "more better",
                    "expected_correction": "better",
                    "is_actionable": True
                },
                {
                    "id": "ACP-003",
                    "category": "grammar",
                    "defect_type": "missing_apostrophe",
                    "original_text": "dont",
                    "expected_correction": "don't",
                    "is_actionable": True
                },
                {
                    "id": "ACP-004",
                    "category": "micro_typography",
                    "defect_type": "repeated_word",
                    "original_text": "the the",
                    "expected_correction": "the",
                    "is_actionable": True
                },
                {
                    "id": "ACP-005",
                    "category": "spelling",
                    "defect_type": "misspelling",
                    "original_text": "definately",
                    "expected_correction": "definitely",
                    "is_actionable": True
                }
            ]
        },
        "corporate_strategy_deck.pptx": {
            "format": "pptx",
            "type": "positive",
            "slides": 3,
            "defects": [
                {
                    "id": "CSD-001",
                    "category": "micro_typography",
                    "defect_type": "excessive_spaces",
                    "original_text": "Market    Expansion",
                    "expected_correction": "Market Expansion",
                    "slide": 1,
                    "is_actionable": True
                },
                {
                    "id": "CSD-002",
                    "category": "grammar",
                    "defect_type": "repeated_phrase",
                    "original_text": "in order to in order to",
                    "expected_correction": "in order to",
                    "slide": 2,
                    "is_actionable": True
                },
                {
                    "id": "CSD-003",
                    "category": "micro_typography",
                    "defect_type": "concatenated_words",
                    "original_text": "hasbeen",
                    "expected_correction": "has been",
                    "slide": 2,
                    "is_actionable": True
                },
                {
                    "id": "CSD-004",
                    "category": "micro_typography",
                    "defect_type": "split_word",
                    "original_text": "strat egy",
                    "expected_correction": "strategy",
                    "slide": 3,
                    "is_actionable": True
                }
            ]
        },
        "clean_perfect_document.pdf": {
            "format": "pdf",
            "type": "negative",
            "pages": 2,
            "defects": []
        }
    }
}


def build_business_financial_pdf(output_path: str):
    doc = fitz.open()

    # Page 1: Title & Overview
    page1 = doc.new_page(width=595, height=842)  # A4
    page1.draw_rect(fitz.Rect(50, 40, 545, 42), fill=(0.1, 0.2, 0.4), color=(0.1, 0.2, 0.4))
    page1.insert_text(fitz.Point(50, 75), "Apex Global Ltd", fontsize=18, fontname="hebo", color=(0.1, 0.1, 0.2))
    page1.insert_text(fitz.Point(50, 100), "Annual Strategic & Financial Audit Report 2026", fontsize=14, fontname="helv", color=(0.2, 0.2, 0.3))

    p1_lines = [
        ("Executive Summary and Operational Review", 12, True, 135),
        ("This official report provides the comprehensive corporate review for the fiscal period.", 10, False, 160),
        ("During this cycle, internal teams werealigned across critical product initiatives.", 10, False, 180),  # werealigned
        ("The overall field oper ation demonstrated resilient progress despite market pressure.", 10, False, 200),  # oper ation
        ("In our Quarterly Performance , revenue exceeded baseline expectations.", 10, False, 220),  # Performance ,
        ("Furthermore, as i highlighted during the shareholder address, discipline is vital.", 10, False, 240),  # as i highlighted
        ("All capital projects were conducted in accordance with statutory guidelines.", 10, False, 260)
    ]
    for text, sz, is_bold, y in p1_lines:
        fname = "hebo" if is_bold else "helv"
        page1.insert_text(fitz.Point(50, y), text, fontsize=sz, fontname=fname, color=(0.15, 0.15, 0.15))
    page1.insert_text(fitz.Point(280, 810), "Page 1 of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 2: Financial Table with Discrepancy
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text(fitz.Point(50, 60), "Fiscal Financial Expenditure Breakdown", fontsize=14, fontname="hebo", color=(0.1, 0.1, 0.2))

    # Draw Table
    # Row headers
    page2.draw_rect(fitz.Rect(50, 90, 545, 115), fill=(0.92, 0.94, 0.98), color=(0.7, 0.7, 0.8))
    page2.insert_text(fitz.Point(60, 107), "Category", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    page2.insert_text(fitz.Point(300, 107), "Allocated (INR)", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    # Row 1: 15,000
    page2.draw_rect(fitz.Rect(50, 115, 545, 140), color=(0.85, 0.85, 0.85))
    page2.insert_text(fitz.Point(60, 132), "Infrastructure & Hosting", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(300, 132), "15,000", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))

    # Row 2: 25,000
    page2.draw_rect(fitz.Rect(50, 140, 545, 165), color=(0.85, 0.85, 0.85))
    page2.insert_text(fitz.Point(60, 157), "Research & Intelligence", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(300, 157), "25,000", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))

    # Row 3: 30,000
    page2.draw_rect(fitz.Rect(50, 165, 545, 190), color=(0.85, 0.85, 0.85))
    page2.insert_text(fitz.Point(60, 182), "Operational Logistics", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(300, 182), "30,000", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))

    # Row 4: Total row with arithmetic defect (15000+25000+30000 = 70,000, but stated 80,000)
    page2.draw_rect(fitz.Rect(50, 190, 545, 215), fill=(0.95, 0.95, 0.97), color=(0.7, 0.7, 0.8))
    page2.insert_text(fitz.Point(60, 207), "Total Expenses", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    page2.insert_text(fitz.Point(300, 207), "80,000", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    page2.insert_text(fitz.Point(50, 250), "Notes: Budget figures are expressed in net terms.", fontsize=9, fontname="heit", color=(0.4, 0.4, 0.4))
    page2.insert_text(fitz.Point(280, 810), "Page 2 of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 3: Organization drift & Signoff
    page3 = doc.new_page(width=595, height=842)
    page3.insert_text(fitz.Point(50, 60), "Governance & Authorization", fontsize=14, fontname="hebo", color=(0.1, 0.1, 0.2))
    page3.insert_text(fitz.Point(50, 95), "Signed on behalf of Apex Globel Ltd by the managing board.", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))  # Apex Globel Ltd
    page3.insert_text(fitz.Point(50, 120), "Date of ratification: 15 October 2026.", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    page3.insert_text(fitz.Point(280, 810), "Page 3 of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(output_path)
    doc.close()


def build_academic_college_docx(output_path: str):
    doc = docx.Document()
    title = doc.add_paragraph()
    t_run = title.add_run("Deep Neural Architecture for Document Classification")
    t_run.font.size = Pt(18)
    t_run.font.bold = True
    t_run.font.color.rgb = RGBColor(30, 45, 90)

    # Paragraph with split word "Docum ent"
    p1 = doc.add_paragraph()
    p1.add_run("This research project presents an autonomous framework for digital processing. ")
    p1.add_run("The central goal of the Docum ent pipeline is high-fidelity text extraction.")

    # Paragraph with double comparative "more better" and contraction "dont"
    p2 = doc.add_paragraph()
    p2.add_run("Experimental benchmarks show that transformer representations are ")
    p2.add_run("more better than classical baseline models. ")
    p2.add_run("Researchers dont need to rely on static heuristic features.")

    # Paragraph with multi-run split spelling mistake "definately"
    p3 = doc.add_paragraph()
    r_start = p3.add_run("The validation curves prove that model convergence was ")
    r_sp = p3.add_run("definately")  # Targeted misspelled token
    r_sp.font.bold = True  # Distinct run formatting to test multi-run preservation
    r_end = p3.add_run(" superior to standard stochastic gradient descent.")

    # Paragraph with repeated word "the the"
    p4 = doc.add_paragraph()
    p4.add_run("In our comparative tests, the the accuracy improved by 14.2% across benchmarks.")

    doc.save(output_path)


def build_corporate_strategy_pptx(output_path: str):
    prs = pptx.Presentation()
    prs.slide_width = PPTXInches(10)
    prs.slide_height = PPTXInches(5.625)  # 16:9
    blank_layout = prs.slide_layouts[6]

    # Slide 1: Title with excessive spaces
    s1 = prs.slides.add_slide(blank_layout)
    txBox = s1.shapes.add_textbox(PPTXInches(1), PPTXInches(1.5), PPTXInches(8), PPTXInches(2))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Market    Expansion Strategy 2026"  # Excessive spaces
    p.font.size = PPTXPt(32)
    p.font.bold = True
    p.font.color.rgb = PPTXRGBColor(25, 40, 80)

    p2 = tf.add_paragraph()
    p2.text = "Corporate Strategic Planning & Global Realignment"
    p2.font.size = PPTXPt(18)
    p2.font.color.rgb = PPTXRGBColor(90, 90, 100)

    # Slide 2: Repeated phrase & concatenated word
    s2 = prs.slides.add_slide(blank_layout)
    tb2 = s2.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    tf2 = tb2.text_frame
    p_h2 = tf2.paragraphs[0]
    p_h2.text = "Operational Alignment and Execution"
    p_h2.font.size = PPTXPt(24)
    p_h2.font.bold = True

    p_b2 = tf2.add_paragraph()
    p_b2.text = "We are streamlining key operations in order to in order to maximize productivity."
    p_b2.font.size = PPTXPt(16)

    p_b3 = tf2.add_paragraph()
    p_b3.text = "The strategic realignment hasbeen adopted across all business departments."
    p_b3.font.size = PPTXPt(16)

    # Slide 3: Split word
    s3 = prs.slides.add_slide(blank_layout)
    tb3 = s3.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    tf3 = tb3.text_frame
    p_h3 = tf3.paragraphs[0]
    p_h3.text = "Next Steps and Forward Roadmap"
    p_h3.font.size = PPTXPt(24)
    p_h3.font.bold = True

    p_b4 = tf3.add_paragraph()
    p_b4.text = "Our long-term strat egy ensures continuous sustainable revenue growth."
    p_b4.font.size = PPTXPt(16)

    prs.save(output_path)


def build_clean_perfect_pdf(output_path: str):
    doc = fitz.open()

    # Page 1: Flawless executive document
    page1 = doc.new_page(width=595, height=842)
    page1.draw_rect(fitz.Rect(50, 40, 545, 42), fill=(0.1, 0.3, 0.5), color=(0.1, 0.3, 0.5))
    page1.insert_text(fitz.Point(50, 75), "Quantum Research Institute", fontsize=18, fontname="hebo", color=(0.1, 0.1, 0.2))
    page1.insert_text(fitz.Point(50, 100), "Quarterly Scientific Briefing and Governance Report", fontsize=13, fontname="helv", color=(0.2, 0.2, 0.3))

    clean_lines_p1 = [
        "Executive Summary",
        "This official briefing summarizes ongoing research initiatives in computational optics.",
        "All projects have maintained rigorous engineering standards and met planned milestones.",
        "The collaborative experiments conducted during the quarter yielded positive outcomes.",
        "Resource allocations adhere strictly to approved budgetary allocations."
    ]
    y = 135
    for idx, line in enumerate(clean_lines_p1):
        is_bold = (idx == 0)
        fname = "hebo" if is_bold else "helv"
        sz = 12 if is_bold else 10
        page1.insert_text(fitz.Point(50, y), line, fontsize=sz, fontname=fname, color=(0.15, 0.15, 0.15))
        y += 24
    page1.insert_text(fitz.Point(280, 810), "Page 1 of 2", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 2: Flawless table & notes
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text(fitz.Point(50, 60), "Approved Resource Distribution", fontsize=14, fontname="hebo", color=(0.1, 0.1, 0.2))

    page2.draw_rect(fitz.Rect(50, 90, 545, 115), fill=(0.92, 0.94, 0.98), color=(0.7, 0.7, 0.8))
    page2.insert_text(fitz.Point(60, 107), "Division", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    page2.insert_text(fitz.Point(300, 107), "Allocation", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    page2.draw_rect(fitz.Rect(50, 115, 545, 140), color=(0.85, 0.85, 0.85))
    page2.insert_text(fitz.Point(60, 132), "Optical Systems Laboratory", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(300, 132), "50,000", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))

    page2.draw_rect(fitz.Rect(50, 140, 545, 165), color=(0.85, 0.85, 0.85))
    page2.insert_text(fitz.Point(60, 157), "Theoretical Physics Unit", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(300, 157), "50,000", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))

    # Accurate sum: 50,000 + 50,000 = 100,000
    page2.draw_rect(fitz.Rect(50, 165, 545, 190), fill=(0.95, 0.95, 0.97), color=(0.7, 0.7, 0.8))
    page2.insert_text(fitz.Point(60, 182), "Total Allocation", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    page2.insert_text(fitz.Point(300, 182), "100,000", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    page2.insert_text(fitz.Point(50, 230), "Report certified by the Academic Review Board on 12 October 2026.", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(280, 810), "Page 2 of 2", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(output_path)
    doc.close()


def generate_all_realistic_benchmarks(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)

    pdf_path = os.path.join(target_dir, "business_financial_report.pdf")
    docx_path = os.path.join(target_dir, "academic_college_project.docx")
    pptx_path = os.path.join(target_dir, "corporate_strategy_deck.pptx")
    clean_pdf_path = os.path.join(target_dir, "clean_perfect_document.pdf")
    json_path = os.path.join(target_dir, "realistic_benchmark_dataset.json")

    build_business_financial_pdf(pdf_path)
    build_academic_college_docx(docx_path)
    build_corporate_strategy_pptx(pptx_path)
    build_clean_perfect_pdf(clean_pdf_path)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(REALISTIC_BENCHMARK_DATASET, f, indent=2)

    print(f"Generated realistic benchmark documents in {target_dir}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generate_all_realistic_benchmarks(current_dir)

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

PHASE9_BENCHMARK_DATASET = {
    "version": "3.0",
    "description": "RAVENX AI Phase 9 Real-World Reliability & Generalization Benchmark Dataset",
    "documents": {
        "phase9_financial_multipage.pdf": {
            "format": "pdf",
            "type": "positive",
            "pages": 3,
            "expected_defects": [
                {"id": "P9-PDF-001", "type": "concatenated_words", "original": "werealigned", "expected": "were aligned", "page": 1},
                {"id": "P9-PDF-002", "type": "split_word", "original": "oper ation", "expected": "operation", "page": 1},
                {"id": "P9-PDF-003", "type": "punctuation_spacing", "original": "Quarterly Performance ,", "expected": "Quarterly Performance,", "page": 1},
                {"id": "P9-PDF-004", "type": "table_arithmetic", "original": "8,00,000", "expected": "7,50,000", "page": 2},
                {"id": "P9-PDF-005", "type": "narrative_variance", "original": "25,000", "expected": "40,000", "page": 2},
                {"id": "P9-PDF-006", "type": "organization_drift", "original": "Apex Globel Ltd", "expected": "Apex Global Ltd", "page": 3}
            ],
            "negative_cases": [
                "Document ID: APEX-FIN-2026",
                "ISO-9001:2015",
                "Section 1.2"
            ]
        },
        "phase9_academic_report.pdf": {
            "format": "pdf",
            "type": "positive",
            "pages": 2,
            "expected_defects": [
                {"id": "P9-ACAD-001", "type": "double_comparative", "original": "more better", "expected": "better", "page": 1},
                {"id": "P9-ACAD-002", "type": "missing_apostrophe", "original": "dont", "expected": "don't", "page": 1},
                {"id": "P9-ACAD-003", "type": "repeated_word", "original": "the the", "expected": "the", "page": 2},
                {"id": "P9-ACAD-004", "type": "pronoun_i", "original": "i", "expected": "I", "page": 2}
            ],
            "negative_cases": [
                "Figure 1: Architecture",
                "Algorithm 2",
                "Table 1"
            ]
        },
        "phase9_clean_executive_brief.pdf": {
            "format": "pdf",
            "type": "negative",
            "pages": 2,
            "expected_defects": [],
            "negative_cases": [
                "Boeing 747",
                "ISO 27001",
                "Total: 100,000",
                "Prepared for: Board of Directors    Document ID: BOD-2026-01"
            ]
        },
        "phase9_contract_agreement.docx": {
            "format": "docx",
            "type": "positive",
            "pages": 1,
            "expected_defects": [
                {"id": "P9-DOCX-001", "type": "split_word", "original": "Docum ent", "expected": "Document"},
                {"id": "P9-DOCX-002", "type": "spelling", "original": "definately", "expected": "definitely"},
                {"id": "P9-DOCX-003", "type": "missing_apostrophe", "original": "cant", "expected": "can't"},
                {"id": "P9-DOCX-004", "type": "repeated_word", "original": "shall shall", "expected": "shall"}
            ],
            "negative_cases": [
                "Clause 4.1",
                "Schedule A",
                "Party A and Party B"
            ]
        },
        "phase9_clean_corporate_policy.docx": {
            "format": "docx",
            "type": "negative",
            "pages": 1,
            "expected_defects": [],
            "negative_cases": [
                "Section 1",
                "Appendix 2",
                "Policy ID: POL-2026"
            ]
        },
        "phase9_board_presentation.pptx": {
            "format": "pptx",
            "type": "positive",
            "slides": 4,
            "expected_defects": [
                {"id": "P9-PPTX-001", "type": "excessive_spaces", "original": "Market    Expansion", "expected": "Market Expansion", "slide": 1},
                {"id": "P9-PPTX-002", "type": "repeated_phrase", "original": "in order to in order to", "expected": "in order to", "slide": 2},
                {"id": "P9-PPTX-003", "type": "concatenated_words", "original": "hasbeen", "expected": "has been", "slide": 3},
                {"id": "P9-PPTX-004", "type": "split_word", "original": "strat egy", "expected": "strategy", "slide": 4}
            ],
            "negative_cases": [
                "Slide 1 of 4",
                "Q2 Roadmap",
                "Target: 15% CAGR"
            ]
        },
        "phase9_clean_keynote.pptx": {
            "format": "pptx",
            "type": "negative",
            "slides": 3,
            "expected_defects": [],
            "negative_cases": [
                "Vision 2030",
                "3 Pillars of Growth"
            ]
        }
    }
}


def build_phase9_financial_pdf(output_path: str):
    doc = fitz.open()

    # Page 1: Overview
    p1 = doc.new_page(width=595, height=842)
    p1.draw_rect(fitz.Rect(50, 40, 545, 42), fill=(0.1, 0.2, 0.45), color=(0.1, 0.2, 0.45))
    p1.insert_text(fitz.Point(50, 75), "Apex Global Ltd", fontsize=18, fontname="hebo", color=(0.1, 0.1, 0.2))
    p1.insert_text(fitz.Point(50, 95), "Quarterly Financial Audit & Performance Review 2026", fontsize=12, fontname="helv", color=(0.3, 0.3, 0.4))

    # Header with wide inter-field spacing (must be preserved!)
    p1.insert_text(fitz.Point(50, 120), "Prepared for: Executive Committee    Document ID: APEX-FIN-2026", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.3))

    p1_lines = [
        ("Executive Summary", 12, True, 150),
        ("This document summarizes financial and operational indicators for the fiscal period.", 10, False, 175),
        ("Internal development teams werealigned across high-priority platform services.", 10, False, 200),  # werealigned
        ("The regional field oper ation achieved record delivery milestones.", 10, False, 225),  # oper ation
        ("In our Quarterly Performance , revenue exceeded baseline projections.", 10, False, 250),  # Performance ,
        ("All internal quality audits strictly comply with ISO-9001:2015 certification guidelines.", 10, False, 275)  # Negative case
    ]
    for text, sz, is_bold, y in p1_lines:
        fname = "hebo" if is_bold else "helv"
        p1.insert_text(fitz.Point(50, y), text, fontsize=sz, fontname=fname, color=(0.15, 0.15, 0.15))
    p1.insert_text(fitz.Point(270, 810), "Page 1 of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 2: Shaded Table with Rupee symbols and calculation discrepancy
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(fitz.Point(50, 60), "2. Operating Expenditure Breakdown", fontsize=14, fontname="hebo", color=(0.1, 0.1, 0.2))

    # Narrative variance: Budget ₹8,50,000, Actual ₹8,90,000, overrun stated 25,000 (calculated 40,000)
    p2.insert_text(fitz.Point(50, 90), "The approved operating budget for Q2 was ₹8,50,000. Actual expenditure was ₹8,90,000, resulting in an overrun of", fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
    p2.insert_text(fitz.Point(50, 108), "₹25,000. The management team will adjust discretionary spending during Q3.", fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))

    # Draw Shaded Table
    # Header: Dark header
    p2.draw_rect(fitz.Rect(50, 135, 545, 160), fill=(0.18, 0.22, 0.32), color=(0.18, 0.22, 0.32))
    p2.insert_text(fitz.Point(60, 152), "Expense Category", fontsize=10, fontname="hebo", color=(1.0, 1.0, 1.0))
    p2.insert_text(fitz.Point(350, 152), "Allocated Amount (₹)", fontsize=10, fontname="hebo", color=(1.0, 1.0, 1.0))

    # Row 1: Shaded row #F0F4F8 (0.941, 0.957, 0.973)
    p2.draw_rect(fitz.Rect(50, 160, 545, 185), fill=(0.941, 0.957, 0.973), color=(0.85, 0.88, 0.92))
    p2.insert_text(fitz.Point(60, 177), "Core Infrastructure & Cloud", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
    p2.insert_text(fitz.Point(350, 177), "3,00,000", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    # Row 2: White row
    p2.draw_rect(fitz.Rect(50, 185, 545, 210), fill=(1.0, 1.0, 1.0), color=(0.85, 0.88, 0.92))
    p2.insert_text(fitz.Point(60, 202), "Field Logistics & Transport", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
    p2.insert_text(fitz.Point(350, 202), "2,00,000", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    # Row 3: Shaded row
    p2.draw_rect(fitz.Rect(50, 210, 545, 235), fill=(0.941, 0.957, 0.973), color=(0.85, 0.88, 0.92))
    p2.insert_text(fitz.Point(60, 227), "Technical Research", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
    p2.insert_text(fitz.Point(350, 227), "2,50,000", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    # Row 4: Shaded Total row (Tinted #E8EDF5 -> 0.910, 0.929, 0.961)
    # Sum: 300000 + 200000 + 250000 = 7,50,000, stated: 8,00,000
    p2.draw_rect(fitz.Rect(50, 235, 545, 260), fill=(0.910, 0.929, 0.961), color=(0.75, 0.8, 0.88))
    p2.insert_text(fitz.Point(60, 252), "Total Expenditure", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    p2.insert_text(fitz.Point(350, 252), "8,00,000", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    # Gridlines to ensure crisp tabular geometry and reliable table detection
    p2.draw_line(fitz.Point(50, 160), fitz.Point(545, 160), color=(0.75, 0.8, 0.88))
    p2.draw_line(fitz.Point(50, 185), fitz.Point(545, 185), color=(0.75, 0.8, 0.88))
    p2.draw_line(fitz.Point(50, 210), fitz.Point(545, 210), color=(0.75, 0.8, 0.88))
    p2.draw_line(fitz.Point(50, 235), fitz.Point(545, 235), color=(0.75, 0.8, 0.88))
    p2.draw_line(fitz.Point(340, 135), fitz.Point(340, 260), color=(0.75, 0.8, 0.88))

    p2.insert_text(fitz.Point(50, 290), "Section 1.2: All figures are subject to quarterly audit.", fontsize=9, fontname="heit", color=(0.4, 0.4, 0.4))
    p2.insert_text(fitz.Point(270, 810), "Page 2 of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 3: Organization name drift
    p3 = doc.new_page(width=595, height=842)
    p3.insert_text(fitz.Point(50, 60), "3. Authorization and Governance", fontsize=14, fontname="hebo", color=(0.1, 0.1, 0.2))
    p3.insert_text(fitz.Point(50, 95), "Signed on behalf of Apex Globel Ltd by the managing director.", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))  # Apex Globel Ltd
    p3.insert_text(fitz.Point(50, 120), "Date of ratification: 15 October 2026.", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    p3.insert_text(fitz.Point(270, 810), "Page 3 of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(output_path)
    doc.close()


def build_phase9_academic_pdf(output_path: str):
    doc = fitz.open()

    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(fitz.Point(50, 70), "Comparative Evaluation of Transformer Neural Models", fontsize=16, fontname="times-bold", color=(0.1, 0.1, 0.1))
    p1.insert_text(fitz.Point(50, 95), "Department of Computer Science & Engineering", fontsize=11, fontname="times-roman", color=(0.3, 0.3, 0.3))

    p1_lines = [
        ("Abstract", 12, True, 130),
        ("This study investigates natural language processing benchmarks across document pipelines.", 10, False, 155),
        ("Empirical findings indicate that fine-tuned transformer weights are more better than baselines.", 10, False, 180),  # more better
        ("Modern researchers dont need to rely on static hand-crafted n-gram features.", 10, False, 205),  # dont
        ("Figure 1: Architecture overview depicts the recurrent feedback mechanism.", 10, False, 230)  # Negative case
    ]
    for text, sz, is_bold, y in p1_lines:
        fname = "times-bold" if is_bold else "times-roman"
        p1.insert_text(fitz.Point(50, y), text, fontsize=sz, fontname=fname, color=(0.15, 0.15, 0.15))
    p1.insert_text(fitz.Point(270, 810), "Page 1 of 2", fontsize=9, fontname="times-roman", color=(0.5, 0.5, 0.5))

    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(fitz.Point(50, 60), "Methodology and Validation", fontsize=14, fontname="times-bold", color=(0.1, 0.1, 0.1))

    p2_lines = [
        ("Across all experimental runs, the the convergence score improved significantly.", 10, False, 90),  # the the
        ("Furthermore, as i demonstrated during the thesis seminar, latency remains sub-10ms.", 10, False, 115),  # as i demonstrated
        ("Table 1 summarizes the cross-validation loss metrics across five seeds.", 10, False, 140)  # Negative case
    ]
    for text, sz, is_bold, y in p2_lines:
        fname = "times-bold" if is_bold else "times-roman"
        p2.insert_text(fitz.Point(50, y), text, fontsize=sz, fontname=fname, color=(0.15, 0.15, 0.15))
    p2.insert_text(fitz.Point(270, 810), "Page 2 of 2", fontsize=9, fontname="times-roman", color=(0.5, 0.5, 0.5))

    doc.save(output_path)
    doc.close()


def build_phase9_clean_pdf(output_path: str):
    doc = fitz.open()

    p1 = doc.new_page(width=595, height=842)
    p1.draw_rect(fitz.Rect(50, 40, 545, 42), fill=(0.15, 0.25, 0.4), color=(0.15, 0.25, 0.4))
    p1.insert_text(fitz.Point(50, 75), "Global Standards Institute", fontsize=18, fontname="hebo", color=(0.1, 0.1, 0.2))
    p1.insert_text(fitz.Point(50, 95), "Executive Briefing: Aerospace & Cybersecurity Compliance", fontsize=12, fontname="helv", color=(0.3, 0.3, 0.4))

    # Header with wide separation
    p1.insert_text(fitz.Point(50, 120), "Prepared for: Board of Directors    Document ID: BOD-2026-01", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.3))

    clean_lines_p1 = [
        "Executive Summary",
        "This official briefing certifies enterprise adherence to international technical standards.",
        "Fleet operators of the Boeing 747 maintain regular airworthiness inspections without exception.",
        "Our digital infrastructure complies rigorously with ISO 27001 data protection protocols.",
        "Audit results from independent reviewers confirm all criteria are fully satisfied."
    ]
    y = 150
    for idx, line in enumerate(clean_lines_p1):
        is_bold = (idx == 0)
        fname = "hebo" if is_bold else "helv"
        sz = 12 if is_bold else 10
        p1.insert_text(fitz.Point(50, y), line, fontsize=sz, fontname=fname, color=(0.15, 0.15, 0.15))
        y += 25
    p1.insert_text(fitz.Point(270, 810), "Page 1 of 2", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(fitz.Point(50, 60), "Resource Allocation Summary", fontsize=14, fontname="hebo", color=(0.1, 0.1, 0.2))

    # Clean table with exact sum: 50,000 + 50,000 = 100,000
    p2.draw_rect(fitz.Rect(50, 85, 545, 110), fill=(0.92, 0.94, 0.98), color=(0.7, 0.7, 0.8))
    p2.insert_text(fitz.Point(60, 102), "Division", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    p2.insert_text(fitz.Point(350, 102), "Budget", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    p2.draw_rect(fitz.Rect(50, 110, 545, 135), fill=(1.0, 1.0, 1.0), color=(0.85, 0.85, 0.85))
    p2.insert_text(fitz.Point(60, 127), "Avionics Safety Laboratory", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
    p2.insert_text(fitz.Point(350, 127), "50,000", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    p2.draw_rect(fitz.Rect(50, 135, 545, 160), fill=(1.0, 1.0, 1.0), color=(0.85, 0.85, 0.85))
    p2.insert_text(fitz.Point(60, 152), "Cryptographic Operations", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
    p2.insert_text(fitz.Point(350, 152), "50,000", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    # Accurate Total row
    p2.draw_rect(fitz.Rect(50, 160, 545, 185), fill=(0.94, 0.95, 0.97), color=(0.7, 0.7, 0.8))
    p2.insert_text(fitz.Point(60, 177), "Total", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))
    p2.insert_text(fitz.Point(350, 177), "100,000", fontsize=10, fontname="hebo", color=(0.1, 0.1, 0.2))

    p2.insert_text(fitz.Point(50, 220), "Certification confirmed on 12 November 2026.", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    p2.insert_text(fitz.Point(270, 810), "Page 2 of 2", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(output_path)
    doc.close()


def build_phase9_contract_docx(output_path: str):
    doc = docx.Document()
    title = doc.add_paragraph()
    r = title.add_run("Master Professional Services Agreement")
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(20, 35, 75)

    p1 = doc.add_paragraph()
    p1.add_run("This Agreement is entered into by Party A and Party B. ")
    p1.add_run("The governing terms of this Docum ent specify operational deliverables.")  # Docum ent

    p2 = doc.add_paragraph()
    p2.add_run("Under Clause 4.1, all software deliverables are ")
    r_def = p2.add_run("definately")  # definately (with bold style to test multi-run)
    r_def.font.bold = True
    r_def.font.color.rgb = RGBColor(180, 20, 20)
    p2.add_run(" subject to rigorous integration acceptance testing.")

    p3 = doc.add_paragraph()
    p3.add_run("Neither party cant waive contractual covenants without prior written approval. ")  # cant
    p3.add_run("Both contractors shall shall maintain active liability insurance coverage.")  # shall shall

    doc.save(output_path)


def build_phase9_clean_docx(output_path: str):
    doc = docx.Document()
    title = doc.add_paragraph()
    r = title.add_run("Corporate Governance Policy")
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(20, 35, 75)

    p1 = doc.add_paragraph()
    p1.add_run("Section 1: General Code of Professional Conduct. ")
    p1.add_run("All enterprise employees must adhere strictly to established ethical guidelines.")

    p2 = doc.add_paragraph()
    p2.add_run("Under Appendix 2, the compliance committee reviews operational filings quarterly. ")
    p2.add_run("All records are archived under Policy ID: POL-2026.")

    doc.save(output_path)


def build_phase9_board_pptx(output_path: str):
    prs = pptx.Presentation()
    prs.slide_width = PPTXInches(10)
    prs.slide_height = PPTXInches(5.625)
    blank_layout = prs.slide_layouts[6]

    # Slide 1: Title with excessive spaces
    s1 = prs.slides.add_slide(blank_layout)
    tb1 = s1.shapes.add_textbox(PPTXInches(1), PPTXInches(1.5), PPTXInches(8), PPTXInches(2))
    p1 = tb1.text_frame.paragraphs[0]
    p1.text = "Market    Expansion Strategy 2026"  # Excessive spaces
    p1.font.size = PPTXPt(32)
    p1.font.bold = True

    # Slide 2: Repeated phrase
    s2 = prs.slides.add_slide(blank_layout)
    tb2 = s2.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    p2_h = tb2.text_frame.paragraphs[0]
    p2_h.text = "Operational Excellence"
    p2_h.font.size = PPTXPt(24)
    p2_b = tb2.text_frame.add_paragraph()
    p2_b.text = "We are streamlining workflows in order to in order to reduce cycle latency."
    p2_b.font.size = PPTXPt(16)

    # Slide 3: Concatenated word
    s3 = prs.slides.add_slide(blank_layout)
    tb3 = s3.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    p3_h = tb3.text_frame.paragraphs[0]
    p3_h.text = "Adoption Metrics"
    p3_h.font.size = PPTXPt(24)
    p3_b = tb3.text_frame.add_paragraph()
    p3_b.text = "The revised architecture hasbeen integrated across enterprise regions."
    p3_b.font.size = PPTXPt(16)

    # Slide 4: Split word
    s4 = prs.slides.add_slide(blank_layout)
    tb4 = s4.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    p4_h = tb4.text_frame.paragraphs[0]
    p4_h.text = "Growth Horizon"
    p4_h.font.size = PPTXPt(24)
    p4_b = tb4.text_frame.add_paragraph()
    p4_b.text = "Our sustainable strat egy targets a 15% CAGR across international markets."
    p4_b.font.size = PPTXPt(16)

    prs.save(output_path)


def build_phase9_clean_pptx(output_path: str):
    prs = pptx.Presentation()
    prs.slide_width = PPTXInches(10)
    prs.slide_height = PPTXInches(5.625)
    blank_layout = prs.slide_layouts[6]

    # Slide 1: Clean title
    s1 = prs.slides.add_slide(blank_layout)
    tb1 = s1.shapes.add_textbox(PPTXInches(1), PPTXInches(1.5), PPTXInches(8), PPTXInches(2))
    p1 = tb1.text_frame.paragraphs[0]
    p1.text = "Vision 2030 Keynote"
    p1.font.size = PPTXPt(32)
    p1.font.bold = True

    # Slide 2: Clean content
    s2 = prs.slides.add_slide(blank_layout)
    tb2 = s2.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    p2_h = tb2.text_frame.paragraphs[0]
    p2_h.text = "3 Pillars of Growth"
    p2_h.font.size = PPTXPt(24)
    p2_b = tb2.text_frame.add_paragraph()
    p2_b.text = "1. Customer Obsession  2. Operational Agility  3. Continuous Innovation"
    p2_b.font.size = PPTXPt(16)

    # Slide 3: Clean roadmap
    s3 = prs.slides.add_slide(blank_layout)
    tb3 = s3.shapes.add_textbox(PPTXInches(1), PPTXInches(1), PPTXInches(8), PPTXInches(3))
    p3_h = tb3.text_frame.paragraphs[0]
    p3_h.text = "Q2 Roadmap"
    p3_h.font.size = PPTXPt(24)
    p3_b = tb3.text_frame.add_paragraph()
    p3_b.text = "All deliverables are on track for global launch."
    p3_b.font.size = PPTXPt(16)

    prs.save(output_path)


def generate_all_phase9_benchmarks(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)

    build_phase9_financial_pdf(os.path.join(target_dir, "phase9_financial_multipage.pdf"))
    build_phase9_academic_pdf(os.path.join(target_dir, "phase9_academic_report.pdf"))
    build_phase9_clean_pdf(os.path.join(target_dir, "phase9_clean_executive_brief.pdf"))
    build_phase9_contract_docx(os.path.join(target_dir, "phase9_contract_agreement.docx"))
    build_phase9_clean_docx(os.path.join(target_dir, "phase9_clean_corporate_policy.docx"))
    build_phase9_board_pptx(os.path.join(target_dir, "phase9_board_presentation.pptx"))
    build_phase9_clean_pptx(os.path.join(target_dir, "phase9_clean_keynote.pptx"))

    dataset_path = os.path.join(target_dir, "phase9_benchmark_dataset.json")
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(PHASE9_BENCHMARK_DATASET, f, indent=2)

    print(f"Generated 7 Phase 9 benchmark documents and dataset inventory in {target_dir}")


if __name__ == "__main__":
    curr = os.path.dirname(os.path.abspath(__file__))
    generate_all_phase9_benchmarks(curr)

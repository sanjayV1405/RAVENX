import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic 'Page X of Y' numbering and running enterprise headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#DC2626"))
        self.drawString(54, 750, "RAVENX AI")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(108, 750, "|   CONFIDENTIAL AUDIT DOSSIER   |   Intelligence That Sees What Others Miss.")

        # Header rule
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Footer rule
        self.line(54, 45, 558, 45)

        # Footer text
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 34, "RAVENX AI Document Quality Inspection Platform  •  Zero Auto-Modification Guarantee")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 34, page_str)
        self.restoreState()


class AuditReportPDFGenerator:
    """Enterprise PDF Audit Report Generator using ReportLab."""

    SEVERITY_COLORS = {
        "critical": colors.HexColor("#DC2626"),
        "high": colors.HexColor("#EA580C"),
        "medium": colors.HexColor("#D97706"),
        "low": colors.HexColor("#2563EB"),
        "info": colors.HexColor("#64748B")
    }

    @classmethod
    def generate(
        cls,
        document_info: Dict[str, Any],
        inspection_info: Dict[str, Any],
        findings: List[Dict[str, Any]],
        requirements_assessment: Optional[Dict[str, Any]] = None,
        comparison_info: Optional[Dict[str, Any]] = None,
        include_excerpts: bool = True
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#090A0D")
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#DC2626")
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        mono_style = ParagraphStyle(
            "MonoMeta",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569")
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0F172A")
        )
        cell_body = ParagraphStyle(
            "CellBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155")
        )

        elements = []

        # 1. Cover Header
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("RAVENX AI DOCUMENT AUDIT REPORT", title_style))
        elements.append(Paragraph("Intelligence That Sees What Others Miss.", subtitle_style))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#DC2626"), spaceBefore=2, spaceAfter=14))

        # 2. Document & Audit Metadata Table
        meta_data = [
            [
                Paragraph("<b>Document Name:</b>", cell_bold),
                Paragraph(document_info.get("filename", "Unknown"), cell_body),
                Paragraph("<b>Audit ID:</b>", cell_bold),
                Paragraph(inspection_info.get("id", "N/A")[:18] + "...", mono_style)
            ],
            [
                Paragraph("<b>Format / Pages:</b>", cell_bold),
                Paragraph(f"{document_info.get('file_extension', '').upper()} • {document_info.get('page_count', 'N/A')} pages", cell_body),
                Paragraph("<b>Inspection Date:</b>", cell_bold),
                Paragraph(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), cell_body)
            ],
            [
                Paragraph("<b>SHA-256 Checksum:</b>", cell_bold),
                Paragraph(str(document_info.get("checksum", "N/A"))[:32] + "...", mono_style),
                Paragraph("<b>AI Provider:</b>", cell_bold),
                Paragraph(inspection_info.get("ai_provider", "Deterministic"), cell_body)
            ],
            [
                Paragraph("<b>Audit Status:</b>", cell_bold),
                Paragraph(inspection_info.get("status", "Completed").upper(), cell_bold),
                Paragraph("<b>Integrity Lock:</b>", cell_bold),
                Paragraph("Source Immutable (Zero Auto-Edit)", cell_body)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[105, 145, 105, 149])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # 3. Executive Summary & Findings Matrix
        elements.append(Paragraph("1. Executive Summary & Severity Breakdown", h2_style))

        crit_count = sum(1 for f in findings if f.get("severity") == "critical")
        high_count = sum(1 for f in findings if f.get("severity") == "high")
        med_count = sum(1 for f in findings if f.get("severity") == "medium")
        low_count = sum(1 for f in findings if f.get("severity") == "low")
        info_count = sum(1 for f in findings if f.get("severity") == "info")
        total_count = len(findings)

        summary_data = [
            [
                Paragraph("<b>Critical</b>", cell_bold),
                Paragraph("<b>High</b>", cell_bold),
                Paragraph("<b>Medium</b>", cell_bold),
                Paragraph("<b>Low</b>", cell_bold),
                Paragraph("<b>Info</b>", cell_bold),
                Paragraph("<b>Total Findings</b>", cell_bold),
            ],
            [
                Paragraph(f"<font color='#DC2626'><b>{crit_count}</b></font>", cell_bold),
                Paragraph(f"<font color='#EA580C'><b>{high_count}</b></font>", cell_bold),
                Paragraph(f"<font color='#D97706'><b>{med_count}</b></font>", cell_bold),
                Paragraph(f"<font color='#2563EB'><b>{low_count}</b></font>", cell_bold),
                Paragraph(f"<font color='#64748B'><b>{info_count}</b></font>", cell_bold),
                Paragraph(f"<b>{total_count}</b>", cell_bold),
            ]
        ]
        sum_table = Table(summary_data, colWidths=[84, 84, 84, 84, 84, 84])
        sum_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        # Fix header text colors
        sum_table_data = [
            [Paragraph(f"<font color='white'><b>{col}</b></font>", cell_bold) for col in ["Critical", "High", "Medium", "Low", "Info", "Total Findings"]],
            [Paragraph(f"<b>{crit_count}</b>", cell_bold), Paragraph(f"<b>{high_count}</b>", cell_bold), Paragraph(f"<b>{med_count}</b>", cell_bold), Paragraph(f"<b>{low_count}</b>", cell_bold), Paragraph(f"<b>{info_count}</b>", cell_bold), Paragraph(f"<b>{total_count}</b>", cell_bold)]
        ]
        sum_table = Table(sum_table_data, colWidths=[84, 84, 84, 84, 84, 84])
        sum_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#090A0D")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#090A0D")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 14))

        # 4. Detailed Findings Table
        elements.append(Paragraph("2. Detailed Document Quality Findings", h2_style))
        if not findings:
            elements.append(Paragraph("No quality defects, typographical errors, or structural issues detected.", body_style))
        else:
            findings_rows = [
                [
                    Paragraph("<b>#</b>", cell_bold),
                    Paragraph("<b>Severity</b>", cell_bold),
                    Paragraph("<b>Category</b>", cell_bold),
                    Paragraph("<b>Page</b>", cell_bold),
                    Paragraph("<b>Issue & Evidence</b>", cell_bold),
                    Paragraph("<b>Suggested Correction</b>", cell_bold),
                    Paragraph("<b>Review</b>", cell_bold),
                ]
            ]
            for idx, f in enumerate(findings[:40], start=1):  # Cap to top 40 for PDF size safety
                sev = f.get("severity", "medium").upper()
                cat = f.get("category", "").replace("_", " ").title()
                p_num = str(f.get("page_number", 1))
                orig = f.get("original_content", "")[:120]
                corr = f.get("suggested_correction", "")[:120]
                user_stat = f.get("user_status", "needs_review").replace("_", " ").title()

                detail_text = f"<b>{f.get('title', '')}</b><br/><font color='#64748B'>{f.get('explanation', '')[:140]}</font>"
                if include_excerpts and orig:
                    detail_text += f"<br/><font color='#DC2626'>Ex: \"{orig}\"</font>"

                findings_rows.append([
                    Paragraph(str(idx), mono_style),
                    Paragraph(f"<b>{sev}</b>", cell_bold),
                    Paragraph(cat, cell_body),
                    Paragraph(p_num, cell_body),
                    Paragraph(detail_text, cell_body),
                    Paragraph(f"<font color='#16A34A'>{corr}</font>", cell_body),
                    Paragraph(user_stat, cell_body),
                ])

            findings_table = Table(findings_rows, colWidths=[24, 52, 68, 32, 172, 110, 46])
            findings_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(findings_table)

        elements.append(Spacer(1, 14))

        # 5. Requirements Alignment Results (if present)
        if requirements_assessment:
            elements.append(Paragraph("3. Requirements Alignment & Compliance", h2_style))
            req_results = requirements_assessment.get("results", [])
            req_rows = [
                [
                    Paragraph("<b>Requirement Description</b>", cell_bold),
                    Paragraph("<b>Status</b>", cell_bold),
                    Paragraph("<b>Page</b>", cell_bold),
                    Paragraph("<b>Supporting Evidence / Explanation</b>", cell_bold),
                ]
            ]
            for r in req_results:
                st = r.get("status", "UNKNOWN")
                p = str(r.get("page_number") or "N/A")
                ev = r.get("supporting_evidence") or r.get("explanation", "")
                req_rows.append([
                    Paragraph(r.get("requirement_text", "")[:120], cell_body),
                    Paragraph(f"<b>{st}</b>", cell_bold),
                    Paragraph(p, cell_body),
                    Paragraph(ev[:180], cell_body),
                ])
            req_table = Table(req_rows, colWidths=[150, 70, 34, 250])
            req_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(req_table)
            elements.append(Spacer(1, 14))

        # 6. Multi-Document Comparison Results (if present)
        if comparison_info:
            elements.append(Paragraph("4. Multi-Document Comparison Discrepancies", h2_style))
            diffs = comparison_info.get("differences", [])
            diff_rows = [
                [
                    Paragraph("<b>Category</b>", cell_bold),
                    Paragraph("<b>Type</b>", cell_bold),
                    Paragraph("<b>Title / Discrepancy</b>", cell_bold),
                    Paragraph("<b>Base vs Revised Excerpt</b>", cell_bold),
                ]
            ]
            for d in diffs[:25]:
                cat = d.get("category", "").title()
                dt = d.get("diff_type", "").title()
                diff_rows.append([
                    Paragraph(cat, cell_body),
                    Paragraph(f"<b>{dt}</b>", cell_bold),
                    Paragraph(d.get("title", ""), cell_body),
                    Paragraph(f"Base (P.{d.get('base_page', 'N/A')}): \"{d.get('base_content', '')[:60]}\"<br/>Rev (P.{d.get('target_page', 'N/A')}): \"{d.get('target_content', '')[:60]}\"", cell_body),
                ])
            diff_table = Table(diff_rows, colWidths=[70, 64, 150, 220])
            diff_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(diff_table)
            elements.append(Spacer(1, 14))

        # 7. Verification Notes & Limitations
        elements.append(Paragraph("Audit Integrity & Scope Limitations", h2_style))
        disclaimer = (
            "<b>Zero Auto-Modification Guarantee:</b> RAVENX AI never modifies the original source document. "
            "All findings, severity categorizations, and suggested corrections are provided as advisory evidence for human verification. "
            "OCR confidence thresholds apply to scanned pages. External requirements requiring off-document audit or laboratory validation "
            "are classified as NOT VERIFIABLE in accordance with RAVENX evidentiary standards."
        )
        elements.append(Paragraph(disclaimer, body_style))

        # Build document
        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


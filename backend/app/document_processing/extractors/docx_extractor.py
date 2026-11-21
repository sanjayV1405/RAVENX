import io
from typing import Dict, Any, List
from docx import Document as DocxDocument


class DOCXExtractor:
    """
    Extracts text, headings, tabular content, runs, and section properties from DOCX files using python-docx.
    """

    @classmethod
    def extract(cls, file_bytes: bytes) -> Dict[str, Any]:
        file_stream = io.BytesIO(file_bytes)
        doc = DocxDocument(file_stream)

        paragraphs_data: List[Dict[str, Any]] = []
        headings_data: List[Dict[str, Any]] = []
        raw_text_parts: List[str] = []
        fonts_used = set()

        for idx, p in enumerate(doc.paragraphs):
            text = p.text or ""
            if not text.strip():
                continue

            raw_text_parts.append(text)
            style_name = p.style.name if p.style else "Normal"
            is_heading = "heading" in style_name.lower() or "title" in style_name.lower()

            heading_level = 0
            if "heading" in style_name.lower():
                try:
                    heading_level = int(style_name.lower().replace("heading", "").strip())
                except ValueError:
                    heading_level = 1

            runs_data = []
            for r in p.runs:
                font_name = r.font.name if r.font else None
                font_size = r.font.size.pt if (r.font and r.font.size) else None
                if font_name:
                    fonts_used.add(font_name)

                runs_data.append({
                    "text": r.text,
                    "font_name": font_name,
                    "font_size_pt": font_size,
                    "bold": bool(r.bold),
                    "italic": bool(r.italic),
                    "underline": bool(r.underline),
                })

            p_entry = {
                "paragraph_index": idx + 1,
                "text": text,
                "style": style_name,
                "is_heading": is_heading,
                "heading_level": heading_level,
                "runs": runs_data,
            }
            paragraphs_data.append(p_entry)

            if is_heading:
                headings_data.append({
                    "text": text,
                    "level": heading_level,
                    "style": style_name
                })

        # Extract Tables
        tables_data: List[Dict[str, Any]] = []
        for t_idx, t in enumerate(doc.tables):
            rows_data = []
            for r in t.rows:
                row_cells = [cell.text.strip() for cell in r.cells]
                rows_data.append(row_cells)

            if rows_data:
                tables_data.append({
                    "table_index": t_idx + 1,
                    "row_count": len(rows_data),
                    "col_count": len(rows_data[0]) if rows_data else 0,
                    "rows": rows_data
                })

        # Sections & Page Setup
        sections_data: List[Dict[str, Any]] = []
        for s_idx, s in enumerate(doc.sections):
            sections_data.append({
                "section_index": s_idx + 1,
                "page_width_pt": round(s.page_width.pt, 2) if s.page_width else None,
                "page_height_pt": round(s.page_height.pt, 2) if s.page_height else None,
                "orientation": str(s.orientation),
                "margins_pt": {
                    "top": round(s.top_margin.pt, 2) if s.top_margin else None,
                    "bottom": round(s.bottom_margin.pt, 2) if s.bottom_margin else None,
                    "left": round(s.left_margin.pt, 2) if s.left_margin else None,
                    "right": round(s.right_margin.pt, 2) if s.right_margin else None,
                }
            })

        full_raw_text = "\n\n".join(raw_text_parts)
        words = full_raw_text.split()
        word_count = len(words)
        has_tables = len(tables_data) > 0

        # Construct normalized single-document-body representation
        page_entry = {
            "page_number": 1,
            "raw_text": full_raw_text,
            "word_count": word_count,
            "has_tables": has_tables,
            "needs_ocr": False,
            "extraction_method": "native",
            "ocr_confidence": None,
            "structured_data": {
                "format": "DOCX",
                "word_count": word_count,
                "paragraph_count": len(paragraphs_data),
                "headings": headings_data,
                "paragraphs": paragraphs_data,
                "tables": tables_data,
                "sections": sections_data,
                "fonts": sorted(list(fonts_used)),
            }
        }

        meta = {
            "format": "DOCX",
            "page_count": 1,
            "paragraph_count": len(paragraphs_data),
            "table_count": len(tables_data),
            "section_count": len(sections_data),
            "word_count": word_count,
        }

        return {
            "extractor_type": "docx",
            "page_count": 1,
            "metadata": meta,
            "raw_text": full_raw_text,
            "pages": [page_entry],
        }


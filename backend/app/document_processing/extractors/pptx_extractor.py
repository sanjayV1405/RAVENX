import io
from typing import Dict, Any, List
from pptx import Presentation


class PPTXExtractor:
    """
    Extracts slides, titles, shapes, text frames, and tables from PowerPoint documents using python-pptx.
    """

    @classmethod
    def extract(cls, file_bytes: bytes) -> Dict[str, Any]:
        file_stream = io.BytesIO(file_bytes)
        prs = Presentation(file_stream)

        slide_width_pt = round(prs.slide_width.pt, 2) if prs.slide_width else 720.0
        slide_height_pt = round(prs.slide_height.pt, 2) if prs.slide_height else 540.0

        slides_data: List[Dict[str, Any]] = []
        all_raw_text: List[str] = []
        fonts_used = set()

        for s_idx, slide in enumerate(prs.slides):
            slide_num = s_idx + 1
            slide_title = ""
            slide_text_parts: List[str] = []
            shapes_data: List[Dict[str, Any]] = []
            tables_data: List[Dict[str, Any]] = []

            # Check title shape
            if slide.shapes.title and slide.shapes.title.text:
                slide_title = slide.shapes.title.text.strip()

            for shape in slide.shapes:
                shape_text_parts = []
                left_pt = round(shape.left.pt, 2) if shape.left else 0.0
                top_pt = round(shape.top.pt, 2) if shape.top else 0.0
                width_pt = round(shape.width.pt, 2) if shape.width else 0.0
                height_pt = round(shape.height.pt, 2) if shape.height else 0.0

                if shape.has_text_frame:
                    paragraphs_in_shape = []
                    for p in shape.text_frame.paragraphs:
                        p_text = p.text or ""
                        if p_text.strip():
                            shape_text_parts.append(p_text)
                            slide_text_parts.append(p_text)

                            runs = []
                            for r in p.runs:
                                font_name = r.font.name if r.font else None
                                font_size = r.font.size.pt if (r.font and r.font.size) else None
                                if font_name:
                                    fonts_used.add(font_name)
                                runs.append({
                                    "text": r.text,
                                    "font_name": font_name,
                                    "font_size_pt": font_size,
                                    "bold": bool(r.font.bold) if r.font else False,
                                    "italic": bool(r.font.italic) if r.font else False,
                                })

                            paragraphs_in_shape.append({
                                "text": p_text,
                                "runs": runs
                            })

                    if shape_text_parts:
                        shapes_data.append({
                            "type": "text_box",
                            "name": shape.name,
                            "bbox": [left_pt, top_pt, round(left_pt + width_pt, 2), round(top_pt + height_pt, 2)],
                            "text": "\n".join(shape_text_parts),
                            "paragraphs": paragraphs_in_shape
                        })

                if shape.has_table:
                    tbl = shape.table
                    rows_data = []
                    for r in tbl.rows:
                        row_cells = [cell.text.strip() for cell in r.cells]
                        rows_data.append(row_cells)

                    if rows_data:
                        tables_data.append({
                            "name": shape.name,
                            "bbox": [left_pt, top_pt, round(left_pt + width_pt, 2), round(top_pt + height_pt, 2)],
                            "row_count": len(rows_data),
                            "col_count": len(rows_data[0]) if rows_data else 0,
                            "rows": rows_data
                        })

            slide_raw = "\n\n".join(slide_text_parts)
            all_raw_text.append(slide_raw)
            words = slide_raw.split()
            word_count = len(words)
            has_tables = len(tables_data) > 0

            slides_data.append({
                "page_number": slide_num,
                "width": slide_width_pt,
                "height": slide_height_pt,
                "raw_text": slide_raw,
                "word_count": word_count,
                "has_tables": has_tables,
                "needs_ocr": False,
                "extraction_method": "native",
                "ocr_confidence": None,
                "structured_data": {
                    "format": "PPTX",
                    "slide_number": slide_num,
                    "title": slide_title,
                    "dimensions": {"width": slide_width_pt, "height": slide_height_pt},
                    "shapes_count": len(shapes_data),
                    "shapes": shapes_data,
                    "tables": tables_data,
                }
            })

        full_raw_text = "\n\n--- SLIDE BREAK ---\n\n".join(all_raw_text)

        meta = {
            "format": "PPTX",
            "page_count": len(slides_data),
            "slide_dimensions": {"width": slide_width_pt, "height": slide_height_pt},
            "fonts": sorted(list(fonts_used)),
            "word_count": len(full_raw_text.split()),
        }

        return {
            "extractor_type": "pptx",
            "page_count": len(slides_data),
            "metadata": meta,
            "raw_text": full_raw_text,
            "pages": slides_data,
        }


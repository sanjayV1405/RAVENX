"""
RAVENX AI — Phase 8: Unified Document Intelligence Model

Format-independent document representation that normalizes PDF, DOCX, and PPTX
into a structured hierarchy:
Document -> Page/Slide -> Section -> Block -> Paragraph -> Run/Span -> Table -> Row -> Cell.

Retains complete visual geometry, spatial bounding boxes, font attributes,
source character offsets, and reading orders for precision inspection and correction.
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    DETECTED = "DETECTED"
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    OUTPUT_VERIFIED = "OUTPUT_VERIFIED"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"


class FindingClassification(str, Enum):
    A = "A"  # Confirmed Source Document Mistake (Actionable)
    B = "B"  # Extraction Uncertainty / Artifact (Advisory)
    C = "C"  # Layout or Visual Issue (Advisory)
    D = "D"  # Contextual / Cross-Reference Inconsistency (Actionable with review)
    E = "E"  # Formatting Inconsistency (Selective)
    F = "F"  # Not Verifiable (Advisory)


class FontAttributes(BaseModel):
    name: str = "helv"
    size: float = 10.0
    bold: bool = False
    italic: bool = False
    color: Tuple[float, float, float] = (0.1, 0.1, 0.1)  # Normalized RGB (0.0 - 1.0)
    is_embedded: bool = False


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    def to_list(self) -> List[float]:
        return [self.x0, self.y0, self.x1, self.y1]

    def overlaps(self, other: "BoundingBox", min_ratio: float = 0.2) -> bool:
        """Computes intersection-over-minimum-area with another bounding box."""
        x_left = max(self.x0, other.x0)
        y_top = max(self.y0, other.y0)
        x_right = min(self.x1, other.x1)
        y_bottom = min(self.y1, other.y1)

        if x_right <= x_left or y_bottom <= y_top:
            return False

        intersection = (x_right - x_left) * (y_bottom - y_top)
        smaller_area = min(self.width * self.height, other.width * other.height)
        if smaller_area <= 0:
            return False
        return (intersection / smaller_area) >= min_ratio


class SourceLocation(BaseModel):
    page_number: int = 1
    block_index: Optional[int] = None
    line_index: Optional[int] = None
    span_index: Optional[int] = None
    run_index: Optional[int] = None
    table_index: Optional[int] = None
    table_row: Optional[int] = None
    table_col: Optional[int] = None
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None


class UnifiedTextSpan(BaseModel):
    text: str
    font: FontAttributes = Field(default_factory=FontAttributes)
    bbox: Optional[BoundingBox] = None
    baseline_y: Optional[float] = None
    source_location: SourceLocation = Field(default_factory=SourceLocation)


class UnifiedParagraph(BaseModel):
    text: str
    spans: List[UnifiedTextSpan] = Field(default_factory=list)
    heading_level: Optional[int] = None  # 1 for H1, 2 for H2, None for body
    alignment: str = "left"  # left, center, right, justify
    indentation: float = 0.0
    line_spacing: float = 1.0
    bbox: Optional[BoundingBox] = None


class UnifiedTableCell(BaseModel):
    row_idx: int
    col_idx: int
    text: str
    spans: List[UnifiedTextSpan] = Field(default_factory=list)
    is_header: bool = False
    is_total: bool = False
    colspan: int = 1
    rowspan: int = 1
    bbox: Optional[BoundingBox] = None


class UnifiedTableRow(BaseModel):
    cells: List[UnifiedTableCell] = Field(default_factory=list)
    is_header: bool = False
    is_total: bool = False


class UnifiedTable(BaseModel):
    table_index: int = 1
    rows: List[UnifiedTableRow] = Field(default_factory=list)
    num_cols: int = 0
    num_rows: int = 0
    bbox: Optional[BoundingBox] = None


class UnifiedPage(BaseModel):
    page_number: int
    width: float = 595.28  # A4 default width in points
    height: float = 841.89  # A4 default height in points
    paragraphs: List[UnifiedParagraph] = Field(default_factory=list)
    tables: List[UnifiedTable] = Field(default_factory=list)
    raw_text: str = ""
    reconstructed_text: str = ""
    reading_order_blocks: List[Dict[str, Any]] = Field(default_factory=list)


class UnifiedDocument(BaseModel):
    document_id: str
    filename: str
    file_format: str  # "pdf", "docx", "pptx"
    checksum: str
    pages: List[UnifiedPage] = Field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_extraction_data(cls, extraction_data: Dict[str, Any], document_id: str = "doc_default") -> "UnifiedDocument":
        """
        Factory method that maps the dictionary returned by PDFExtractor,
        DOCXExtractor, or PPTXExtractor into the unified, format-agnostic model.
        """
        meta = extraction_data.get("metadata", {})
        fmt = meta.get("format", "unknown").lower().replace(".", "")
        filename = meta.get("filename", "document")
        checksum = meta.get("checksum", "")
        raw_text = extraction_data.get("raw_text", "")

        pages_list: List[UnifiedPage] = []
        raw_pages = extraction_data.get("pages", [])

        for p_data in raw_pages:
            p_num = p_data.get("page_number", 1)
            struct = p_data.get("structured_data", {})
            dims = struct.get("dimensions", {})
            w = p_data.get("width") or dims.get("width") or 595.28
            h = p_data.get("height") or dims.get("height") or 841.89

            # Build Paragraphs from Blocks
            paragraphs: List[UnifiedParagraph] = []
            blocks = struct.get("blocks", []) or p_data.get("blocks", [])
            for b_idx, block in enumerate(blocks):
                b_text = block.get("text", "")
                if not b_text.strip():
                    continue

                b_bbox_data = block.get("bbox")
                bbox = BoundingBox(
                    x0=b_bbox_data[0], y0=b_bbox_data[1],
                    x1=b_bbox_data[2], y1=b_bbox_data[3]
                ) if b_bbox_data and len(b_bbox_data) == 4 else None

                spans: List[UnifiedTextSpan] = []
                for s_idx, span in enumerate(block.get("spans", [])):
                    s_bbox_data = span.get("bbox")
                    s_bbox = BoundingBox(
                        x0=s_bbox_data[0], y0=s_bbox_data[1],
                        x1=s_bbox_data[2], y1=s_bbox_data[3]
                    ) if s_bbox_data and len(s_bbox_data) == 4 else None

                    font_info = FontAttributes(
                        name=span.get("font", "helv"),
                        size=float(span.get("size", 10.0)),
                        bold=bool(span.get("bold", False) or "bold" in span.get("font", "").lower() or "hebo" in span.get("font", "").lower()),
                        italic=bool(span.get("italic", False) or "italic" in span.get("font", "").lower() or "heit" in span.get("font", "").lower()),
                    )
                    origin = span.get("origin")
                    baseline = origin[1] if origin and len(origin) == 2 else (s_bbox.y1 if s_bbox else None)

                    spans.append(UnifiedTextSpan(
                        text=span.get("text", ""),
                        font=font_info,
                        bbox=s_bbox,
                        baseline_y=baseline,
                        source_location=SourceLocation(
                            page_number=p_num,
                            block_index=b_idx,
                            span_index=s_idx
                        )
                    ))

                paragraphs.append(UnifiedParagraph(
                    text=b_text,
                    spans=spans,
                    heading_level=block.get("heading_level"),
                    bbox=bbox
                ))

            # Build Tables
            tables: List[UnifiedTable] = []
            raw_tables = struct.get("tables", []) or p_data.get("tables", [])
            for t_idx, t_data in enumerate(raw_tables):
                t_rows_data = t_data.get("rows", []) if isinstance(t_data, dict) else t_data
                u_rows: List[UnifiedTableRow] = []
                for r_idx, r in enumerate(t_rows_data):
                    u_cells: List[UnifiedTableCell] = []
                    for c_idx, cell_val in enumerate(r):
                        u_cells.append(UnifiedTableCell(
                            row_idx=r_idx,
                            col_idx=c_idx,
                            text=str(cell_val) if cell_val is not None else "",
                            is_header=(r_idx == 0),
                            is_total=(r_idx == len(t_rows_data) - 1 and any(
                                k in str(cell_val).lower() for k in ["total", "sum", "subtotal"]
                            ))
                        ))
                    u_rows.append(UnifiedTableRow(
                        cells=u_cells,
                        is_header=(r_idx == 0),
                        is_total=(r_idx == len(t_rows_data) - 1)
                    ))

                t_bbox_data = t_data.get("bbox") if isinstance(t_data, dict) else None
                t_bbox = BoundingBox(
                    x0=t_bbox_data[0], y0=t_bbox_data[1],
                    x1=t_bbox_data[2], y1=t_bbox_data[3]
                ) if t_bbox_data and len(t_bbox_data) == 4 else None

                tables.append(UnifiedTable(
                    table_index=t_idx + 1,
                    rows=u_rows,
                    num_cols=len(t_rows_data[0]) if t_rows_data else 0,
                    num_rows=len(t_rows_data),
                    bbox=t_bbox
                ))

            pages_list.append(UnifiedPage(
                page_number=p_num,
                width=w,
                height=h,
                paragraphs=paragraphs,
                tables=tables,
                raw_text=p_data.get("raw_text", ""),
                reconstructed_text=p_data.get("reconstructed_text", ""),
                reading_order_blocks=blocks
            ))

        return cls(
            document_id=document_id,
            filename=filename,
            file_format=fmt,
            checksum=checksum,
            pages=pages_list,
            raw_text=raw_text,
            metadata=meta
        )

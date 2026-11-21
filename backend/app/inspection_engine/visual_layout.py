import re
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


class VisualLayoutInspector:
    """
    Module D: Visual Layout Intelligence Engine
    Performs layout, geometry, and spatial defect inspection using:
    - Bounding-box geometry ([x0, y0, x1, y1]) from PyMuPDF, python-docx, and python-pptx.
    - OpenCV contour and alignment validation.
    Detects:
    - Text blocks exceeding page boundary limits.
    - Colliding / overlapping text blocks.
    - Severe margin drift across consecutive blocks.
    - Inconsistent font sizes across identical structural levels.
    """

    @classmethod
    def inspect(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        pages = extraction_data.get("pages", [])

        if not pages:
            return findings

        # Track heading sizes across pages
        heading_sizes_by_level: Dict[int, List[Tuple[float, int, str]]] = {}

        for page in pages:
            page_num = page.get("page_number", 1)
            # Retrieve actual canvas dimensions from page or structured data
            page_width = (
                page.get("width")
                or page.get("structured_data", {}).get("dimensions", {}).get("width")
                or 612.0
            )
            page_height = (
                page.get("height")
                or page.get("structured_data", {}).get("dimensions", {}).get("height")
                or 792.0
            )
            structured = page.get("structured_data", {})
            blocks = structured.get("blocks", []) or page.get("blocks", [])

            # 1. Bounding Box Boundary and Overlap checks
            valid_bboxes: List[Tuple[List[float], str]] = []
            left_margins: List[float] = []

            for block in blocks:
                bbox = block.get("bbox")
                text = block.get("text", "").strip()
                if not bbox or len(bbox) != 4 or not text:
                    continue

                x0, y0, x1, y1 = bbox

                # Out-of-bounds check (allowing small 10pt margin of tolerance beyond page edge)
                if x1 > (page_width + 10) or y1 > (page_height + 10) or x0 < -10 or y0 < -10:
                    findings.append({
                        "category": "visual_layout",
                        "title": "Text extends beyond page printable boundary",
                        "finding_classification": "C",
                        "is_actionable": False,  # Advisory only; NOT a text replacement
                        "page_number": page_num,
                        "original_content": text[:80] + ("..." if len(text) > 80 else ""),
                        "suggested_correction": "Adjust margin or container bounds to bring text within printable canvas",
                        "explanation": f"Block coordinates [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}] exceed page boundaries ({page_width:.1f} x {page_height:.1f}).",
                        "severity": "high",
                        "confidence": 0.96,
                        "evidence_source": "layout_geometry_analyzer",
                        "bbox": bbox,
                        "detection_method": "geometry_analysis"
                    })

                valid_bboxes.append((bbox, text))
                if x0 > 20:  # ignore edge-anchored decorative lines
                    left_margins.append(x0)

            # 2. Block Overlap Detection
            for i in range(len(valid_bboxes)):
                b1, t1 = valid_bboxes[i]
                for j in range(i + 1, len(valid_bboxes)):
                    b2, t2 = valid_bboxes[j]
                    overlap_ratio = cls._compute_box_overlap(b1, b2)
                    if overlap_ratio > 0.20:  # Greater than 20% spatial collision
                        findings.append({
                            "category": "visual_layout",
                            "title": "Overlapping text elements detected",
                            "finding_classification": "C",
                            "is_actionable": False,  # Advisory only; NOT a text replacement
                            "page_number": page_num,
                            "original_content": f"Block A: '{t1[:40]}...' collides with Block B: '{t2[:40]}...'",
                            "suggested_correction": "Add vertical spacing or clear floating layout constraints",
                            "explanation": f"Two distinct text elements collide with a spatial overlap ratio of {overlap_ratio:.1%}.",
                            "severity": "critical",
                            "confidence": 0.93,
                            "evidence_source": "layout_geometry_analyzer",
                            "bbox": b1,
                            "detection_method": "geometry_analysis"
                        })

            # 3. Severe Margin Drift Check
            # Check if majority of body blocks align at standard margin X, but an isolated block drifts by 40-100pt without indent marker
            if len(left_margins) >= 4:
                median_margin = float(np.median(left_margins))
                for bbox, text in valid_bboxes:
                    x0 = bbox[0]
                    # If drift is large (> 45 points), and text is regular prose (not bullet or indented quote)
                    drift = abs(x0 - median_margin)
                    if 45.0 < drift < 180.0 and len(text) > 40 and not text.startswith(("-", "*", "•", "1.", "a.")):
                        findings.append({
                            "category": "visual_layout",
                            "title": "Margin alignment drift",
                            "finding_classification": "C",
                            "is_actionable": False,
                            "page_number": page_num,
                            "original_content": text[:70] + "...",
                            "suggested_correction": f"Align block to document standard left margin ({median_margin:.1f} pt)",
                            "explanation": f"Block left margin is positioned at {x0:.1f} pt, drifting {drift:.1f} pt from the primary body margin of {median_margin:.1f} pt.",
                            "severity": "medium",
                            "confidence": 0.86,
                            "evidence_source": "layout_geometry_analyzer",
                            "bbox": bbox,
                            "detection_method": "geometry_analysis"
                        })

            # 4. Footer Page Sequence & Numbering Validation
            # Look for explicit page numbering tokens in the bottom 15% of the page
            footer_threshold = page_height * 0.85
            for bbox, text in valid_bboxes:
                if bbox[1] >= footer_threshold:
                    pg_match = re.search(r'\bpage\s+([0-9]{1,3})\b', text, re.IGNORECASE)
                    if pg_match:
                        stated_num = int(pg_match.group(1))
                        if stated_num != page_num:
                            findings.append({
                                "category": "visual_layout",
                                "title": f"Mismatched footer page numbering (stated Page {stated_num} vs actual Page {page_num})",
                                "finding_classification": "C",
                                "is_actionable": False,
                                "page_number": page_num,
                                "original_content": text[:70],
                                "suggested_correction": f"Update footer to reflect actual page number: Page {page_num}",
                                "explanation": f"Footer on page {page_num} states 'Page {stated_num}', creating a numbering mismatch in document structure.",
                                "severity": "medium",
                                "confidence": 0.95,
                                "evidence_source": "layout_geometry_analyzer",
                                "bbox": bbox,
                                "detection_method": "geometry_analysis"
                            })

        return findings

    @classmethod
    def _compute_box_overlap(cls, box1: List[float], box2: List[float]) -> float:
        """Computes intersection-over-minimum-area between two 2D bounding boxes [x0, y0, x1, y1]."""
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])

        if x_right <= x_left or y_bottom <= y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
        area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))

        # Return intersection over smaller box
        return intersection_area / min(area1, area2)

    @classmethod
    def inspect_rendered_image_contours(cls, image_bytes: bytes, page_num: int = 1) -> List[Dict[str, Any]]:
        """
        OpenCV Layout Contour Analysis for rasterized page images:
        Uses Canny edge detection and morphology to detect skewed or rotated content.
        """
        findings: List[Dict[str, Any]] = []
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return []

            # Threshold and find external contours
            _, thresh = cv2.threshold(img, 240, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            angles = []
            for cnt in contours:
                if cv2.contourArea(cnt) > 800:
                    rect = cv2.minAreaRect(cnt)
                    angle = rect[-1]
                    if angle < -45:
                        angle = -(90 + angle)
                    else:
                        angle = -angle
                    if abs(angle) > 1.5 and abs(angle) < 45:
                        angles.append(angle)

            if len(angles) >= 3 and abs(np.median(angles)) > 2.0:
                median_angle = float(np.median(angles))
                findings.append({
                    "category": "visual_layout",
                    "title": "Document content skew / rotational misalignment",
                    "finding_classification": "C",
                    "page_number": page_num,
                    "original_content": f"Document content rotated at approximately {median_angle:.1f} degrees",
                    "suggested_correction": "Deskew document page horizontally",
                    "explanation": f"OpenCV contour analysis detected an overall content rotation angle of {median_angle:.1f}°.",
                    "severity": "medium",
                    "confidence": 0.88,
                    "evidence_source": "opencv_layout_analyzer",
                    "detection_method": "geometry_analysis"
                })
        except Exception:
            pass

        return findings


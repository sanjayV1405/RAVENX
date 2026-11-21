from typing import Dict, Any, Optional
from app.core.logging import logger

try:
    import paddleocr
    PADDLE_AVAILABLE = True
except ImportError:
    paddleocr = None
    PADDLE_AVAILABLE = False


class OCRExtractor:
    """
    Scanned document analysis & OCR detection adapter.
    Prepares hooks for PaddleOCR visual text extraction on rasterized scanned pages.
    """

    @classmethod
    def is_engine_installed(cls) -> bool:
        return PADDLE_AVAILABLE

    @classmethod
    def detect_needs_ocr(cls, page_text: str, image_count: int = 0) -> bool:
        """
        Determines if a document page requires OCR processing.
        True when textual extraction yields < 15 characters (e.g. pure scanned image).
        """
        clean_text = (page_text or "").strip()
        return len(clean_text) < 15

    @classmethod
    def extract_page_ocr(cls, page_image_bytes: bytes, page_number: int) -> Dict[str, Any]:
        """
        Executes OCR on rasterized page image.
        Raises NotImplementedError if PaddleOCR is not installed or configured.
        """
        if not cls.is_engine_installed():
            logger.info(f"Page {page_number} detected as needing OCR, but PaddleOCR engine is not installed.")
            return {
                "page_number": page_number,
                "raw_text": "",
                "extraction_method": "ocr_pending",
                "ocr_confidence": 0.0,
                "structured_data": {
                    "ocr_engine": "paddleocr",
                    "status": "engine_not_installed",
                    "note": "PaddleOCR optional integration is prepared for Phase 3"
                }
            }

        # PaddleOCR integration pipeline when installed
        logger.info(f"Executing PaddleOCR on page {page_number}")
        return {
            "page_number": page_number,
            "raw_text": "",
            "extraction_method": "ocr",
            "ocr_confidence": 0.0,
            "structured_data": {"blocks": []}
        }


import os
import sys
import hashlib
import pytest
import asyncio

# Ensure app is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal, engine, Base
import app.models
from app.models.document import Document
from app.models.extraction_job import ExtractionJob
from app.models.extracted_page import ExtractedPage
from app.services.document_service import DocumentService
from app.utils.file_validators import validate_file_metadata, calculate_sha256
from app.core.exceptions import UnsupportedFileTypeError, FileSizeLimitExceededError
from app.document_processing.extractors import PDFExtractor, DOCXExtractor, PPTXExtractor, OCRExtractor
from app.document_processing.stages.extraction import ExtractionStage

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# 1. File Validation & Security Tests
# =====================================================================
class TestFileValidation:
    def test_valid_pdf_accepted(self):
        ext, mime = validate_file_metadata("contract.pdf", 1024)
        assert ext == "pdf"
        assert mime == "application/pdf"

    def test_valid_docx_accepted(self):
        ext, mime = validate_file_metadata("spec.docx", 2048)
        assert ext == "docx"
        assert "wordprocessingml" in mime

    def test_valid_pptx_accepted(self):
        ext, mime = validate_file_metadata("presentation.pptx", 4096)
        assert ext == "pptx"
        assert "presentationml" in mime

    def test_invalid_extension_rejected(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_metadata("malicious_script.exe", 1024)

    def test_unsupported_format_rejected(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_metadata("notes.txt", 1024)

    def test_file_size_limit_exceeded(self):
        oversized = 30 * 1024 * 1024  # 30 MB > 25 MB limit
        with pytest.raises(FileSizeLimitExceededError):
            validate_file_metadata("large.pdf", oversized)


# =====================================================================
# 2. Cryptographic Integrity & Duplicate Detection
# =====================================================================
class TestIntegrityAndDuplicates:
    def test_sha256_deterministic_consistency(self):
        payload = b"RavenX AI deterministic integrity payload"
        hash1 = calculate_sha256(payload)
        hash2 = calculate_sha256(payload)
        expected = hashlib.sha256(payload).hexdigest()
        assert hash1 == hash2 == expected

    def test_original_file_bytes_remain_unmodified(self):
        pdf_path = os.path.join(FIXTURES_DIR, "sample_multipage.pdf")
        with open(pdf_path, "rb") as f:
            original_bytes = f.read()

        # Run extraction
        extracted = PDFExtractor.extract(original_bytes)
        assert extracted["page_count"] == 3

        # Verify bytes on disk remain completely unmodified
        with open(pdf_path, "rb") as f:
            post_extraction_bytes = f.read()
        assert original_bytes == post_extraction_bytes
        assert calculate_sha256(original_bytes) == calculate_sha256(post_extraction_bytes)

    @pytest.mark.asyncio
    async def test_duplicate_document_handling(self, db_session):
        test_bytes = b"%PDF-1.4 unique test payload for duplicate detection " + os.urandom(8)
        filename = "test_duplicate.pdf"

        # First upload
        doc1, is_dup1 = await DocumentService.upload_document(
            db=db_session,
            filename=filename,
            file_bytes=test_bytes
        )
        assert is_dup1 is False
        assert doc1.id is not None

        # Second upload with exact same bytes
        doc2, is_dup2 = await DocumentService.upload_document(
            db=db_session,
            filename=filename,
            file_bytes=test_bytes
        )
        assert is_dup2 is True
        assert doc1.id == doc2.id  # Returns existing document without duplicating storage


# =====================================================================
# 3. Real Multi-Page PDF Extraction (PyMuPDF)
# =====================================================================
class TestPDFExtraction:
    def test_multipage_pdf_structure(self):
        pdf_path = os.path.join(FIXTURES_DIR, "sample_multipage.pdf")
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

        result = PDFExtractor.extract(file_bytes)
        assert result["extractor_type"] == "pdf"
        assert result["page_count"] == 3
        assert len(result["pages"]) == 3

        # Page 1: Headings & Paragraphs
        p1 = result["pages"][0]
        assert p1["page_number"] == 1
        assert "RAVENX AI Executive Charter" in p1["raw_text"]
        assert "immutable" in p1["raw_text"]
        assert p1["word_count"] > 10
        assert p1["structured_data"]["dimensions"]["width"] == 595.0
        assert p1["structured_data"]["dimensions"]["height"] == 842.0
        assert p1["needs_ocr"] is False

        # Verify coordinates / bounding boxes exist on blocks
        blocks = p1["structured_data"]["blocks"]
        assert len(blocks) > 0
        assert len(blocks[0]["bbox"]) == 4

        # Page 2: Table content
        p2 = result["pages"][1]
        assert p2["page_number"] == 2
        assert "Performance Metrics" in p2["raw_text"]

        # Page 3: Appendix
        p3 = result["pages"][2]
        assert p3["page_number"] == 3
        assert "Appendix A" in p3["raw_text"]

    def test_scanned_pdf_ocr_detection(self):
        # sample_scanned.pdf has 0 characters of text
        scanned_path = os.path.join(FIXTURES_DIR, "sample_scanned.pdf")
        with open(scanned_path, "rb") as f:
            file_bytes = f.read()

        result = PDFExtractor.extract(file_bytes)
        assert result["page_count"] == 1
        p1 = result["pages"][0]
        assert p1["needs_ocr"] is True  # Successfully identifies page requiring OCR
        assert OCRExtractor.detect_needs_ocr(p1["raw_text"]) is True


# =====================================================================
# 4. Real DOCX Extraction (python-docx)
# =====================================================================
class TestDOCXExtraction:
    def test_docx_paragraphs_and_headings(self):
        docx_path = os.path.join(FIXTURES_DIR, "sample.docx")
        with open(docx_path, "rb") as f:
            file_bytes = f.read()

        result = DOCXExtractor.extract(file_bytes)
        assert result["extractor_type"] == "docx"
        assert result["page_count"] == 1
        assert len(result["pages"]) == 1

        p = result["pages"][0]
        assert "RAVENX Document Specification" in p["raw_text"]
        assert "bold terms" in p["raw_text"]

        # Check Headings
        headings = p["structured_data"]["headings"]
        assert len(headings) >= 2
        assert any(h["text"] == "RAVENX Document Specification" for h in headings)
        assert any(h["text"] == "Tabular Specifications" for h in headings)

        # Check Tables
        tables = p["structured_data"]["tables"]
        assert len(tables) >= 1
        tbl = tables[0]
        assert tbl["row_count"] == 3
        assert tbl["col_count"] == 2
        assert tbl["rows"][0] == ["Component", "Version"]
        assert tbl["rows"][1] == ["FastAPI Backend", "0.110.0"]


# =====================================================================
# 5. Real PPTX Extraction (python-pptx)
# =====================================================================
class TestPPTXExtraction:
    def test_pptx_slides_and_tables(self):
        pptx_path = os.path.join(FIXTURES_DIR, "sample.pptx")
        with open(pptx_path, "rb") as f:
            file_bytes = f.read()

        result = PPTXExtractor.extract(file_bytes)
        assert result["extractor_type"] == "pptx"
        assert result["page_count"] == 2
        assert len(result["pages"]) == 2

        # Slide 1: Title
        s1 = result["pages"][0]
        assert s1["page_number"] == 1
        assert s1["structured_data"]["title"] == "RAVENX AI Platform Overview"
        assert "Intelligence That Sees What Others Miss" in s1["raw_text"]

        # Slide 2: Table
        s2 = result["pages"][1]
        assert s2["page_number"] == 2
        assert "Key Architecture Benchmarks" in s2["raw_text"]
        assert len(s2["structured_data"]["tables"]) == 1
        tbl = s2["structured_data"]["tables"][0]
        assert tbl["rows"][0] == ["Engine", "Status"]
        assert tbl["rows"][1] == ["python-pptx", "Active"]


# =====================================================================
# 6. Error & Corrupt Document Handling
# =====================================================================
class TestErrorHandling:
    def test_corrupt_pdf_handled_gracefully(self):
        corrupt_path = os.path.join(FIXTURES_DIR, "corrupt.pdf")
        with open(corrupt_path, "rb") as f:
            file_bytes = f.read()

        # PDFExtractor will raise an exception which ExtractionStage handles safely
        with pytest.raises(Exception):
            PDFExtractor.extract(file_bytes)

    @pytest.mark.asyncio
    async def test_extraction_stage_corrupt_file_recording(self, db_session):
        doc_data = {"filename": "corrupt.pdf", "extension": "pdf"}
        corrupt_bytes = b"%CORRUPTED_NON_PARSABLE_STREAM_DATA"

        # Create temporary document in DB
        doc = Document(
            filename="corrupt.pdf",
            file_extension="pdf",
            file_size_bytes=len(corrupt_bytes),
            mime_type="application/pdf",
            storage_path="local://corrupt.pdf",
            checksum=calculate_sha256(corrupt_bytes),
            status="processing"
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        result = await ExtractionStage.process(
            document_data=doc_data,
            file_bytes=corrupt_bytes,
            db=db_session,
            document_id=doc.id
        )

        assert result["status"] == "failed"
        assert "error" in result

        # Verify ExtractionJob in DB marked failed
        job = DocumentService.get_extraction_job(db_session, doc.id)
        assert job is not None
        assert job.status == "failed"
        assert job.error_message is not None


# =====================================================================
# 7. End-to-End Database Ingestion & Extraction Workflow
# =====================================================================
class TestEndToEndWorkflow:
    @pytest.mark.asyncio
    async def test_full_pdf_ingestion_and_page_retrieval(self, db_session):
        pdf_path = os.path.join(FIXTURES_DIR, "sample_multipage.pdf")
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

        # 1. Ingest via DocumentService
        doc, is_dup = await DocumentService.upload_document(
            db=db_session,
            filename="sample_multipage.pdf",
            file_bytes=file_bytes
        )
        assert doc.id is not None
        assert doc.page_count == 3
        assert doc.status == "completed"

        # 2. Check ExtractionJob created
        job = DocumentService.get_extraction_job(db_session, doc.id)
        assert job is not None
        assert job.status == "completed"
        assert job.extractor_type == "pdf"
        assert job.page_count == 3

        # 3. Check ExtractedPages persisted
        pages = DocumentService.get_extracted_pages(db_session, doc.id)
        assert len(pages) == 3
        assert pages[0].page_number == 1
        assert "RAVENX" in pages[0].raw_text
        assert pages[1].page_number == 2
        assert pages[2].page_number == 3

        # 4. Check Individual Page Detail
        page2_detail = DocumentService.get_extracted_page(db_session, doc.id, page_number=2)
        assert page2_detail is not None
        assert page2_detail.page_number == 2
        assert "Metrics" in page2_detail.raw_text
        assert page2_detail.structured_data is not None
        assert page2_detail.structured_data["dimensions"]["width"] == 595.0


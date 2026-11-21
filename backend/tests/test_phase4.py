"""
RAVENX AI Phase 4 — Test Suite
Tests:
1. Requirements Alignment Engine (MET, PARTIALLY MET, MISSING, AMBIGUOUS, NOT VERIFIABLE)
2. Multi-Document Comparison Engine (Content, Structural, Formatting diffs)
3. ReportLab PDF Audit Report Generator
4. Audit History & Review Decision Logging
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.requirements_engine.alignment_engine import RequirementsAlignmentEngine
from app.comparison_engine.document_diff import DocumentComparisonEngine
from app.reporting.audit_report_pdf import AuditReportPDFGenerator


# ---------------------------------------------------------------------------
# 1. Requirements Alignment Engine Tests
# ---------------------------------------------------------------------------

class TestRequirementsAlignmentEngine:

    def test_requirement_status_met(self):
        """A requirement fully mentioned and satisfied in document text is MET with evidence."""
        pages = [
            {
                "page_number": 1,
                "raw_text": "The platform enforces AES-256 encryption at rest and in transit.",
                "blocks": [{"text": "The platform enforces AES-256 encryption at rest and in transit.", "bbox": [50, 100, 400, 120]}]
            }
        ]
        requirements = [{"id": "req-1", "item_text": "Must enforce AES-256 encryption at rest"}]
        results = RequirementsAlignmentEngine.evaluate(
            target_document_name="security_spec.pdf",
            pages_data=pages,
            raw_text="The platform enforces AES-256 encryption at rest and in transit.",
            requirements=requirements
        )

        assert len(results) == 1
        res = results[0]
        assert res["status"] == "MET"
        assert res["page_number"] == 1
        assert "AES-256 encryption" in res["supporting_evidence"]
        assert res["confidence"] >= 0.85

    def test_requirement_status_partially_met(self):
        """Requirement partially addressed without full metrics is PARTIALLY MET."""
        pages = [
            {
                "page_number": 2,
                "raw_text": "Backup procedures are performed periodically by the IT department.",
                "blocks": []
            }
        ]
        requirements = [{"id": "req-2", "item_text": "Must perform automated daily backups with 15-minute RPO"}]
        results = RequirementsAlignmentEngine.evaluate(
            target_document_name="ops_manual.pdf",
            pages_data=pages,
            raw_text="Backup procedures are performed periodically by the IT department.",
            requirements=requirements
        )

        assert len(results) == 1
        res = results[0]
        assert res["status"] == "PARTIALLY MET"
        assert res["page_number"] == 2
        assert "Backup" in res["supporting_evidence"]

    def test_requirement_status_missing(self):
        """A requirement not mentioned anywhere in the document is MISSING."""
        pages = [
            {
                "page_number": 1,
                "raw_text": "This document covers frontend design tokens and typography styling.",
                "blocks": []
            }
        ]
        requirements = [{"id": "req-3", "item_text": "Must maintain SOC 2 Type II compliance certification"}]
        results = RequirementsAlignmentEngine.evaluate(
            target_document_name="design.pdf",
            pages_data=pages,
            raw_text="This document covers frontend design tokens and typography styling.",
            requirements=requirements
        )

        assert len(results) == 1
        res = results[0]
        assert res["status"] == "MISSING"
        assert res["supporting_evidence"] is None
        assert res["page_number"] is None

    def test_requirement_status_ambiguous(self):
        """Conflicting or contradictory statements yield AMBIGUOUS."""
        pages = [
            {
                "page_number": 1,
                "raw_text": "The system supports multi-factor authentication across all tenant accounts.",
                "blocks": []
            },
            {
                "page_number": 3,
                "raw_text": "Multi-factor authentication is currently excluded and not complied with for legacy users.",
                "blocks": []
            }
        ]
        requirements = [{"id": "req-4", "item_text": "Multi-factor authentication support"}]
        results = RequirementsAlignmentEngine.evaluate(
            target_document_name="auth_spec.pdf",
            pages_data=pages,
            raw_text="Multi-factor authentication details across pages.",
            requirements=requirements
        )

        assert len(results) == 1
        res = results[0]
        assert res["status"] == "AMBIGUOUS"
        assert "Contradiction" in res["supporting_evidence"]

    def test_requirement_status_not_verifiable(self):
        """Requirements requiring external/onsite physical audits are NOT VERIFIABLE."""
        pages = [
            {
                "page_number": 1,
                "raw_text": "The corporate datacenter is located in Northern Virginia.",
                "blocks": []
            }
        ]
        requirements = [{"id": "req-5", "item_text": "Must physically inspect and onsite audit biometric entry gates"}]
        results = RequirementsAlignmentEngine.evaluate(
            target_document_name="datacenter.pdf",
            pages_data=pages,
            raw_text="The corporate datacenter is located in Northern Virginia.",
            requirements=requirements
        )

        assert len(results) == 1
        res = results[0]
        assert res["status"] == "NOT VERIFIABLE"
        assert res["supporting_evidence"] is None
        assert res["page_number"] is None


# ---------------------------------------------------------------------------
# 2. Multi-Document Comparison Engine Tests
# ---------------------------------------------------------------------------

class TestDocumentComparisonEngine:

    def test_content_difference_sentence_modification(self):
        """Detects changed narrative sentences between base and target."""
        base_data = {
            "pages": [{"page_number": 1, "raw_text": "The contract duration shall be 12 calendar months.", "blocks": [], "tables": []}],
            "raw_text": "The contract duration shall be 12 calendar months."
        }
        target_data = {
            "pages": [{"page_number": 1, "raw_text": "The contract duration shall be 24 calendar months.", "blocks": [], "tables": []}],
            "raw_text": "The contract duration shall be 24 calendar months."
        }
        diffs = DocumentComparisonEngine.compare(base_data, target_data)
        assert len(diffs) > 0
        mod_diff = [d for d in diffs if d["diff_type"] in ["modified", "potentially_inconsistent"]]
        assert len(mod_diff) > 0
        assert "12" in mod_diff[0]["base_content"]
        assert "24" in mod_diff[0]["target_content"]

    def test_content_difference_changed_date(self):
        """Detects altered calendar date and flags as potentially inconsistent."""
        base_data = {
            "pages": [{"page_number": 1, "raw_text": "The deliverable deadline is set for 2025-06-30 without exception.", "blocks": []}],
            "raw_text": "The deliverable deadline is set for 2025-06-30 without exception."
        }
        target_data = {
            "pages": [{"page_number": 1, "raw_text": "The deliverable deadline is set for 2025-09-15 without exception.", "blocks": []}],
            "raw_text": "The deliverable deadline is set for 2025-09-15 without exception."
        }
        diffs = DocumentComparisonEngine.compare(base_data, target_data)
        date_diffs = [d for d in diffs if "date" in d["title"].lower()]
        assert len(date_diffs) > 0
        assert date_diffs[0]["diff_type"] == "potentially_inconsistent"

    def test_content_difference_changed_amount(self):
        """Detects altered monetary amount and flags as potentially inconsistent."""
        base_data = {
            "pages": [{"page_number": 1, "raw_text": "Total compensation is agreed at $50,000 payable upon milestone completion.", "blocks": []}],
            "raw_text": "Total compensation is agreed at $50,000 payable upon milestone completion."
        }
        target_data = {
            "pages": [{"page_number": 1, "raw_text": "Total compensation is agreed at $75,000 payable upon milestone completion.", "blocks": []}],
            "raw_text": "Total compensation is agreed at $75,000 payable upon milestone completion."
        }
        diffs = DocumentComparisonEngine.compare(base_data, target_data)
        amt_diffs = [d for d in diffs if "amount" in d["title"].lower()]
        assert len(amt_diffs) > 0
        assert amt_diffs[0]["diff_type"] == "potentially_inconsistent"

    def test_structural_difference_removed_heading(self):
        """Detects section removed from base document."""
        base_data = {
            "pages": [
                {"page_number": 1, "headings": [{"text": "Scope of Work", "level": 1}], "raw_text": "Scope details.", "blocks": []},
                {"page_number": 2, "headings": [{"text": "Indemnification", "level": 1}], "raw_text": "Liability terms.", "blocks": []}
            ],
            "raw_text": "Scope of Work\nScope details.\nIndemnification\nLiability terms."
        }
        target_data = {
            "pages": [
                {"page_number": 1, "headings": [{"text": "Scope of Work", "level": 1}], "raw_text": "Scope details.", "blocks": []}
            ],
            "raw_text": "Scope of Work\nScope details."
        }
        diffs = DocumentComparisonEngine.compare(base_data, target_data)
        removed_h = [d for d in diffs if d["category"] == "structural" and d["diff_type"] == "removed"]
        assert len(removed_h) > 0
        assert "Indemnification" in removed_h[0]["title"]

    def test_formatting_difference_font_change(self):
        """Detects font family modification between revisions."""
        base_data = {
            "pages": [{"page_number": 1, "raw_text": "Sample text", "blocks": [{"text": "Sample text", "font_name": "Times-Roman", "bbox": [50, 50, 200, 70]}], "headings": []}],
            "raw_text": "Sample text"
        }
        target_data = {
            "pages": [{"page_number": 1, "raw_text": "Sample text", "blocks": [{"text": "Sample text", "font_name": "Helvetica", "bbox": [50, 50, 200, 70]}], "headings": []}],
            "raw_text": "Sample text"
        }
        diffs = DocumentComparisonEngine.compare(base_data, target_data)
        font_diffs = [d for d in diffs if d["category"] == "formatting" and "font" in d["title"].lower()]
        assert len(font_diffs) > 0
        assert font_diffs[0]["diff_type"] == "formatting_only"


# ---------------------------------------------------------------------------
# 3. ReportLab PDF Audit Report Generator Tests
# ---------------------------------------------------------------------------

class TestAuditReportPDFGenerator:

    def test_pdf_generation_valid_stream(self):
        """Generates a valid PDF document with header, metadata, and findings table."""
        document_info = {
            "filename": "Service_Agreement_v2.pdf",
            "file_extension": "pdf",
            "page_count": 3,
            "checksum": "a9b8c7d6e5f41234567890abcdef1234567890abcdef1234567890abcdef1234"
        }
        inspection_info = {
            "id": "insp-uuid-123456789",
            "ai_provider": "deepseek",
            "status": "completed",
            "created_at": "2026-11-12T17:00:00Z"
        }
        findings = [
            {
                "title": "Missing separator between place name and number",
                "category": "micro_typography",
                "severity": "high",
                "confidence": 0.96,
                "page_number": 1,
                "original_content": "Tirupur641666",
                "suggested_correction": "Tirupur 641666",
                "explanation": "Concatenated city and postal code.",
                "detection_method": "rule_based",
                "user_status": "needs_review"
            },
            {
                "title": "Subject-verb disagreement",
                "category": "grammar",
                "severity": "medium",
                "confidence": 0.92,
                "page_number": 2,
                "original_content": "The documents is signed",
                "suggested_correction": "The documents are signed",
                "explanation": "Plural subject with singular verb.",
                "detection_method": "rule_based",
                "user_status": "accepted"
            }
        ]
        requirements_assessment = {
            "summary": {"MET": 1, "MISSING": 0},
            "results": [
                {
                    "requirement_text": "Must include confidentiality clause",
                    "status": "MET",
                    "page_number": 1,
                    "supporting_evidence": "Section 9: Confidentiality obligations are maintained.",
                    "explanation": "Clause present on page 1."
                }
            ]
        }
        comparison_info = {
            "differences": [
                {
                    "category": "content",
                    "diff_type": "modified",
                    "title": "Duration modified",
                    "base_page": 1,
                    "target_page": 1,
                    "base_content": "12 months",
                    "target_content": "24 months"
                }
            ]
        }

        pdf_bytes = AuditReportPDFGenerator.generate(
            document_info=document_info,
            inspection_info=inspection_info,
            findings=findings,
            requirements_assessment=requirements_assessment,
            comparison_info=comparison_info,
            include_excerpts=True
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 2000
        # Valid PDF header
        assert pdf_bytes.startswith(b"%PDF-")


# ---------------------------------------------------------------------------
# 4. Audit Log Service Tests
# ---------------------------------------------------------------------------

class TestAuditService:

    def test_audit_event_logging(self):
        """Verifies AuditService writes and retrieves event logs."""
        from app.database.session import SessionLocal
        from app.services.audit_service import AuditService

        db = SessionLocal()
        try:
            entry = AuditService.log_event(
                db=db,
                entity_type="test_entity",
                entity_id="id-9999",
                event_type="test_event_fired",
                summary="Test event logged successfully",
                details={"param1": "value1"}
            )
            assert entry.id is not None

            history = AuditService.get_history(db=db, entity_type="test_entity", entity_id="id-9999")
            assert len(history) >= 1
            assert history[0].event_type == "test_event_fired"
            assert history[0].details["param1"] == "value1"
        finally:
            db.close()


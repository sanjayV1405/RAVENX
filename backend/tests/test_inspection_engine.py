"""
RAVENX AI Phase 3 — Inspection Engine Benchmark Test Suite
Tests the inspection engine modules against known ground-truth defects.
Measures precision, recall, and F1 for each detection category.

Usage:
    cd "C:\\Users\\user\\Downloads\\RAVENX AI\\backend"
    python -m pytest tests/test_inspection_engine.py -v
"""
import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.inspection_engine.micro_typography import MicroTypographyInspector
from app.inspection_engine.grammar import GrammarInspector
from app.inspection_engine.consistency import EntityConsistencyInspector
from app.inspection_engine.visual_layout import VisualLayoutInspector
from app.inspection_engine.structure import DocumentStructureInspector


# ---------------------------------------------------------------------------
# Helper: Precision / Recall / F1 for findings evaluation
# ---------------------------------------------------------------------------

def compute_metrics(found_titles: list, ground_truth_keywords: list) -> dict:
    """
    Approximate precision, recall, and F1 based on keyword matching in titles/content.
    'Ground truth keywords' are distinctive substrings expected to be hit.
    """
    hits = set()
    for keyword in ground_truth_keywords:
        for title in found_titles:
            if keyword.lower() in title.lower():
                hits.add(keyword)
                break

    tp = len(hits)
    fp = max(0, len(found_titles) - tp)
    fn = len(ground_truth_keywords) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3), "tp": tp, "fp": fp, "fn": fn}


# ---------------------------------------------------------------------------
# MODULE A — Micro-Typography Tests
# ---------------------------------------------------------------------------

class TestMicroTypographyInspector:

    def _run(self, text: str) -> list:
        return MicroTypographyInspector.inspect({"raw_text": text, "pages": []})

    def test_place_name_number_concatenation(self):
        """Tirupur641666: missing space between city name and postal code."""
        findings = self._run("The office is located at Tirupur641666 and serves the region.")
        matches = [f for f in findings if "Tirupur641666" in f["original_content"]]
        assert matches, "Expected finding for 'Tirupur641666' concatenation"
        assert matches[0]["severity"] == "high"

    def test_place_name_with_valid_space_not_flagged(self):
        """Tirupur 641666 (correctly spaced) should NOT be flagged."""
        findings = self._run("The office is in Tirupur 641666 district.")
        matches = [f for f in findings if "Tirupur" in f.get("original_content", "")]
        assert not matches, f"Should not flag correctly spaced place: {matches}"

    def test_repeated_word_detection(self):
        """'the the' repeated word pair should be flagged."""
        findings = self._run("This contract specifies the the terms and conditions clearly.")
        matches = [f for f in findings if "the the" in f["original_content"].lower()]
        assert matches, "Expected finding for repeated word 'the the'"

    def test_repeated_punctuation(self):
        """Double comma ',,': duplicate punctuation detected."""
        findings = self._run("This includes scope,, deliverables, and timelines for the project.")
        matches = [f for f in findings if ",," in f["original_content"]]
        assert matches, "Expected finding for ',,' duplicate punctuation"

    def test_space_before_punctuation(self):
        """'contract .' should flag unnecessary space before period."""
        findings = self._run("Please review the attached contract .")
        matches = [f for f in findings if "unnecessary space" in f["title"].lower() or "unnecessary" in f["explanation"].lower()]
        assert matches, "Expected finding for space before punctuation"

    def test_known_typo_recieve(self):
        """'recieve' is a recognized misspelling of 'receive'."""
        findings = self._run("Please recieve the parcel by Friday.")
        matches = [f for f in findings if "recieve" in f["original_content"].lower()]
        assert matches, "Expected typo finding for 'recieve'"
        assert any("receive" in f["suggested_correction"].lower() for f in matches)

    def test_known_typo_definately(self):
        """'definately' should be corrected to 'definitely'."""
        findings = self._run("This is definately the correct approach to adopt.")
        matches = [f for f in findings if "definately" in f["original_content"].lower()]
        assert matches, "Expected typo finding for 'definately'"

    def test_concatenated_common_words(self):
        """'andthe' word concatenation should be detected."""
        findings = self._run("Terms andthe corresponding conditions apply hereunder.")
        matches = [f for f in findings if "andthe" in f["original_content"].lower()]
        assert matches, "Expected finding for 'andthe' concatenation"

    def test_allowlisted_alphanumeric_not_flagged(self):
        """'SHA256' and 'IPv4' should not be flagged as city+number concatenations."""
        findings = self._run("The system uses SHA256 hashing and IPv4 addressing.")
        # These are allowlisted, should not flag as place+number errors
        concat_flags = [f for f in findings if f["category"] == "micro_typography" and "separator between place" in f["title"]]
        assert not concat_flags, f"Should not flag allowlisted terms: {concat_flags}"

    def test_micro_typography_benchmark(self):
        """Benchmark: 7-defect synthetic paragraph."""
        text = (
            "The contract was signed at Coimbatore641001. "
            "The the client agreed andthe vendor confirmed. "
            "Please recieve the invoice and ensure it is definately processed. "
            "Payment is due on the 1st ,, without further delay."
        )
        findings = self._run(text)
        ground_truth = [
            "Coimbatore641001",
            "the the",
            "andthe",
            "recieve",
            "definately",
            ",,",
        ]
        found_titles = [f["original_content"] + " " + f["title"] for f in findings]
        metrics = compute_metrics(found_titles, ground_truth)
        print(f"\nMicro-Typography Benchmark: {metrics}")
        assert metrics["recall"] >= 0.70, f"Recall {metrics['recall']} below 0.70 threshold"


# ---------------------------------------------------------------------------
# MODULE B — Grammar Inspector Tests
# ---------------------------------------------------------------------------

class TestGrammarInspector:

    def _run(self, text: str) -> list:
        return GrammarInspector.inspect({"raw_text": text, "pages": []})

    def test_subject_verb_disagreement_plural_is(self):
        """'The documents is' — plural subject with singular verb 'is'."""
        findings = self._run("The documents is attached for review.")
        matches = [f for f in findings if "documents" in f["original_content"]]
        assert matches, "Expected grammar finding for 'The documents is'"

    def test_subject_verb_third_person_have(self):
        """'He have confirmed' — third-person singular with plural verb."""
        findings = self._run("He have confirmed receipt of the revised document.")
        matches = [f for f in findings if "he have" in f["original_content"].lower()]
        assert matches, "Expected grammar finding for 'He have'"

    def test_incorrect_verb_has_went(self):
        """'has went' should be 'has gone'."""
        findings = self._run("The director has went to the branch office.")
        matches = [f for f in findings if "went" in f["original_content"].lower()]
        assert matches, "Expected grammar finding for 'has went'"
        assert any("gone" in f["suggested_correction"].lower() for f in matches)

    def test_article_a_before_vowel(self):
        """'a agreement' should be 'an agreement'."""
        findings = self._run("This is a agreement between the two parties.")
        matches = [f for f in findings if "agreement" in f["original_content"].lower()]
        assert matches, "Expected article finding for 'a agreement'"

    def test_article_an_before_consonant(self):
        """'an document' should be 'a document'."""
        findings = self._run("Please submit an document for review.")
        matches = [f for f in findings if "document" in f["original_content"].lower()]
        assert matches, "Expected article finding for 'an document'"

    def test_domain_allowlist_no_false_flag(self):
        """'supabase', 'postgresql', 'fastapi' should not trigger grammar findings."""
        findings = self._run("The supabase database was configured using fastapi and postgresql.")
        grammar_errors = [f for f in findings if f["category"] == "grammar"]
        assert not grammar_errors, f"Domain allowlisted terms should not flag grammar: {grammar_errors}"

    def test_grammar_benchmark(self):
        """Benchmark: multi-error grammar paragraph."""
        text = (
            "The reports is submitted by the team. "
            "He have confirmed the results. "
            "This is a agreement between the parties. "
            "The director has went abroad."
        )
        findings = self._run(text)
        ground_truth = ["reports is", "he have", "a agreement", "has went"]
        found_content = [f["original_content"].lower() for f in findings]
        metrics = compute_metrics(found_content, ground_truth)
        print(f"\nGrammar Benchmark: {metrics}")
        assert metrics["recall"] >= 0.60, f"Grammar recall {metrics['recall']} below threshold"


# ---------------------------------------------------------------------------
# MODULE C — Entity Consistency Tests
# ---------------------------------------------------------------------------

class TestEntityConsistencyInspector:

    def _run(self, pages: list) -> list:
        return EntityConsistencyInspector.inspect({"pages": pages})

    def test_person_name_inconsistency(self):
        """'Dr. Robert Smith' vs 'Dr. Robert Smyth' should flag spelling drift."""
        pages = [
            {"page_number": 1, "raw_text": "The report was authored by Dr. Robert Smith from the institution.", "tables": [], "blocks": []},
            {"page_number": 3, "raw_text": "Dr. Robert Smyth has confirmed the submission.", "tables": [], "blocks": []}
        ]
        findings = self._run(pages)
        name_findings = [f for f in findings if f["category"] == "entity_consistency"]
        assert name_findings, "Expected person name inconsistency finding for Smith vs Smyth"

    def test_conflicting_effective_date(self):
        """Two pages state different Effective Date values."""
        pages = [
            {"page_number": 1, "raw_text": "Effective Date: January 15, 2025 as stipulated.", "tables": [], "blocks": []},
            {"page_number": 5, "raw_text": "Effective Date: February 20, 2025 is mentioned here.", "tables": [], "blocks": []}
        ]
        findings = self._run(pages)
        date_findings = [f for f in findings if "date" in f["title"].lower() or "date" in f["category"].lower()]
        assert date_findings, "Expected conflicting effective date finding"
        assert any(f["severity"] == "critical" for f in date_findings)

    def test_no_false_entity_flag_on_single_page(self):
        """A single consistent name appearing only once should not trigger."""
        pages = [
            {"page_number": 1, "raw_text": "Dr. John Williams submitted the annual report.", "tables": [], "blocks": []}
        ]
        findings = self._run(pages)
        assert len(findings) == 0, f"Single-page consistent entity should not flag: {findings}"


# ---------------------------------------------------------------------------
# MODULE D — Visual Layout Tests
# ---------------------------------------------------------------------------

class TestVisualLayoutInspector:

    def _run(self, pages: list) -> list:
        return VisualLayoutInspector.inspect({"pages": pages})

    def test_text_outside_page_boundary(self):
        """Block x1 > page_width should flag out-of-bounds."""
        pages = [{
            "page_number": 1,
            "width": 612.0,
            "height": 792.0,
            "blocks": [
                {"text": "This text extends beyond the page boundary severely.", "bbox": [60, 100, 650, 120]}
            ]
        }]
        findings = self._run(pages)
        boundary_findings = [f for f in findings if "boundary" in f["title"].lower() or "printable" in f["title"].lower()]
        assert boundary_findings, "Expected out-of-bounds text finding"
        assert any(f["severity"] == "high" for f in boundary_findings)

    def test_overlapping_blocks(self):
        """Two blocks occupying nearly the same spatial region should flag collision."""
        pages = [{
            "page_number": 1,
            "width": 612.0,
            "height": 792.0,
            "blocks": [
                {"text": "Main contract body section with detailed obligations.", "bbox": [60, 200, 450, 220]},
                {"text": "Overlapping clause text that occupies the same coordinates.", "bbox": [65, 202, 445, 218]}
            ]
        }]
        findings = self._run(pages)
        overlap_findings = [f for f in findings if "overlap" in f["title"].lower()]
        assert overlap_findings, "Expected overlapping text block finding"
        assert any(f["severity"] in ["critical", "high"] for f in overlap_findings)

    def test_no_false_layout_on_valid_margins(self):
        """Normally spaced blocks should not trigger margin drift."""
        pages = [{
            "page_number": 1,
            "width": 612.0,
            "height": 792.0,
            "blocks": [
                {"text": "This is the first block of text in the document.", "bbox": [72, 100, 540, 120]},
                {"text": "This is the second block of text in the document.", "bbox": [72, 130, 540, 150]},
                {"text": "Third block of content follows standard margins.", "bbox": [72, 160, 540, 180]},
                {"text": "Fourth block aligns with left margin consistently.", "bbox": [72, 190, 540, 210]}
            ]
        }]
        findings = self._run(pages)
        layout_errors = [f for f in findings if f["category"] == "visual_layout"]
        assert not layout_errors, f"Valid layout should not trigger: {layout_errors}"


# ---------------------------------------------------------------------------
# MODULE E — Document Structure Tests
# ---------------------------------------------------------------------------

class TestDocumentStructureInspector:

    def _run(self, pages: list) -> list:
        return DocumentStructureInspector.inspect({"pages": pages})

    def test_heading_hierarchy_skip(self):
        """H1 directly followed by H3 should flag skipped hierarchy."""
        pages = [{
            "page_number": 1,
            "raw_text": "",
            "headings": [
                {"level": 1, "text": "Introduction"},
                {"level": 3, "text": "Subsection Details"}
            ],
            "tables": []
        }]
        findings = self._run(pages)
        h_findings = [f for f in findings if "skipped heading" in f["title"].lower() or "hierarchy" in f["title"].lower()]
        assert h_findings, "Expected heading hierarchy skip finding"

    def test_broken_numbered_sequence(self):
        """Sections 1, 2, 4 — skipping 3."""
        pages = [
            {"page_number": 1, "raw_text": "1. Introduction\nThis is the introduction.", "headings": [], "tables": []},
            {"page_number": 2, "raw_text": "2. Scope\nThis is the scope.", "headings": [], "tables": []},
            {"page_number": 3, "raw_text": "4. Methodology\nThis section jumps numbering.", "headings": [], "tables": []}
        ]
        findings = self._run(pages)
        num_findings = [f for f in findings if "numbering" in f["title"].lower() or "sequence" in f["title"].lower() or "jumped" in f["title"].lower()]
        assert num_findings, "Expected broken section sequence finding"

    def test_empty_table_flagged(self):
        """A table with no data should produce a structural finding."""
        pages = [{
            "page_number": 2,
            "raw_text": "The following table shows results:",
            "headings": [],
            "tables": [{"data": [["", "", ""], ["", "", ""]]}]
        }]
        findings = self._run(pages)
        table_findings = [f for f in findings if "empty table" in f["title"].lower()]
        assert table_findings, "Expected empty table finding"

    def test_unexpected_blank_page(self):
        """A blank page sandwiched between populated pages should be flagged."""
        pages = [
            {"page_number": 1, "raw_text": "This is the introduction.", "headings": [], "tables": []},
            {"page_number": 2, "raw_text": "", "headings": [], "tables": []},
            {"page_number": 3, "raw_text": "This is the conclusion.", "headings": [], "tables": []}
        ]
        findings = self._run(pages)
        blank_page_findings = [f for f in findings if "blank page" in f["title"].lower()]
        assert blank_page_findings, "Expected unexpected blank page finding"
        assert blank_page_findings[0]["page_number"] == 2


# ---------------------------------------------------------------------------
# Integration: Deduplication Stage
# ---------------------------------------------------------------------------

class TestDeduplicationStage:

    def test_deduplication_removes_exact_duplicates(self):
        """Same category + page + content should collapse to one finding."""
        import asyncio
        from app.document_processing.stages.deduplication import FindingDeduplicationStage

        raw = [
            {"category": "micro_typography", "page_number": 1, "original_content": "recieve", "suggested_correction": "receive", "title": "Typo", "explanation": "...", "severity": "medium", "confidence": 0.9},
            {"category": "micro_typography", "page_number": 1, "original_content": "recieve", "suggested_correction": "receive", "title": "Typo", "explanation": "...", "severity": "medium", "confidence": 0.9},
        ]

        result = asyncio.run(FindingDeduplicationStage.process(raw))
        assert len(result) == 1, f"Expected 1 deduplicated result, got {len(result)}"

    def test_deduplication_keeps_distinct_findings(self):
        """Different categories or pages should produce separate entries."""
        import asyncio
        from app.document_processing.stages.deduplication import FindingDeduplicationStage

        raw = [
            {"category": "micro_typography", "page_number": 1, "original_content": "recieve", "suggested_correction": "receive", "title": "Typo", "explanation": "...", "severity": "medium", "confidence": 0.9},
            {"category": "grammar", "page_number": 1, "original_content": "recieve", "suggested_correction": "receive", "title": "Grammar", "explanation": "...", "severity": "medium", "confidence": 0.9},
            {"category": "micro_typography", "page_number": 2, "original_content": "recieve", "suggested_correction": "receive", "title": "Typo p2", "explanation": "...", "severity": "medium", "confidence": 0.9},
        ]

        result = asyncio.run(FindingDeduplicationStage.process(raw))
        assert len(result) == 3, f"Expected 3 distinct findings, got {len(result)}"

    def test_severity_normalization(self):
        """Unknown severity values should be normalized to 'medium'."""
        import asyncio
        from app.document_processing.stages.deduplication import FindingDeduplicationStage

        raw = [
            {"category": "structural", "page_number": 1, "original_content": "Bad section", "suggested_correction": "Fix it", "title": "X", "explanation": "...", "severity": "UNKNOWN_LEVEL", "confidence": 0.8}
        ]
        result = asyncio.run(FindingDeduplicationStage.process(raw))
        assert result[0]["severity"] == "medium"

    def test_empty_original_content_filtered(self):
        """Findings with empty original_content should be dropped."""
        import asyncio
        from app.document_processing.stages.deduplication import FindingDeduplicationStage

        raw = [
            {"category": "structural", "page_number": 1, "original_content": "", "suggested_correction": "X", "title": "empty", "explanation": "...", "severity": "low", "confidence": 0.5}
        ]
        result = asyncio.run(FindingDeduplicationStage.process(raw))
        assert len(result) == 0, "Expected empty content finding to be filtered"


# ---------------------------------------------------------------------------
# Reporting Stage
# ---------------------------------------------------------------------------

class TestReportingStage:

    def test_severity_summary_counts(self):
        import asyncio
        from app.document_processing.stages.reporting import ReportGenerationStage

        findings = [
            {"severity": "critical", "original_content": "A"},
            {"severity": "high", "original_content": "B"},
            {"severity": "high", "original_content": "C"},
            {"severity": "medium", "original_content": "D"},
            {"severity": "info", "original_content": "E"}
        ]

        report = asyncio.run(ReportGenerationStage.process(findings))
        s = report["summary"]
        assert s["total_findings"] == 5
        assert s["critical_severity"] == 1
        assert s["high_severity"] == 2
        assert s["medium_severity"] == 1
        assert s["info_severity"] == 1


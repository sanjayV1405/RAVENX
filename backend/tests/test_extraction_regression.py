import os
import pytest
from app.document_processing.extractors.pdf_extractor import PDFExtractor
from app.inspection_engine.table_validator import TableArithmeticValidator
from app.inspection_engine.micro_typography import MicroTypographyInspector
from app.inspection_engine.grammar import GrammarInspector
from app.inspection_engine.consistency import EntityConsistencyInspector


def test_table_arithmetic_installation_discrepancy():
    """
    Test Coimbatore/Erode/Salem installation discrepancy:
    52 + 41 + 35 = 128 != stated 138 -> must flag as discrepancy.
    Late jobs: 6 + 5 + 6 = 17 == stated 17 -> must NOT flag.
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 1,
                "structured_data": {
                    "tables": [
                        {
                            "table_index": 1,
                            "bbox": [50.0, 200.0, 500.0, 400.0],
                            "row_count": 5,
                            "col_count": 3,
                            "rows": [
                                ["Region", "Installations", "Late jobs"],
                                ["Coimbatore", "52", "6"],
                                ["Erode", "41", "5"],
                                ["Salem", "35", "6"],
                                ["Total", "138", "17"]
                            ]
                        }
                    ]
                }
            }
        ]
    }

    findings = TableArithmeticValidator.inspect(sample_extraction)

    # Must flag Installations discrepancy
    installation_findings = [f for f in findings if "Installations" in f["title"]]
    assert len(installation_findings) == 1
    assert installation_findings[0]["finding_classification"] == "A"
    assert "128" in installation_findings[0]["explanation"]
    assert "138" in installation_findings[0]["explanation"]
    assert installation_findings[0]["severity"] == "high"

    # Late jobs is 6+5+6=17 == stated 17 -> MUST NOT be flagged!
    late_job_findings = [f for f in findings if "Late jobs" in f["title"]]
    assert len(late_job_findings) == 0


def test_table_arithmetic_indian_format_exact_match():
    """
    Test Indian numbering format sum (e.g. 3,20,000 + 2,15,000 + 1,37,500 + 2,00,000 = 8,72,500).
    When calculated total matches stated total, zero findings must be reported.
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 2,
                "structured_data": {
                    "tables": [
                        {
                            "table_index": 1,
                            "rows": [
                                ["Cost category", "Actual amount (I)"],
                                ["Equipment upgrades", "3,20,000"],
                                ["Travel and field allowance", "2,15,000"],
                                ["Software licenses and tooling", "1,37,500"],
                                ["Staff training", "2,00,000"],
                                ["Total", "8,72,500"]
                            ]
                        }
                    ]
                }
            }
        ]
    }

    findings = TableArithmeticValidator.inspect(sample_extraction)
    assert len(findings) == 0


def test_repeated_word_source_defect():
    """
    Repeated consecutive words such as 'improve improve' must be flagged as
    a genuine source document defect (Classification A).
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 1,
                "raw_text": "We need to improve improve response consistency across regional hubs."
            }
        ]
    }

    findings = MicroTypographyInspector.inspect(sample_extraction)
    dup_findings = [f for f in findings if "improve" in f["title"].lower()]
    assert len(dup_findings) >= 1
    assert dup_findings[0]["finding_classification"] == "A"
    assert dup_findings[0]["suggested_correction"] == "improve"


def test_table_cell_concatenation_marked_as_extraction_uncertainty():
    """
    A token like 'Coimbatore526' occurring in a table-flagged block must be
    classified as 'B' (Extraction Uncertainty / Artifact), not 'A'.
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 1,
                "structured_data": {
                    "blocks": [
                        {
                            "bbox": [50.0, 200.0, 200.0, 250.0],
                            "text": "Coimbatore526",
                            "is_table_block": True
                        }
                    ]
                }
            }
        ]
    }

    findings = MicroTypographyInspector.inspect(sample_extraction)
    table_artifacts = [f for f in findings if "Coimbatore" in f["title"] or "Coimbatore" in f["original_content"]]
    assert len(table_artifacts) >= 1
    assert table_artifacts[0]["finding_classification"] == "B"
    assert table_artifacts[0]["confidence"] <= 0.75


def test_grammar_subject_verb_agreement():
    """
    Verify subject-verb agreement inspection:
    1. 'all regional teams was aligned' -> 'teams were'
    2. 'each regional lead are responsible' -> 'lead is'
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 1,
                "raw_text": "During Q2, all regional teams was aligned on targets, but each regional lead are responsible for reporting."
            }
        ]
    }

    findings = GrammarInspector.inspect(sample_extraction)
    sv_findings = [f for f in findings if f["category"] == "grammar"]
    assert len(sv_findings) >= 2
    for f in sv_findings:
        assert f["finding_classification"] == "A"

    teams_was = [f for f in sv_findings if "teams was" in f["original_content"].lower()]
    assert len(teams_was) == 1
    assert "were" in teams_was[0]["suggested_correction"].lower()

    lead_are = [f for f in sv_findings if "lead are" in f["original_content"].lower()]
    assert len(lead_are) == 1
    assert "is" in lead_are[0]["suggested_correction"].lower()


def test_organization_name_drift():
    """
    Verify corporate entity name styling drift:
    'NORTHSTAR OFFICE SYSTEMS' vs 'North Star Office Systems' across pages.
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 1,
                "raw_text": "NORTHSTAR OFFICE SYSTEMS quarterly operations review report."
            },
            {
                "page_number": 2,
                "raw_text": "Approved by North Star Office Systems executive board."
            }
        ]
    }

    findings = EntityConsistencyInspector.inspect(sample_extraction)
    org_findings = [f for f in findings if "organization name styling" in f["title"].lower()]
    assert len(org_findings) == 1
    assert org_findings[0]["finding_classification"] == "A"
    assert org_findings[0]["severity"] == "high"


def test_chronological_milestone_contradiction():
    """
    Approval date preceding Review date is a contextual logic error (Classification D).
    """
    sample_extraction = {
        "pages": [
            {
                "page_number": 1,
                "raw_text": "Review date: 30 June 2026\nApproval date: 12 June 2026"
            }
        ]
    }

    findings = EntityConsistencyInspector.inspect(sample_extraction)
    date_findings = [f for f in findings if "chronological inconsistency" in f["title"].lower()]
    assert len(date_findings) == 1
    assert date_findings[0]["finding_classification"] == "D"
    assert date_findings[0]["severity"] == "critical"


def test_pdf_extractor_span_space_awareness():
    """
    Verify PDFExtractor span-aware text building logic.
    """
    # Simulate a PyMuPDF block with multiple spans on a single line separated by a physical gap
    dummy_block = {
        "lines": [
            {
                "bbox": [50.0, 100.0, 200.0, 115.0],
                "spans": [
                    {"text": "Quarterly", "bbox": [50.0, 100.0, 100.0, 115.0]},
                    {"text": "Review", "bbox": [105.0, 100.0, 150.0, 115.0]},  # 5pt gap -> needs space
                    {"text": "Copy", "bbox": [155.0, 100.0, 190.0, 115.0]}     # 5pt gap -> needs space
                ]
            },
            {
                "bbox": [50.0, 120.0, 200.0, 135.0],
                "spans": [
                    {"text": "Northstar", "bbox": [50.0, 120.0, 110.0, 135.0]}
                ]
            }
        ]
    }

    built_text = PDFExtractor._build_block_text(dummy_block)
    # Must have spaces between spans and between lines
    assert built_text == "Quarterly Review Copy Northstar"
    assert "QuarterlyReview" not in built_text

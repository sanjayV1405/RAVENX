import os
import io
import json
import hashlib
import docx
import pptx
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector
from app.correction_engine.output_validator import IndependentOutputValidator

ARTIFACTS_DIR = r"C:\Users\user\.gemini\antigravity\brain\2de0010a-3fd3-4a31-950d-ac0bd3d04363"
BENCHMARK_DIR = r"C:\Users\user\Downloads\RAVENX AI\backend\tests\ground_truth"

def generate_output_artifacts():
    # 1. DOCX Output Generation
    docx_path = os.path.join(BENCHMARK_DIR, "phase9_contract_agreement.docx")
    with open(docx_path, "rb") as f:
        docx_bytes = f.read()
    orig_docx_hash = hashlib.sha256(docx_bytes).hexdigest()

    docx_findings = [
        {"id": "DOCX-1", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 1, "original_content": "Docum ent", "suggested_correction": "Document"},
        {"id": "DOCX-2", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 1, "original_content": "definately", "suggested_correction": "definitely"},
        {"id": "DOCX-3", "category": "grammar", "finding_classification": "A", "is_actionable": True, "page_number": 1, "original_content": "cant", "suggested_correction": "can't"},
        {"id": "DOCX-4", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 1, "original_content": "shall shall", "suggested_correction": "shall"}
    ]

    corr_docx_bytes, d_count, d_log = DOCXCorrector.correct(docx_bytes, docx_findings)
    val_docx = IndependentOutputValidator.validate_output(docx_bytes, corr_docx_bytes, "docx", d_log, orig_docx_hash)

    out_docx_path = os.path.join(ARTIFACTS_DIR, "corrected_phase9_contract_agreement.docx")
    with open(out_docx_path, "wb") as f:
        f.write(corr_docx_bytes)

    # 2. PPTX Output Generation
    pptx_path = os.path.join(BENCHMARK_DIR, "phase9_board_presentation.pptx")
    with open(pptx_path, "rb") as f:
        pptx_bytes = f.read()
    orig_pptx_hash = hashlib.sha256(pptx_bytes).hexdigest()

    pptx_findings = [
        {"id": "PPTX-1", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 1, "original_content": "market    expansion", "suggested_correction": "market expansion"},
        {"id": "PPTX-2", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 2, "original_content": "in order to in order to", "suggested_correction": "in order to"},
        {"id": "PPTX-3", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 3, "original_content": "hasbeen", "suggested_correction": "has been"},
        {"id": "PPTX-4", "category": "micro_typography", "finding_classification": "A", "is_actionable": True, "page_number": 4, "original_content": "strat egy", "suggested_correction": "strategy"}
    ]

    corr_pptx_bytes, p_count, p_log = PPTXCorrector.correct(pptx_bytes, pptx_findings)
    val_pptx = IndependentOutputValidator.validate_output(pptx_bytes, corr_pptx_bytes, "pptx", p_log, orig_pptx_hash)

    out_pptx_path = os.path.join(ARTIFACTS_DIR, "corrected_phase9_board_presentation.pptx")
    with open(out_pptx_path, "wb") as f:
        f.write(corr_pptx_bytes)

    print("DOCX Validation:", val_docx["status"], "| Applied:", d_count)
    print("PPTX Validation:", val_pptx["status"], "| Applied:", p_count)

if __name__ == "__main__":
    generate_output_artifacts()

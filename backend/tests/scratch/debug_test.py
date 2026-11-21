import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio
from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector

async def test():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "b6974764-d9e7-4813-8cad-67e20bd8efd5_RAVENX_AI_intentional_mistakes_test.pdf"))
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    result = await pipeline.execute("RAVENX_AI_intentional_mistakes_test.pdf", file_bytes)
    findings = result.get("findings", [])
    print("=== FINDINGS ===")
    for f in findings:
        print(f"[{f.get('category')}] {f.get('title')} | orig: {repr(f.get('original_content'))} -> corr: {repr(f.get('suggested_correction'))} | act: {f.get('is_actionable')}")

    actionable = [f for f in findings if f.get("is_actionable", True)]
    corrected_bytes, applied_count, applied_log = PDFCorrector.correct(file_bytes, actionable)
    print("\n=== APPLIED LOG ===")
    for item in applied_log:
        print(item)

if __name__ == "__main__":
    asyncio.run(test())

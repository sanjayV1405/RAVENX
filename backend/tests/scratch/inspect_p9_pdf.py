import os
import asyncio
import json
from app.document_processing.pipeline import DocumentInspectionPipeline

async def main():
    p = os.path.join("tests", "ground_truth", "phase9_financial_multipage.pdf")
    with open(p, "rb") as f:
        data = f.read()
    pipeline = DocumentInspectionPipeline(ai_provider="deepseek")
    res = await pipeline.execute("phase9_financial_multipage.pdf", data)
    print("PAGE COUNT:", res["extraction"]["page_count"])
    for i, page in enumerate(res["extraction"]["pages"]):
        print(f"--- PAGE {i+1} RAW TEXT ---")
        print(page.get("raw_text") or page.get("reconstructed_text"))
    print("\nFINDINGS:")
    for f in res["findings"]:
        print(f"- Category: {f.get('category')} | Orig: '{f.get('original_content')}' | Corr: '{f.get('suggested_correction')}' | Page: {f.get('page_number')}")

if __name__ == "__main__":
    asyncio.run(main())

import fitz, sys, asyncio
sys.path.insert(0, 'backend')
from app.document_processing.pipeline import DocumentInspectionPipeline
from app.correction_engine.pdf_corrector import PDFCorrector

async def test():
    with open('backend/tests/ground_truth/synthetic_test_doc.pdf', 'rb') as f:
        file_bytes = f.read()
    pipeline = DocumentInspectionPipeline(ai_provider='deepseek')
    result = await pipeline.execute('synthetic_test_doc.pdf', file_bytes)
    findings = result['findings']
    print(f'Total findings: {len(findings)}')
    for fi in findings:
        cat = fi.get("category", "")
        orig = repr(fi.get("original_content","")[:60])
        corr = repr(fi.get("suggested_correction","")[:40])
        act = fi.get("is_actionable")
        print(f'  [{cat}] orig={orig} -> corr={corr} actionable={act}')
    print()
    corrected_bytes, applied_count, applied_log = PDFCorrector.correct(file_bytes, findings)
    print(f'Applied: {applied_count}')
    for log in applied_log:
        print(f"  Applied: {repr(log.get('original','')[:50])} -> {repr(log.get('corrected','')[:40])}")
    doc = fitz.open(stream=corrected_bytes, filetype='pdf')
    p1 = doc[0].get_text('text')
    p2 = doc[1].get_text('text')
    print()
    print('=== P1 TEXT ===')
    print(repr(p1))
    print()
    print('=== P2 TEXT ===')
    print(repr(p2))
    doc.close()

asyncio.run(test())

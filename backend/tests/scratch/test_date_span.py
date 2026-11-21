import os
import fitz

base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
pdf_path = os.path.join(base, "uploads", "b6974764-d9e7-4813-8cad-67e20bd8efd5_RAVENX_AI_intentional_mistakes_test.pdf")
doc = fitz.open(pdf_path)
p2 = doc[1]
rects = p2.search_for('12 June 2026')
print('Search for "12 June 2026":', rects)

from app.correction_engine.pdf_corrector import PDFCorrector
for r in rects:
    font, sz, col, base, span_text, span_rect = PDFCorrector._discover_font_baseline_and_span(p2, r)
    print('Discovered:', font, sz, col, base, repr(span_text), span_rect)

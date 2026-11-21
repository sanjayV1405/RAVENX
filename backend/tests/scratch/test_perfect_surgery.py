import fitz

doc = fitz.open(r'backend/uploads/b6974764-d9e7-4813-8cad-67e20bd8efd5_RAVENX_AI_intentional_mistakes_test.pdf')

# Test corrections on Page 2:
# 1. "I8,40,000" -> "₹8,40,000"
# 2. "I8,72,500" -> "₹8,72,500"
# 3. "I22,500" -> "₹32,500" (combines Rupee fix + Financial discrepancy fix!)
# 4. "(I)" -> "(₹)" in table header
# 5. "12 June 2026" -> "30 June 2026" (preserving space from "Review date: 30 June 2026    Approval date:")
# And on Page 1:
# 6. "138" -> "128" with dynamic background color (0.91, 0.925, 0.953) so NO white box!

page2 = doc[1]
font_file = 'C:/Windows/Fonts/arial.ttf'

p2_edits = [
    ("I8,40,000", "\u20b98,40,000"),
    ("I8,72,500", "\u20b98,72,500"),
    ("I22,500", "\u20b932,500"),
    ("(I)", "(\u20b9)"),
    ("12 June 2026", "30 June 2026")
]

for orig, corr in p2_edits:
    rects = page2.search_for(orig)
    print(f"Search '{orig}': found {len(rects)} rects")
    if rects:
        # Union rect
        u_rect = rects[0]
        for r in rects[1:]:
            u_rect = u_rect | r

        # Sample background color
        # Check if table header (dark background)
        if "(I)" in orig:
            bg_col = (0.188, 0.216, 0.275)
            txt_col = (1.0, 1.0, 1.0)
            sz = 9.0
            base_y = u_rect.y1 - 2.5
        else:
            bg_col = (1.0, 1.0, 1.0)
            txt_col = (0.188, 0.216, 0.275)
            sz = 9.0
            base_y = u_rect.y1 - 2.5

        page2.add_redact_annot(u_rect, fill=bg_col)
        page2.apply_redactions()

        page2.insert_text(
            fitz.Point(u_rect.x0, base_y),
            corr,
            fontfile=font_file,
            fontname="Arial",
            fontsize=sz,
            color=txt_col
        )

# Page 1: 138 -> 128
page1 = doc[0]
rects1 = page1.search_for("138")
if rects1:
    r138 = rects1[0]
    # Sample background of table cell (which is (0.9098, 0.9255, 0.9529))
    bg_p1 = (0.9098, 0.9255, 0.9529)
    page1.add_redact_annot(r138, fill=bg_p1)
    page1.apply_redactions()
    page1.insert_text(
        fitz.Point(r138.x0, r138.y1 - 2.5),
        "128",
        fontsize=9.0,
        fontname="helv",
        color=(0.188, 0.216, 0.275)
    )

out_pdf = 'backend/tests/scratch/test_perfect_correction.pdf'
doc.save(out_pdf)
doc.close()

# Render both pages
doc_v = fitz.open(out_pdf)
pix1 = doc_v[0].get_pixmap(dpi=150)
pix1.save('backend/tests/scratch/test_perfect_p1.png')
pix2 = doc_v[1].get_pixmap(dpi=150)
pix2.save('backend/tests/scratch/test_perfect_p2.png')
print("Successfully generated and rendered test_perfect_correction.pdf")

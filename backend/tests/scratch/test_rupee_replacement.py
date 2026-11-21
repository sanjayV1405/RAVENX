import fitz

doc = fitz.open(r'backend/uploads/b6974764-d9e7-4813-8cad-67e20bd8efd5_RAVENX_AI_intentional_mistakes_test.pdf')
page = doc[1]

# Find all ZapfDingbats 'I' spans on page 2
target_spans = []
d = page.get_text('dict')
for b in d.get('blocks', []):
    for l in b.get('lines', []):
        for s in l.get('spans', []):
            if s.get('font') == 'ZapfDingbats' and s.get('text') == 'I':
                target_spans.append(s)

print(f'Found {len(target_spans)} ZapfDingbats I spans on page 2:')
for s in target_spans:
    bbox = fitz.Rect(s['bbox'])
    origin = s['origin']
    size = s['size']
    color = s.get('color', 0)
    print('  Target:', bbox, 'origin:', origin, 'size:', size, 'color:', color)

    # For table header with dark background, detect or pass proper fill
    if color == 16777215:  # White text on dark header
        fill = (0.188, 0.216, 0.275)
    else:
        fill = (1, 1, 1)
    page.add_redact_annot(bbox, fill=fill)

page.apply_redactions()

# Insert TrueType Arial font AFTER apply_redactions() with fontfile
font_file = 'C:/Windows/Fonts/arial.ttf'

# Insert the real Rupee symbol ₹ using TrueType Arial
for s in target_spans:
    bbox = fitz.Rect(s['bbox'])
    origin = fitz.Point(s['origin'][0], s['origin'][1])
    size = s['size']
    color = s.get('color', 0)
    if color == 16777215:
        text_color = (1.0, 1.0, 1.0)
    elif isinstance(color, int) and color != 0:
        r = ((color >> 16) & 255) / 255.0
        g = ((color >> 8) & 255) / 255.0
        b = (color & 255) / 255.0
        text_color = (r, g, b)
    else:
        text_color = (0.188, 0.216, 0.275)

    # Insert text with fontfile parameter!
    page.insert_text(origin, '\u20b9', fontfile=font_file, fontname='Arial', fontsize=size, color=text_color)

out_pdf = 'backend/tests/scratch/test_rupee_fixed.pdf'
doc.save(out_pdf)
doc.close()

# Re-open and render to PNG
doc2 = fitz.open(out_pdf)
pix = doc2[1].get_pixmap(dpi=150)
pix.save('backend/tests/scratch/test_rupee_fixed_p2.png')
print('SUCCESS! Rendered test_rupee_fixed_p2.png')

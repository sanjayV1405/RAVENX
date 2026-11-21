import re

lines = [
    "Prepared for: Operations Leadership Team    Document ID: NOS-OPS-Q2-026",
    "Review date: 30 June 2026    Approval date: 12 June 2026",
    "Operations    Leadership"  # This IS excessive spaces inside a title
]

pattern = re.compile(r'(\b[a-zA-Z0-9_\-]+)\s{2,}([a-zA-Z0-9_\-]+\b)')

def is_field_separator(text, match):
    line_context = text[max(0, match.start() - 40):min(len(text), match.end() + 40)]
    w2 = match.group(2)
    after_match = text[match.end():min(len(text), match.end() + 20)]
    # Check if w2 is part of a metadata label like 'Document ID' or 'Approval date'
    if re.search(r'^(?:Document\s+ID|Doc\s+ID|Approval\s+date|Review\s+date|Date|Page|Ref|Version|Status)\b', w2 + after_match, re.IGNORECASE):
        return True
    # Check if line has multiple key-value pairs with colons separated by spaces
    if re.search(r':.*?(\s{2,}).*?:', line_context):
        return True
    return False

for l in lines:
    for m in pattern.finditer(l):
        sep = is_field_separator(l, m)
        print(f'Match "{m.group(0)}" in "{l[:30]}...": is_field_separator = {sep}')

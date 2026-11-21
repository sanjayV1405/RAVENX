import re

text = """The approved operating budget for Q2 was I8,40,000. Actual expenditure was I8,72,500, resulting in an overrun of
I22,500. The finance team will review recurring vendor charges before the next reporting cycle."""

# Consistency engine
variance_pattern = re.compile(
    r'(?:approved|operating|project|allocated)\s+(?:operating\s+)?budget\s+(?:for\s+[^.]+?)?was\s+([I₹$€£]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?).*?'
    r'actual\s+(?:operating\s+)?expenditure\s+(?:for\s+[^.]+?)?was\s+([I₹$€£]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?).*?'
    r'(?:resulting\s+in\s+an?\s+)?overrun\s+of\s+([I₹$€£]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?)',
    re.IGNORECASE | re.DOTALL
)

m = variance_pattern.search(text)
if m:
    b_val = float(m.group(2).rstrip(',').replace(",", ""))
    a_val = float(m.group(4).rstrip(',').replace(",", ""))
    o_val = float(m.group(6).rstrip(',').replace(",", ""))
    calc = a_val - b_val
    curr_prefix = m.group(5) or ""
    orig_token = f"{curr_prefix}{m.group(6).rstrip(',')}"
    corr_token = f"₹{int(calc):,}"
    print(f"Consistency Engine: orig={repr(orig_token)} -> corr={repr(corr_token)}")

# Micro typography Rule 13
corrupt_curr_pattern = re.compile(r'(?<=\s|\()I(?=[0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?|\))')
for cm in corrupt_curr_pattern.finditer(text):
    before_match = text[max(0, cm.start() - 25):cm.start()].lower()
    if "overrun" in before_match:
        print(f"Micro-Typography: Skipped overrun token at {cm.span()}")
        continue
    after_idx = cm.end()
    rest = text[after_idx:min(len(text), after_idx + 15)]
    amt_match = re.match(r'^[0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?', rest)
    if amt_match:
        full_token = f"I{amt_match.group(0)}"
        corr_token = f"₹{amt_match.group(0)}"
        print(f"Micro-Typography: orig={repr(full_token)} -> corr={repr(corr_token)}")

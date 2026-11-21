import re

text = """The approved operating budget for Q2 was I8,40,000. Actual expenditure was I8,72,500, resulting in an overrun of
I22,500. The finance team will review recurring vendor charges before the next reporting cycle."""

variance_pattern = re.compile(
    r'(?:approved|operating|project|allocated)\s+(?:operating\s+)?budget\s+(?:for\s+[^.]+?)?was\s+([I₹$€£]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?).*?'
    r'actual\s+(?:operating\s+)?expenditure\s+(?:for\s+[^.]+?)?was\s+([I₹$€£]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?).*?'
    r'(?:resulting\s+in\s+an?\s+)?overrun\s+of\s+([I₹$€£]|Rs\.?)?\s*([0-9,]+(?:\.[0-9]+)?)',
    re.IGNORECASE | re.DOTALL
)

m = variance_pattern.search(text)
print("Match found:", bool(m))
if m:
    print("Groups:", m.groups())
    b_str = m.group(2)
    a_str = m.group(4)
    o_str = m.group(6)
    b_val = float(b_str.replace(",", ""))
    a_val = float(a_str.replace(",", ""))
    o_val = float(o_str.replace(",", ""))
    calc_diff = a_val - b_val
    print(f"Budget: {b_val}, Actual: {a_val}, Stated: {o_val}, Calculated: {calc_diff}")

import re
from typing import Dict, Any, List, Optional, Tuple


class TableArithmeticValidator:
    """
    Module T: Spatially-Grounded Table Arithmetic Validator
    Validates arithmetic integrity in tabular structures:
    - Identifies header rows, data rows, and summary/total rows.
    - Accurately parses international & Indian number formats (e.g., '1,234.56', '3,20,000').
    - Performs column-wise sum validation for numeric columns with stated totals.
    - Compares calculated column totals against explicitly stated totals.
    - Flags true arithmetic discrepancies as Source Document Defects (Classification A).
    - Carefully ignores matching totals (e.g. late jobs: 6 + 5 + 6 = 17 vs stated 17).
    - Ignores percentage columns, identifier columns (dates, years, IDs), and mixed non-numeric data.
    """

    TOTAL_KEYWORDS = {"total", "grand total", "subtotal", "sub-total", "sum", "overall"}

    @classmethod
    def _parse_numeric(cls, val_str: str) -> Optional[float]:
        """Parses an integer or floating-point number from a string,
        handling commas (standard and Indian format), currency symbols, etc."""
        if not val_str or not isinstance(val_str, str):
            return None
        cleaned = val_str.strip()
        # Remove currency symbols and common indicators
        cleaned = re.sub(r'^[₹$€£I\s]+', '', cleaned)
        cleaned = cleaned.replace(',', '').strip()
        # Ensure it looks like a valid number
        if re.match(r'^-?[0-9]+(?:\.[0-9]+)?$', cleaned):
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @classmethod
    def inspect(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        pages = extraction_data.get("pages", [])

        for page in pages:
            page_num = page.get("page_number", 1)
            # Find tables from structured_data or page.get("tables")
            structured = page.get("structured_data", {})
            tables = structured.get("tables", []) or page.get("tables", [])

            for t_idx, table in enumerate(tables):
                rows = []
                bbox = None
                if isinstance(table, dict):
                    rows = table.get("rows", []) or table.get("data", [])
                    bbox = table.get("bbox")
                elif isinstance(table, list):
                    rows = table

                if not rows or len(rows) < 3:
                    # Need at least header, at least one data row, and total row
                    continue

                table_findings = cls._validate_table(rows, page_num=page_num, bbox=bbox, table_idx=t_idx + 1)
                findings.extend(table_findings)

        return findings

    @classmethod
    def _validate_table(
        cls,
        rows: List[List[Any]],
        page_num: int,
        bbox: Optional[List[float]],
        table_idx: int
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        # 1. Identify header row (typically row 0)
        header_row = [str(c).strip() if c is not None else "" for c in rows[0]]
        num_cols = len(header_row)

        # 2. Identify total row (usually the last row or row containing 'total')
        total_row_idx = None
        for r_idx in range(len(rows) - 1, 0, -1):
            row_str = " ".join(str(c).lower().strip() for c in rows[r_idx] if c is not None)
            if any(k in row_str for k in cls.TOTAL_KEYWORDS):
                total_row_idx = r_idx
                break

        if total_row_idx is None:
            return findings

        data_rows = rows[1:total_row_idx]
        total_row = rows[total_row_idx]

        if not data_rows:
            return findings

        # 3. For each column, check if all data rows and total row have valid numeric values
        for col_idx in range(num_cols):
            if col_idx >= len(total_row):
                continue

            col_header = header_row[col_idx] if col_idx < len(header_row) else f"Column {col_idx+1}"
            header_lower = col_header.lower()

            # Skip year / ID / index / percentage columns
            if any(skip_word in header_lower for skip_word in ["year", "date", "no.", "id", "#", "%", "percent", "ratio", "rate"]):
                continue

            raw_stated_str = str(total_row[col_idx]).strip() if col_idx < len(total_row) and total_row[col_idx] is not None else ""
            stated_total_val = cls._parse_numeric(raw_stated_str)
            if stated_total_val is None:
                continue

            # Parse data row values
            data_values: List[Tuple[str, float]] = []
            all_valid = True
            for r in data_rows:
                if col_idx >= len(r) or r[col_idx] is None:
                    all_valid = False
                    break
                cell_raw = str(r[col_idx]).strip()
                val = cls._parse_numeric(cell_raw)
                if val is None:
                    all_valid = False
                    break
                # Get row label from first column
                row_label = str(r[0]).strip() if len(r) > 0 and r[0] is not None else f"Row {len(data_values)+1}"
                data_values.append((row_label, val))

            if not all_valid or len(data_values) < 2:
                continue

            # 4. Currency uniformity check across data rows
            currencies_in_col = set()
            for r in data_rows:
                if col_idx < len(r) and r[col_idx] is not None:
                    raw_str = str(r[col_idx]).strip()
                    curr_match = re.search(r'([₹$€£]|USD|EUR|GBP|Rs\.?)', raw_str)
                    if curr_match:
                        currencies_in_col.add(curr_match.group(1))

            if len(currencies_in_col) > 1:
                findings.append({
                    "category": "consistency",
                    "title": f"Inconsistent currency symbols in column '{col_header}'",
                    "finding_classification": "D",
                    "is_actionable": False,
                    "page_number": page_num,
                    "original_content": f"Currencies found: {', '.join(sorted(currencies_in_col))}",
                    "suggested_correction": "Standardize on a single uniform currency unit",
                    "explanation": f"Column '{col_header}' contains conflicting currency denominations: {', '.join(sorted(currencies_in_col))}.",
                    "severity": "medium",
                    "confidence": 0.92,
                    "evidence_source": "table_arithmetic_validator",
                    "bbox": bbox,
                    "detection_method": "geometry_analysis"
                })

            # Compute sum
            computed_total = sum(v[1] for v in data_values)
            # Handle float precision
            discrepancy = computed_total - stated_total_val

            # If discrepancy is non-zero (allowing small float epsilon)
            if abs(discrepancy) > 0.01:
                # Format cell-level evidence breakdown
                calc_breakdown = " + ".join(
                    f"{v[1]:g}" if v[1].is_integer() else f"{v[1]:.2f}"
                    for v in data_values
                )
                stated_str = raw_stated_str if raw_stated_str else (f"{stated_total_val:g}" if stated_total_val.is_integer() else f"{stated_total_val:.2f}")

                # Format computed total preserving comma styling if present in original
                if "," in raw_stated_str:
                    s_int = str(int(computed_total))
                    # Check if Indian numbering format (comma after 3 digits, then groups of 2)
                    clean_digits = re.sub(r'[^0-9]', '', raw_stated_str)
                    is_indian = bool(len(clean_digits) > 4 and len(raw_stated_str.replace(" ", "").split(",")[-2]) == 2)
                    if is_indian and len(s_int) > 3:
                        last3 = s_int[-3:]
                        rest = s_int[:-3]
                        parts = []
                        while len(rest) > 2:
                            parts.insert(0, rest[-2:])
                            rest = rest[:-2]
                        if rest:
                            parts.insert(0, rest)
                        computed_str = ",".join(parts) + "," + last3
                    else:
                        computed_str = f"{int(computed_total):,}" if computed_total.is_integer() else f"{computed_total:,.2f}"
                else:
                    computed_str = f"{computed_total:g}" if computed_total.is_integer() else f"{computed_total:.2f}"

                diff_str = f"{abs(discrepancy):g}" if abs(discrepancy).is_integer() else f"{abs(discrepancy):.2f}"
                sign_str = "+" if discrepancy > 0 else "-"

                details = ", ".join(f"{v[0]}: {v[1]:g}" for v in data_values)

                findings.append({
                    "category": "consistency",
                    "title": f"Arithmetic calculation discrepancy in table total ('{col_header}')",
                    "finding_classification": "A",  # Confirmed source document arithmetic defect
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": stated_str,
                    "suggested_correction": computed_str,
                    "explanation": (
                        f"In Table {table_idx} ('{col_header}'), the calculated sum of component rows is {calc_breakdown} = {computed_str}, "
                        f"which conflicts with the stated total of {stated_str} (discrepancy of {sign_str}{diff_str}). Components: {details}."
                    ),
                    "severity": "high",
                    "confidence": 0.99,
                    "evidence_source": "table_arithmetic_validator",
                    "bbox": bbox,
                    "char_offset_start": None,
                    "char_offset_end": None,
                    "detection_method": "geometry_analysis"
                })

        return findings

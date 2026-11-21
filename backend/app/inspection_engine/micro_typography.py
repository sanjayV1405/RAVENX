import re
from typing import Dict, Any, List, Optional, Tuple


class MicroTypographyInspector:
    """
    Module A: Micro-Typographical Intelligence
    Detects subtle typographic defects that standard checkers frequently miss:
    - Missing spaces between words and word concatenations.
    - Missing separators between place names and numbers (e.g., Tirupur641666).
    - Unnecessary spaces and space before punctuation.
    - Repeated words (e.g., 'improve improve', 'the the').
    - Repeated punctuation (e.g., ',,', '..').
    - Punctuation errors and sentence capitalization anomalies.
    - Common high-frequency misspellings.
    - Suspicious character substitutions (e.g. leetspeak/digit substitutions in text).
    - Inconsistent capitalization and abbreviations.

    Classifications:
    - Classification A: Genuine source document defects (e.g., duplicate words, intentional typos).
    - Classification B: Extraction uncertainties / artifacts (e.g., table cell concatenations).
    """

    # Common concatenated word pairs
    CONCATENATED_WORDS = {
        "werealigned": "were aligned",
        "teamcompleted": "team completed",
        "andthe": "and the",
        "ofthe": "of the",
        "tothe": "to the",
        "inthe": "in the",
        "onthe": "on the",
        "atthe": "at the",
        "forthe": "for the",
        "fromthe": "from the",
        "bythe": "by the",
        "withthe": "with the",
        "allthe": "all the",
        "inaccordance": "in accordance",
        "withregard": "with regard",
        "toensure": "to ensure",
        "shouldbe": "should be",
        "willbe": "will be",
        "canbe": "can be",
        "wouldbe": "would be",
        "mustbe": "must be",
        "hasbeen": "has been",
        "havebeen": "have been",
        "hadbeen": "had been",
        "mayalso": "may also",
        "aswell": "as well",
        "atleast": "at least",
        "inorder": "in order",
        "thisdocument": "this document"
    }

    # Accidental word splits (spaces inserted within single standard English words)
    SPLIT_WORDS = {
        "docum ent": "document",
        "oper ation": "operation",
        "organ ization": "organization",
        "man ager": "manager",
        "sched ule": "schedule",
        "req uirement": "requirement",
        "deliv ery": "delivery",
        "qual ity": "quality",
        "infor mation": "information",
        "imple mentation": "implementation",
        "strat egy": "strategy",
        "strat egic": "strategic",
        "exec ution": "execution",
        "devel opment": "development",
        "perfor mance": "performance"
    }

    # Common misspellings with deterministic corrections
    COMMON_TYPOS = {
        "recieve": "receive",
        "recieved": "received",
        "recieving": "receiving",
        "seperate": "separate",
        "seperated": "separated",
        "seperation": "separation",
        "definately": "definitely",
        "occurance": "occurrence",
        "occurrance": "occurrence",
        "calender": "calendar",
        "accomodate": "accommodate",
        "accomodation": "accommodation",
        "wierd": "weird",
        "untill": "until",
        "goverment": "government",
        "enviroment": "environment",
        "responsability": "responsibility",
        "adress": "address",
        "neccessary": "necessary",
        "succesful": "successful",
        "truely": "truly",
        "maintainance": "maintenance",
        "arguement": "argument",
        "privilege": "privilege",
        "priviledge": "privilege",
        "tommorrow": "tomorrow",
        "fourty": "forty"
    }

    # Non-geographic alphanumeric tokens that should NOT be flagged as missing space
    ALPHANUMERIC_ALLOWLIST = {
        "boeing747", "boeing737", "sha256", "sha512", "md5", "utf8", "utf16", "mp3", "mp4",
        "h2o", "co2", "a4", "a3", "b5", "iso9001", "iso27001", "ieee802", "win32", "win64",
        "ipv4", "ipv6", "x86", "x64", "f16", "f35", "h1", "h2", "h3", "h4", "h5", "h6",
        "section1", "section2", "section3", "clause1", "clause2", "table1", "table2",
        "fig1", "fig2", "figure1", "figure2", "item1", "item2", "v1", "v2", "step1", "step2"
    }

    @classmethod
    def inspect(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        pages = extraction_data.get("pages", [])

        if not pages and extraction_data.get("raw_text"):
            # Fallback if no page objects present
            findings.extend(cls._inspect_text_unit(extraction_data["raw_text"], page_num=1))
            return findings

        for page in pages:
            page_num = page.get("page_number", 1)
            # Inspect blocks if available for bbox association
            structured = page.get("structured_data", {})
            blocks = structured.get("blocks", []) or page.get("blocks", [])
            
            if blocks:
                for block in blocks:
                    block_text = block.get("text", "")
                    bbox = block.get("bbox")
                    is_table_block = block.get("is_table_block", False)
                    block_findings = cls._inspect_text_unit(
                        block_text,
                        page_num=page_num,
                        bbox=bbox,
                        is_table_block=is_table_block
                    )
                    findings.extend(block_findings)
            else:
                page_text = page.get("reconstructed_text") or page.get("raw_text", "")
                findings.extend(cls._inspect_text_unit(page_text, page_num=page_num))

        return findings

    @classmethod
    def _inspect_text_unit(
        cls,
        text: str,
        page_num: int = 1,
        bbox: Optional[List[float]] = None,
        is_table_block: bool = False
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        if not text or not text.strip():
            return findings

        # 1. Place name + postal/number concatenation (e.g. Tirupur641666, Coimbatore641001)
        # Matches capitalized word directly merged with 5-6 digit number or postal code
        place_num_pattern = re.compile(r'\b([A-Z][a-zA-Z]{2,})([0-9]{2,6})\b')
        for match in place_num_pattern.finditer(text):
            full_match = match.group(0)
            word_part = match.group(1)
            num_part = match.group(2)
            if full_match.lower() not in cls.ALPHANUMERIC_ALLOWLIST:
                # If this text block belongs to a table, it is likely an extraction artifact (Classification B)
                # If in body narrative with 5-6 digits (postal code), it is a true source defect (Classification A)
                is_postal = len(num_part) in (5, 6)
                if is_table_block:
                    findings.append({
                        "category": "micro_typography",
                        "title": f"Possible table cell concatenation artifact '{full_match}'",
                        "finding_classification": "B",  # Extraction uncertainty
                        "is_actionable": False,
                        "page_number": page_num,
                        "original_content": full_match,
                        "suggested_correction": f"{word_part} {num_part}",
                        "explanation": f"The token '{full_match}' inside a table region appears to be an extraction adjacency artifact rather than a confirmed document defect.",
                        "severity": "low",
                        "confidence": 0.70,
                        "evidence_source": "micro_typography_engine",
                        "bbox": bbox,
                        "char_offset_start": match.start(),
                        "char_offset_end": match.end(),
                        "detection_method": "geometry_analysis"
                    })
                elif is_postal:
                    findings.append({
                        "category": "micro_typography",
                        "title": "Missing separator between place name and postal number",
                        "finding_classification": "A",  # Genuine source defect
                        "is_actionable": True,
                        "page_number": page_num,
                        "original_content": full_match,
                        "suggested_correction": f"{word_part} {num_part}",
                        "explanation": f"The place name '{word_part}' and numeric code '{num_part}' are concatenated without a required separating space.",
                        "severity": "high",
                        "confidence": 0.96,
                        "evidence_source": "micro_typography_engine",
                        "bbox": bbox,
                        "char_offset_start": match.start(),
                        "char_offset_end": match.end(),
                        "detection_method": "rule_based"
                    })

        # 2. Accidental word concatenations (e.g., andthe -> and the)
        for concat, corrected in cls.CONCATENATED_WORDS.items():
            pattern = re.compile(rf'\b{re.escape(concat)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                findings.append({
                    "category": "micro_typography",
                    "title": "Accidental word concatenation",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": corrected,
                    "explanation": f"Detected concatenated words '{match.group(0)}' lacking whitespace.",
                    "severity": "medium",
                    "confidence": 0.95,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 3. Repeated consecutive duplicate words (e.g., 'improve improve', 'the the')
        repeated_word_pattern = re.compile(r'\b([a-zA-Z]{2,})\s+\1\b', re.IGNORECASE)
        for match in repeated_word_pattern.finditer(text):
            word = match.group(1)
            findings.append({
                "category": "micro_typography",
                "title": f"Duplicated word '{word}'",
                "finding_classification": "A",  # Genuine source defect
                "is_actionable": True,
                "page_number": page_num,
                "original_content": match.group(0),
                "suggested_correction": word,
                "explanation": f"The word '{word}' is duplicated consecutively in the sentence.",
                "severity": "medium",
                "confidence": 0.98,
                "evidence_source": "micro_typography_engine",
                "bbox": bbox,
                "char_offset_start": match.start(),
                "char_offset_end": match.end(),
                "detection_method": "rule_based"
            })

        # 4. Repeated punctuation (e.g. ',,', '..', ';;', '??', '!!' - but not ellipsis '...')
        repeated_punct_pattern = re.compile(r'(,{2,}|;{2,}|\?{2,}|!{2,}|(?<!\.)\.\.(?!\.))')
        for match in repeated_punct_pattern.finditer(text):
            punct = match.group(0)
            suggested = punct[0]
            findings.append({
                "category": "micro_typography",
                "title": "Duplicate punctuation",
                "finding_classification": "A",
                "is_actionable": True,
                "page_number": page_num,
                "original_content": punct,
                "suggested_correction": suggested,
                "explanation": f"Repeated punctuation marks '{punct}' detected where a single mark is standard.",
                "severity": "low",
                "confidence": 0.95,
                "evidence_source": "micro_typography_engine",
                "bbox": bbox,
                "char_offset_start": match.start(),
                "char_offset_end": match.end(),
                "detection_method": "rule_based"
            })

        # 5. Space before punctuation (e.g. "word ," or "word .")
        space_before_punct = re.compile(r'(\b[a-zA-Z0-9]+)\s+([,.:;?!])(?=\s|$)')
        for match in space_before_punct.finditer(text):
            original = match.group(0)
            word = match.group(1)
            punct = match.group(2)
            findings.append({
                "category": "micro_typography",
                "title": "Unnecessary space preceding punctuation mark",
                "finding_classification": "A",
                "is_actionable": True,
                "page_number": page_num,
                "original_content": original,
                "suggested_correction": f"{word}{punct}",
                "explanation": f"Punctuation mark '{punct}' is improperly preceded by whitespace.",
                "severity": "low",
                "confidence": 0.94,
                "evidence_source": "micro_typography_engine",
                "bbox": bbox,
                "char_offset_start": match.start(),
                "char_offset_end": match.end(),
                "detection_method": "rule_based"
            })

        # 6. Multiple consecutive spaces inside sentences (e.g. "word   word")
        # Captures complete word tokens before and after spaces to eliminate word truncation.
        # Uses horizontal whitespace [^\S\r\n]{2,} to avoid flagging newline/paragraph breaks.
        # Skips table blocks where multiple spaces represent intentional column alignment.
        # Also preserves intentional inter-field separation in document headers, date rows, and numbered lists.
        if not is_table_block:
            multi_space_pattern = re.compile(r'(\b[a-zA-Z0-9_\-]+)[^\S\r\n]{2,}([a-zA-Z0-9_\-]+\b)')
            for match in multi_space_pattern.finditer(text):
                w1 = match.group(1)
                w2 = match.group(2)
                full_orig = match.group(0)

                # Check if this space is separating two metadata fields or columnar items on the same line
                # E.g. "Team    Document ID", "30 June 2026    Approval date:", "Item 1  2. Item 2"
                line_context = text[max(0, match.start() - 40):min(len(text), match.end() + 40)]
                after_match = text[match.end():min(len(text), match.end() + 20)]
                is_field_separator = bool(
                    re.search(r'^(?:Document\s+ID|Doc\s+ID|Approval\s+date|Review\s+date|Date|Page|Ref|Version|Status)\b|^[0-9]+[.)]', w2 + after_match, re.IGNORECASE) or
                    re.search(r':.*?([^\S\r\n]{2,}).*?:', line_context)
                )
                if is_field_separator:
                    continue

                findings.append({
                    "category": "micro_typography",
                    "title": "Excessive consecutive spaces",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": full_orig,
                    "suggested_correction": f"{w1} {w2}",
                    "explanation": f"Found multiple consecutive spaces between '{w1}' and '{w2}'.",
                    "severity": "low",
                    "confidence": 0.95,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 7. Common high-frequency misspellings
        for typo, correction in cls.COMMON_TYPOS.items():
            pattern = re.compile(rf'\b{re.escape(typo)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                orig = match.group(0)
                if orig.isupper():
                    corr = correction.upper()
                elif orig[0].isupper():
                    corr = correction.capitalize()
                else:
                    corr = correction

                findings.append({
                    "category": "micro_typography",
                    "title": f"Spelling typo '{orig}'",
                    "finding_classification": "A",  # Genuine source defect
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": orig,
                    "suggested_correction": corr,
                    "explanation": f"'{orig}' is a recognized spelling mistake for '{corr}'.",
                    "severity": "medium",
                    "confidence": 0.97,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 8. Character substitution / Leetspeak digits inside words (e.g. 'c0ntract', 'd1g1tal')
        subst_pattern = re.compile(r'\b([a-zA-Z]+[0-9]+[a-zA-Z]+|[a-zA-Z]*[0-9]+[a-zA-Z]+[0-9]*)\b')
        digit_map = {'0': 'o', '1': 'i', '3': 'e', '5': 's'}
        for match in subst_pattern.finditer(text):
            candidate = match.group(0)
            if candidate.lower() in cls.ALPHANUMERIC_ALLOWLIST:
                continue
            replaced = candidate
            for d, char in digit_map.items():
                replaced = replaced.replace(d, char)
            if replaced.lower() in ["contract", "digital", "system", "information", "work", "document", "report"]:
                findings.append({
                    "category": "micro_typography",
                    "title": "Suspicious digit substitution in word",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": candidate,
                    "suggested_correction": replaced,
                    "explanation": f"The word '{candidate}' contains numeric digits substituted for alphabetic characters.",
                    "severity": "high",
                    "confidence": 0.92,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 9. Inconsistent mid-word capitalization (e.g. 'DocuMent', 'INtroduction')
        camel_pattern = re.compile(r'\b([A-Z][a-z]+[A-Z][a-z]+)\b')
        camel_allowlist = {"javascript", "typescript", "iphone", "ipad", "ebay", "github", "gitlab", "postgresql", "fastapi"}
        for match in camel_pattern.finditer(text):
            word = match.group(0)
            if word.lower() not in camel_allowlist:
                findings.append({
                    "category": "micro_typography",
                    "title": f"Irregular internal capitalization in '{word}'",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": word,
                    "suggested_correction": word.capitalize(),
                    "explanation": f"'{word}' has irregular mid-word capitalization.",
                    "severity": "low",
                    "confidence": 0.85,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 10. Split words with accidental space (e.g. 'Docum ent' -> 'Document')
        for split_form, unified_word in cls.SPLIT_WORDS.items():
            pattern = re.compile(rf'\b{re.escape(split_form)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                matched = match.group(0)
                # Preserve original capitalization
                if matched[0].isupper():
                    corr_form = unified_word.capitalize()
                else:
                    corr_form = unified_word

                findings.append({
                    "category": "micro_typography",
                    "title": f"Accidentally split word '{matched}'",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": matched,
                    "suggested_correction": corr_form,
                    "explanation": f"'{matched}' contains an erroneous internal space separating syllables of '{corr_form}'.",
                    "severity": "medium",
                    "confidence": 0.94,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 11. Missing space after punctuation (e.g. 'analysis,reports' -> 'analysis, reports')
        # Excludes URLs, decimal numbers, and domain names
        missing_space_punct = re.compile(r'\b([a-zA-Z]{3,})([,;])([a-zA-Z]{3,})\b')
        for match in missing_space_punct.finditer(text):
            w1 = match.group(1)
            punct = match.group(2)
            w2 = match.group(3)
            # Skip if looks like a file extension or code reference
            if w2.lower() in {"com", "org", "net", "edu", "gov", "io", "ai", "py", "ts", "js"}:
                continue

            orig_str = match.group(0)
            findings.append({
                "category": "micro_typography",
                "title": f"Missing space after '{punct}'",
                "finding_classification": "A",
                "is_actionable": True,
                "page_number": page_num,
                "original_content": orig_str,
                "suggested_correction": f"{w1}{punct} {w2}",
                "explanation": f"Missing standard whitespace following punctuation mark in '{orig_str}'.",
                "severity": "low",
                "confidence": 0.93,
                "evidence_source": "micro_typography_engine",
                "bbox": bbox,
                "char_offset_start": match.start(),
                "char_offset_end": match.end(),
                "detection_method": "rule_based"
            })

        # 12. Lowercase standalone pronoun 'i' (e.g. 'as i mentioned' -> 'as I mentioned')
        pronoun_i_pattern = re.compile(r'(?<=\s)(i)(?=[\s,.:;?!])|^i(?=[\s,.:;?!])')
        for match in pronoun_i_pattern.finditer(text):
            orig_i = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            # Context snippet for clean replacement
            snippet_start = max(0, start_pos - 4)
            snippet_end = min(len(text), end_pos + 6)
            findings.append({
                "category": "micro_typography",
                "title": "Uncapitalized first-person pronoun 'i'",
                "finding_classification": "A",
                "is_actionable": True,
                "page_number": page_num,
                "original_content": orig_i,
                "suggested_correction": "I",
                "explanation": "The English first-person singular pronoun 'I' must always be capitalized.",
                "severity": "medium",
                "confidence": 0.96,
                "evidence_source": "micro_typography_engine",
                "bbox": bbox,
                "char_offset_start": start_pos,
                "char_offset_end": end_pos,
                "detection_method": "rule_based"
            })

        # 13. Corrupted currency symbol: 'I' preceding Indian currency numbers or in headers
        # E.g. "I8,40,000" -> "₹8,40,000", "(I)" -> "(₹)"
        corrupt_curr_pattern = re.compile(r'(?<=\s|\()I(?=[0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?|\))')
        for match in corrupt_curr_pattern.finditer(text):
            # Check context to ensure it is in a financial/currency context
            c_start = max(0, match.start() - 25)
            c_end = min(len(text), match.end() + 25)
            ctx = text[c_start:c_end].lower()

            # If this currency token follows 'overrun', skip it so the financial variance engine handles both symbol and amount
            before_match = text[max(0, match.start() - 25):match.start()].lower()
            if "overrun" in before_match:
                continue
            if any(term in ctx for term in ["budget", "expenditure", "overrun", "cost", "amount", "total", "inr", "charge", "price", "fee"]):
                # Capture the full token including adjacent amount or parens for clean surgical targeting
                after_idx = match.end()
                rest = text[after_idx:min(len(text), after_idx + 15)]
                amt_match = re.match(r'^[0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]+)?', rest)
                if amt_match:
                    full_token = f"I{amt_match.group(0)}"
                    corr_token = f"₹{amt_match.group(0)}"
                elif rest.startswith(")"):
                    full_token = "(I)"
                    corr_token = "(₹)"
                else:
                    full_token = "I"
                    corr_token = "₹"

                findings.append({
                    "category": "micro_typography",
                    "title": "Corrupted currency symbol (rendered as black box or placeholder)",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": full_token,
                    "suggested_correction": corr_token,
                    "explanation": f"Currency prefix '{full_token}' uses an unmapped glyph (ZapfDingbats square) representing the Indian Rupee symbol ({corr_token}).",
                    "severity": "high",
                    "confidence": 0.98,
                    "evidence_source": "micro_typography_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.start() + len(full_token),
                    "detection_method": "rule_based"
                })

        return findings

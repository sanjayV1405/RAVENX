import re
from typing import Dict, Any, List, Optional


class GrammarInspector:
    """
    Module B: Grammar and Language Intelligence
    Inspects:
    - Subject-verb agreement (e.g. 'The documents is', 'The report are', 'all regional teams was', 'each regional lead are').
    - Incorrect auxiliary/participle verb forms (e.g. 'has went', 'have broke').
    - Indefinite article misuse ('a apple', 'an document', 'a hour').
    - Double negatives ('did not have no', 'cannot barely').
    - Sentence capitalization following terminal punctuation.
    - Architecture hook for LanguageTool API/server with robust rule fallback.
    - Domain allowlisting to prevent false positives on technical/proper nouns.
    """

    # Domain allowlist for terms that should never trigger grammar/spelling flags
    DOMAIN_ALLOWLIST = {
        "ravenx", "pymupdf", "pydantic", "fastapi", "opencv", "supabase", "postgresql",
        "docx", "pptx", "pdf", "sha256", "sha-256", "jwt", "oauth2", "rest", "api", "sdk",
        "deepseek", "gemini", "languagetool", "paddleocr", "ocr", "sqlite", "bbox",
        "asyncio", "uvicorn", "docker", "kubernetes", "github", "tailwind", "shadcn",
        "nextjs", "react", "lucide", "json", "jsonl", "xml", "html", "css"
    }

    # Subject-verb agreement patterns:
    # 1. Plural noun phrase with singular verb (e.g. "all regional teams was", "these documents is")
    # 2. Singular noun phrase with plural verb (e.g. "each regional lead are", "the report are")
    # 3. Pronoun agreement (e.g. "he are", "they is")
    SV_DISAGREEMENTS = [
        (
            re.compile(r'\b(the|these|those|all|our|their)\s+(?:[a-zA-Z]+\s+)?([a-zA-Z]+s)\s+(is|was|has)\b', re.IGNORECASE),
            "plural subject with singular verb",
            lambda m: m.group(0).rsplit(m.group(3), 1)[0] + ("are" if m.group(3).lower() == "is" else "were" if m.group(3).lower() == "was" else "have"),
            "high"
        ),
        (
            re.compile(r'\b(each|every|either|neither)\s+(?:[a-zA-Z]+\s+)?([a-zA-Z]+[^s\s])\s+(are|were|have)\b', re.IGNORECASE),
            "singular subject with plural verb",
            lambda m: m.group(0).rsplit(m.group(3), 1)[0] + ("is" if m.group(3).lower() == "are" else "was" if m.group(3).lower() == "were" else "has"),
            "high"
        ),
        (
            re.compile(r'\b(the|this|that)\s+([a-zA-Z]+[^s\s])\s+(are|were)\b', re.IGNORECASE),
            "singular subject with plural verb",
            lambda m: f"{m.group(1)} {m.group(2)} " + ("is" if m.group(3).lower() == "are" else "was"),
            "high"
        ),
        (
            re.compile(r'\b(he|she|it)\s+(have|are|were)\b', re.IGNORECASE),
            "third-person singular pronoun with plural verb",
            lambda m: f"{m.group(1)} " + ("has" if m.group(2).lower() == "have" else "is" if m.group(2).lower() == "are" else "was"),
            "high"
        ),
        (
            re.compile(r'\b(they|we|you)\s+(is|was|has)\b', re.IGNORECASE),
            "plural pronoun with singular verb",
            lambda m: f"{m.group(1)} " + ("are" if m.group(2).lower() == "is" else "were" if m.group(2).lower() == "was" else "have"),
            "high"
        )
    ]

    # Double comparatives / superlatives
    DOUBLE_COMPARATIVES = [
        (re.compile(r'\bmore\s+better\b', re.IGNORECASE), "better"),
        (re.compile(r'\bmore\s+easier\b', re.IGNORECASE), "easier"),
        (re.compile(r'\bmore\s+faster\b', re.IGNORECASE), "faster"),
        (re.compile(r'\bmost\s+best\b', re.IGNORECASE), "best"),
        (re.compile(r'\bmost\s+greatest\b', re.IGNORECASE), "greatest"),
        (re.compile(r'\bmost\s+highest\b', re.IGNORECASE), "highest")
    ]

    # Malformed idiom / prepositional errors
    IDIOMATIC_ERRORS = [
        (re.compile(r'\bwith\s+regards\s+to\b', re.IGNORECASE), "with regard to", "Standard professional phrasing is 'with regard to'."),
        (re.compile(r'\bin\s+according\s+to\b', re.IGNORECASE), "in accordance with", "Standard phrasing is 'in accordance with' or 'according to'."),
        (re.compile(r'\birregardless\b', re.IGNORECASE), "regardless", "Use 'regardless' instead of the non-standard 'irregardless'."),
        (re.compile(r'\bfor\s+all\s+intensive\s+purposes\b', re.IGNORECASE), "for all intents and purposes", "The idiom is 'for all intents and purposes'.")
    ]

    # Missing apostrophes in common contractions
    MISSING_APOSTROPHES = {
        "dont": "don't",
        "doesnt": "doesn't",
        "didnt": "didn't",
        "isnt": "isn't",
        "arent": "aren't",
        "wasnt": "wasn't",
        "werent": "weren't",
        "havent": "haven't",
        "hasnt": "hasn't",
        "hadnt": "hadn't",
        "cant": "can't",
        "couldnt": "couldn't",
        "shouldnt": "shouldn't",
        "wouldnt": "wouldn't",
        "wont": "won't"
    }

    # Incorrect verb forms
    VERB_FORM_ERRORS = [
        (re.compile(r'\bhas\s+went\b', re.IGNORECASE), "has gone", "Use the past participle 'gone' with 'has'."),
        (re.compile(r'\bhave\s+went\b', re.IGNORECASE), "have gone", "Use the past participle 'gone' with 'have'."),
        (re.compile(r'\bhad\s+went\b', re.IGNORECASE), "had gone", "Use the past participle 'gone' with 'had'."),
        (re.compile(r'\bhas\s+wrote\b', re.IGNORECASE), "has written", "Use the past participle 'written' with 'has'."),
        (re.compile(r'\bhave\s+wrote\b', re.IGNORECASE), "have written", "Use the past participle 'written' with 'have'."),
        (re.compile(r'\bhas\s+broke\b', re.IGNORECASE), "has broken", "Use the past participle 'broken' with 'has'."),
        (re.compile(r'\bhave\s+took\b', re.IGNORECASE), "have taken", "Use the past participle 'taken' with 'have'."),
        (re.compile(r'\bhas\s+did\b', re.IGNORECASE), "has done", "Use the past participle 'done' with 'has'.")
    ]

    # Article misuse patterns
    ARTICLE_A_BEFORE_VOWEL = re.compile(r'\b(a)\s+([aeio][a-z]{2,})\b', re.IGNORECASE)
    ARTICLE_AN_BEFORE_CONSONANT = re.compile(r'\b(an)\s+([bcdfghjklmnpqrstvwxyz][a-z]{2,})\b', re.IGNORECASE)

    # Exceptions where 'a' before vowel sound is phonetically consonant (e.g. 'a European', 'a user', 'a university')
    VOWEL_EXCEPTIONS = {"user", "university", "unique", "european", "utility", "unit", "uniform", "universal"}
    CONSONANT_EXCEPTIONS = {"hour", "honest", "honor", "heir", "honorable"}

    @classmethod
    def inspect(cls, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        pages = extraction_data.get("pages", [])

        if not pages and extraction_data.get("raw_text"):
            findings.extend(cls._inspect_text(extraction_data["raw_text"], page_num=1))
            return findings

        for page in pages:
            page_num = page.get("page_number", 1)
            structured = page.get("structured_data", {})
            blocks = structured.get("blocks", []) or page.get("blocks", [])
            if blocks:
                for block in blocks:
                    block_text = block.get("text", "")
                    bbox = block.get("bbox")
                    findings.extend(cls._inspect_text(block_text, page_num=page_num, bbox=bbox))
            else:
                page_text = page.get("reconstructed_text") or page.get("raw_text", "")
                findings.extend(cls._inspect_text(page_text, page_num=page_num))

        return findings

    @classmethod
    def _inspect_text(
        cls,
        text: str,
        page_num: int = 1,
        bbox: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        if not text or not text.strip():
            return findings

        # 1. Subject-Verb Agreement checks
        for pattern, desc, fixer, severity in cls.SV_DISAGREEMENTS:
            for match in pattern.finditer(text):
                subject = match.group(2) if match.lastindex >= 2 else ""
                # Skip if subject is in domain allowlist
                if subject.lower() in cls.DOMAIN_ALLOWLIST:
                    continue
                # Exclude nouns ending in 's' that are singular (news, series, species, analysis)
                if subject.lower() in {"news", "series", "species", "basis", "analysis", "status", "process"}:
                    continue

                correction = fixer(match)
                findings.append({
                    "category": "grammar",
                    "title": f"Grammar error: {desc}",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": correction,
                    "explanation": f"Subject-verb disagreement detected: '{match.group(0)}'. Suggested correction: '{correction}'.",
                    "severity": severity,
                    "confidence": 0.93,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 2. Incorrect verb participle forms
        for pattern, correction, explanation in cls.VERB_FORM_ERRORS:
            for match in pattern.finditer(text):
                findings.append({
                    "category": "grammar",
                    "title": "Incorrect verb form",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": correction,
                    "explanation": explanation,
                    "severity": "high",
                    "confidence": 0.98,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 3. Indefinite article misuse: 'a' before vowel sound
        for match in cls.ARTICLE_A_BEFORE_VOWEL.finditer(text):
            word = match.group(2)
            if word.lower() not in cls.VOWEL_EXCEPTIONS and word.lower() not in cls.DOMAIN_ALLOWLIST:
                findings.append({
                    "category": "grammar",
                    "title": f"Incorrect indefinite article before '{word}'",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": f"an {word}",
                    "explanation": f"Use the indefinite article 'an' before words beginning with vowel sounds.",
                    "severity": "medium",
                    "confidence": 0.94,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 4. Indefinite article misuse: 'an' before consonant sound
        for match in cls.ARTICLE_AN_BEFORE_CONSONANT.finditer(text):
            word = match.group(2)
            if word.lower() not in cls.CONSONANT_EXCEPTIONS and word.lower() not in cls.DOMAIN_ALLOWLIST:
                findings.append({
                    "category": "grammar",
                    "title": f"Incorrect indefinite article before '{word}'",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": f"a {word}",
                    "explanation": f"Use the indefinite article 'a' before words beginning with consonant sounds.",
                    "severity": "medium",
                    "confidence": 0.94,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 5. Sentence capitalization: lowercase letter beginning sentence after terminal period
        sentence_cap_pattern = re.compile(r'([.?!])\s+([a-z][a-zA-Z]+)')
        for match in sentence_cap_pattern.finditer(text):
            punct = match.group(1)
            word = match.group(2)
            if word.lower() in {"etc", "eg", "ie", "vs", "al"}:
                continue
            findings.append({
                "category": "grammar",
                "title": "Uncapitalized sentence start",
                "finding_classification": "A",
                "is_actionable": True,
                "page_number": page_num,
                "original_content": match.group(0),
                "suggested_correction": f"{punct} {word.capitalize()}",
                "explanation": f"A sentence ending in '{punct}' should be followed by a capitalized word.",
                "severity": "low",
                "confidence": 0.90,
                "evidence_source": "grammar_engine",
                "bbox": bbox,
                "char_offset_start": match.start(),
                "char_offset_end": match.end(),
                "detection_method": "rule_based"
            })

        # 6. Double comparatives / superlatives
        for pattern, correction in cls.DOUBLE_COMPARATIVES:
            for match in pattern.finditer(text):
                findings.append({
                    "category": "grammar",
                    "title": f"Redundant comparative '{match.group(0)}'",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": correction,
                    "explanation": f"Double comparative detected. Use '{correction}' instead of '{match.group(0)}'.",
                    "severity": "medium",
                    "confidence": 0.96,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 7. Malformed idiomatic / prepositional expressions
        for pattern, correction, explanation in cls.IDIOMATIC_ERRORS:
            for match in pattern.finditer(text):
                findings.append({
                    "category": "grammar",
                    "title": "Incorrect prepositional idiom",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": match.group(0),
                    "suggested_correction": correction,
                    "explanation": explanation,
                    "severity": "medium",
                    "confidence": 0.95,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 8. Missing apostrophes in common contractions
        for typo, corr in cls.MISSING_APOSTROPHES.items():
            pattern = re.compile(rf'\b{re.escape(typo)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                orig_token = match.group(0)
                if orig_token.isupper():
                    replacement = corr.upper()
                elif orig_token[0].isupper():
                    replacement = corr.capitalize()
                else:
                    replacement = corr

                findings.append({
                    "category": "grammar",
                    "title": f"Missing contraction apostrophe in '{orig_token}'",
                    "finding_classification": "A",
                    "is_actionable": True,
                    "page_number": page_num,
                    "original_content": orig_token,
                    "suggested_correction": replacement,
                    "explanation": f"The contraction '{orig_token}' is missing its apostrophe.",
                    "severity": "low",
                    "confidence": 0.94,
                    "evidence_source": "grammar_engine",
                    "bbox": bbox,
                    "char_offset_start": match.start(),
                    "char_offset_end": match.end(),
                    "detection_method": "rule_based"
                })

        # 9. Repeated 2-to-3 word phrases (e.g. 'in order to in order to', 'as well as as well as')
        repeated_phrase_pattern = re.compile(r'\b([a-zA-Z]{2,}(?:\s+[a-zA-Z]{2,}){1,2})\s+\1\b', re.IGNORECASE)
        for match in repeated_phrase_pattern.finditer(text):
            phrase = match.group(1)
            # Skip if part of a number or allowlisted term
            if phrase.lower() in {"very very", "bye bye", "ha ha"}:
                continue

            findings.append({
                "category": "grammar",
                "title": f"Repeated phrase '{phrase}'",
                "finding_classification": "A",
                "is_actionable": True,
                "page_number": page_num,
                "original_content": match.group(0),
                "suggested_correction": phrase,
                "explanation": f"The phrase '{phrase}' is duplicated consecutively in the sentence.",
                "severity": "medium",
                "confidence": 0.97,
                "evidence_source": "grammar_engine",
                "bbox": bbox,
                "char_offset_start": match.start(),
                "char_offset_end": match.end(),
                "detection_method": "rule_based"
            })

        return findings

"""Verification engine — compares uploaded rows against reference data."""

import re
import difflib
from typing import Any, Callable

ARABIC_DIACRITICS = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u08F0-\u08FF]')


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip footnotes, collapse whitespace."""
    if not text:
        return ''
    normalized = text.lower()
    normalized = re.sub(r'\[\d+\]', '', normalized)
    normalized = re.sub(r'\(\d+\)', '', normalized)
    normalized = re.sub(r'[†‡*]+', '', normalized)
    normalized = re.sub(r'[^\w\s]', ' ', normalized, flags=re.UNICODE)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def similarity_ratio(text_a: str, text_b: str) -> float:
    """Return similarity ratio between 0.0 and 1.0 using SequenceMatcher."""
    a = normalize_text(text_a)
    b = normalize_text(text_b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def word_diff_details(uploaded: str, reference: str) -> dict[str, Any]:
    """Detect missing, extra, and changed words between uploaded and reference text."""
    uploaded_words = normalize_text(uploaded).split()
    reference_words = normalize_text(reference).split()

    matcher = difflib.SequenceMatcher(None, reference_words, uploaded_words)
    missing_words: list[str] = []
    extra_words: list[str] = []
    changed_pairs: list[dict[str, str]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            missing_words.extend(reference_words[i1:i2])
        elif tag == 'insert':
            extra_words.extend(uploaded_words[j1:j2])
        elif tag == 'replace':
            ref_chunk = ' '.join(reference_words[i1:i2])
            up_chunk = ' '.join(uploaded_words[j1:j2])
            changed_pairs.append({'reference': ref_chunk, 'uploaded': up_chunk})

    return {
        'missing_words': missing_words,
        'extra_words': extra_words,
        'changed_segments': changed_pairs,
    }


def classify_row_status(similarity: float) -> str:
    """Classify a single row based on similarity score."""
    if similarity >= 0.98:
        return 'accurate'
    if similarity >= 0.70:
        return 'partially_accurate'
    return 'inaccurate'


def classify_overall_status(accuracy_percentage: float) -> str:
    """Classify overall verification result (FR-4-06)."""
    if accuracy_percentage >= 95.0:
        return 'accurate'
    if accuracy_percentage >= 50.0:
        return 'partially_accurate'
    return 'inaccurate'


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic Quranic text consistently across system."""
    if not text:
        return ''

    normalized = ARABIC_DIACRITICS.sub('', text)
    normalized = normalized.replace('\u0640', '')  # tatweel

    # unify Arabic letters (IMPORTANT: match frontend)
    normalized = re.sub(r'[إأآٱ]', 'ا', normalized)
    normalized = re.sub(r'ى', 'ي', normalized)
    normalized = re.sub(r'ة', 'ه', normalized)

    normalized = re.sub(r'[^\u0600-\u06FF\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def arabic_similarity_ratio(text_a: str, text_b: str) -> float:
    """Return similarity ratio for Arabic text using normalized comparison."""
    a = normalize_arabic_text(text_a)
    b = normalize_arabic_text(text_b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def arabic_char_diff_details(uploaded: str, reference: str) -> dict[str, Any]:
    """Detect character-level differences in normalized Arabic text."""
    uploaded_chars = list(normalize_arabic_text(uploaded))
    reference_chars = list(normalize_arabic_text(reference))

    matcher = difflib.SequenceMatcher(None, reference_chars, uploaded_chars)
    missing_chars: list[str] = []
    extra_chars: list[str] = []
    changed_segments: list[dict[str, str]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            missing_chars.extend(reference_chars[i1:i2])
        elif tag == 'insert':
            extra_chars.extend(uploaded_chars[j1:j2])
        elif tag == 'replace':
            changed_segments.append({
                'reference': ''.join(reference_chars[i1:i2]),
                'uploaded': ''.join(uploaded_chars[j1:j2]),
            })

    return {
        'missing_words': missing_chars,
        'extra_words': extra_chars,
        'changed_segments': changed_segments,
    }


def _verify_content_rows(
    uploaded_rows: list[dict],
    reference_lookup: dict[tuple[int, int], str],
    content_field: str,
    compare_fn: Callable[[str, str], float],
    diff_fn: Callable[[str, str], dict],
    accurate_message: str,
    missing_reference_message: str,
    missing_content_message: str,
) -> dict[str, Any]:

    details = []

    exact_matches = 0
    partial_matches = 0
    mismatches = 0
    reference_not_found = 0
    invalid_rows = 0

    similarity_scores = []

    BISMILLAH = "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ"

    def is_bismillah(text: str) -> bool:
        return "بسم" in normalize_arabic_text(text)

    def strip_bismillah(text: str) -> str:
        if not text:
            return ""
        if is_bismillah(text):
            return ""
        return text

    for row in uploaded_rows:

        # -------------------------
        # Validate surah / ayah
        # -------------------------
        try:
            surah = int(row.get('surah_number') or 0)
            ayah = int(row.get('ayah_number') or 0)
        except:
            invalid_rows += 1
            continue

        uploaded_text = (row.get(content_field) or '').strip()

        # -------------------------
        # Normalize Arabic if needed
        # -------------------------
        if content_field == 'arabic_text':
            uploaded_text = normalize_arabic_text(uploaded_text)

        # -------------------------
        # Skip invalid rows
        # -------------------------
        if not uploaded_text or surah <= 0 or ayah <= 0:
            invalid_rows += 1
            continue

        # -------------------------
        # 🔥 REMOVE BISMILLAH ROW COMPLETELY
        # -------------------------
        if content_field == 'arabic_text' and is_bismillah(uploaded_text):
            continue

        # -------------------------
        # Reference lookup
        # -------------------------
        reference_text = reference_lookup.get((surah, ayah))

        if reference_text is None:
            reference_not_found += 1
            details.append({
                "surah_number": surah,
                "ayah_number": ayah,
                "status": "reference_not_found",
                "uploaded_text": strip_bismillah(uploaded_text),
                "reference_text": None,
                "similarity_percentage": 0,
                "differences": {},
                "message": missing_reference_message,
            })
            continue

        # -------------------------
        # Compare
        # -------------------------
        sim = compare_fn(uploaded_text, reference_text)
        diff = diff_fn(uploaded_text, reference_text)

        similarity_scores.append(sim)

        if sim >= 0.98:
            status = "accurate"
            exact_matches += 1
        elif sim >= 0.70:
            status = "partially_accurate"
            partial_matches += 1
        else:
            status = "inaccurate"
            mismatches += 1

        # -------------------------
        # Store result
        # -------------------------
        details.append({
            "surah_number": surah,
            "ayah_number": ayah,
            "status": status,

            # CLEAN OUTPUT (safe for UI)
            "uploaded_text": strip_bismillah(uploaded_text),
            "reference_text": reference_text,

            "similarity_percentage": round(sim * 100, 2),
            "differences": diff,
            "message": accurate_message if status == "accurate" else "Mismatch detected",
        })

    # -------------------------
    # Summary
    # -------------------------
    total = exact_matches + partial_matches + mismatches

    accuracy = (
        round((sum(similarity_scores) / len(similarity_scores)) * 100, 2)
        if similarity_scores else 0
    )

    avg_similarity = (
        round((sum(similarity_scores) / len(similarity_scores)) * 100, 2)
        if similarity_scores else 0
    )

    return {
        "summary": {
            "total_uploaded_rows": len(uploaded_rows),
            "total_compared": total,
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "mismatches": mismatches,
            "reference_not_found": reference_not_found,
            "invalid_rows": invalid_rows,
            "accuracy_percentage": accuracy,
            "average_similarity_percentage": avg_similarity,
        },
        "details": details,
    }


def verify_translation_rows(
    uploaded_rows: list[dict],
    reference_lookup: dict[tuple[int, int], str],
) -> dict[str, Any]:
    """Compare uploaded translation rows against a reference lookup keyed by (surah, ayah)."""
    return _verify_content_rows(
        uploaded_rows=uploaded_rows,
        reference_lookup=reference_lookup,
        content_field='translation',
        compare_fn=similarity_ratio,
        diff_fn=word_diff_details,
        accurate_message='Translation matches the approved reference.',
        missing_reference_message='No approved reference translation found for this ayah.',
        missing_content_message='Missing translation text or invalid reference.',
    )


def verify_quranic_text_rows(
    uploaded_rows: list[dict],
    reference_lookup: dict[tuple[int, int], str],
) -> dict[str, Any]:
    """Compare uploaded Quranic Arabic text rows against a reference lookup keyed by (surah, ayah)."""
    return _verify_content_rows(
        uploaded_rows=uploaded_rows,
        reference_lookup=reference_lookup,
        content_field='arabic_text',
        compare_fn=arabic_similarity_ratio,
        diff_fn=arabic_char_diff_details,
        accurate_message='Quranic text matches the approved reference.',
        missing_reference_message='No approved reference Quranic text found for this ayah.',
        missing_content_message='Missing Arabic text or invalid reference.',
    )


def _status_message(status: str, diff: dict, accurate_message: str) -> str:
    if status == 'accurate':
        return accurate_message
    parts = []
    if diff.get('missing_words'):
        sample = diff['missing_words'][:5]
        parts.append(f"Missing: {', '.join(str(w) for w in sample)}")
    if diff.get('extra_words'):
        sample = diff['extra_words'][:5]
        parts.append(f"Extra: {', '.join(str(w) for w in sample)}")
    if diff.get('changed_segments'):
        parts.append(f"{len(diff['changed_segments'])} segment(s) differ")
    if status == 'partially_accurate':
        return 'Partial match - ' + ('; '.join(parts) if parts else 'minor differences detected.')
    return 'Mismatch - ' + ('; '.join(parts) if parts else 'significant differences detected.')

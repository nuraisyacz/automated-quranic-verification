"""utils/quran_compare.py - diacritic-aware Quranic text verification (stdlib only).

Two layers:
  * skeleton()      letters only; used to recognise basmalah.
  * compare_ayah()  full comparison INCLUDING diacritics, differences listed by type.

Reference and upload both pass through canonical(), so identical text stored with
different Unicode encodings is not reported as an error.

NOTE: this file is plain ASCII on purpose (all Arabic characters are written as \\uXXXX
escapes) so it survives copy/paste and editors that hide invisible characters.
"""
import hashlib
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

# Diacritics + Quranic annotation signs. Excludes U+06DD (ayah end), U+06DE, U+06E9.
_DIAC = "\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED"
_DIAC_RE = re.compile("[" + _DIAC + "]")
_WAQF_RE = re.compile("[\u06D6-\u06DC]")  # pause signs (optionally ignored)
# ayah-end / hizb / sajdah markers, ornate brackets, and Western / Arabic-Indic digits
_NONTEXT_RE = re.compile("[\u06DD\u06DE\u06E9\uFD3E\uFD3F0-9\u0660-\u0669\u06F0-\u06F9]")
_INVISIBLE_RE = re.compile("[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]")

# Variants treated as the SAME character. Deliberately minimal: the uploaded text must match the
# reference exactly, so alef wasla vs plain alef and the two sukun code points are NOT folded;
# they are reported as differences. Only typing/extraction artifacts are folded:
#   U+06A9 keheh -> U+0643 kaf        U+0640 tatweel -> removed
_VARIANTS = str.maketrans({"\u06A9": "\u0643", "\u0640": None})

# Used ONLY for the letters-only skeleton.
_FOLD = str.maketrans({
    "\u0623": "\u0627", "\u0625": "\u0627", "\u0622": "\u0627", "\u0671": "\u0627",
    "\u0649": "\u064A",
    "\u0629": "\u0647",
})

# bismillah ar-rahman ar-rahim, letters only
BASMALAH_SKELETON = "\u0628\u0633\u0645 \u0627\u0644\u0644\u0647 \u0627\u0644\u0631\u062D\u0645\u0646 \u0627\u0644\u0631\u062D\u064A\u0645"


def canonical(text, ignore_waqf=False):
    """Unicode-clean text but KEEP diacritics."""
    text = unicodedata.normalize("NFC", text or "")
    text = _INVISIBLE_RE.sub("", text).replace("\u00A0", " ").translate(_VARIANTS)
    text = _NONTEXT_RE.sub("", text)
    if ignore_waqf:
        text = _WAQF_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def skeleton(text):
    """Letters only. Never used for the final verdict."""
    return _DIAC_RE.sub("", canonical(text)).translate(_FOLD)


def is_basmalah(text):
    """True only if the WHOLE text is the basmalah (not a substring match)."""
    return skeleton(text) == BASMALAH_SKELETON


def strip_leading_basmalah(text):
    """Drop a basmalah (first four words) at the start of text. Works on the original string,
    so the remaining words keep their original encoding."""
    words = (text or "").split()
    if len(words) > 4 and skeleton(" ".join(words[:4])) == BASMALAH_SKELETON:
        return " ".join(words[4:])
    return text or ""


def _prep(text, surah, ayah):
    """The basmalah is part of ayah 1 only in Al-Fatihah. Elsewhere it is not counted as
    part of the ayah, whether the upload or the reference includes it."""
    if ayah == 1 and surah != 1:
        return strip_leading_basmalah(text)
    return text


def _clusters(text):
    """Letter + attached diacritics, so diffs are meaningful."""
    out = []
    for ch in text:
        if out and _DIAC_RE.match(ch):
            out[-1] += ch
        else:
            out.append(ch)
    return out


def _base(cluster):
    """Base letter of a cluster. Alef wasla counts as the same base letter as alef, so a
    wasla/alef difference is reported as a mark-level (partial) difference, not a wrong letter."""
    return _DIAC_RE.sub("", cluster).replace("\u0671", "\u0627")


def compare_ayah(uploaded, reference, ignore_waqf=False):
    u, r = canonical(uploaded, ignore_waqf), canonical(reference, ignore_waqf)
    if u == r:
        return {"status": "accurate", "similarity_percentage": 100.0, "differences": [], "message": ""}

    uc, rc = _clusters(u), _clusters(r)
    sm = SequenceMatcher(None, uc, rc, autojunk=False)
    ratio = sm.ratio()

    diffs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        up, rf = "".join(uc[i1:i2]), "".join(rc[j1:j2])
        if tag == "delete":
            kind = "extra"      # in upload, not in reference
        elif tag == "insert":
            kind = "missing"    # in reference, not in upload
        elif i2 - i1 == j2 - j1 and all(_base(a) == _base(b) for a, b in zip(uc[i1:i2], rc[j1:j2])):
            kind = "diacritic"  # same letters, different marks
        else:
            kind = "letter"
        diffs.append({"type": kind, "position": i1, "uploaded": up, "reference": rf,
                      "uploaded_codepoints": " ".join("U+%04X" % ord(c) for c in up),
                      "reference_codepoints": " ".join("U+%04X" % ord(c) for c in rf)})

    # Only diacritic differences -> partial. Any wrong, missing or extra letter (including a
    # changed hamza or alef maksura) -> inaccurate.
    if diffs and all(d["type"] == "diacritic" for d in diffs):
        status, msg = "partially_accurate", "Only diacritics differ from the reference."
    else:
        status, msg = "inaccurate", "Letters differ from the reference."
    return {"status": status, "similarity_percentage": round(ratio * 100, 2),
            "differences": diffs, "message": msg}


def content_hash(rows, field="arabic_text"):
    """SHA-256 of the uploaded content in a canonical, order-independent form."""
    lines = []
    for row in rows:
        try:
            key = (int(row["surah_number"]), int(row["ayah_number"]))
        except (KeyError, TypeError, ValueError):
            key = (0, 0)
        lines.append("%d:%d:%s" % (key[0], key[1], canonical(row.get(field, ""))))
    return hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def describe_scope(keys_by_surah, expected_by_surah):
    """e.g. 'Surah 112 (4/4 ayahs); Surah 113 (5/5 ayahs)'"""
    parts = []
    for s in sorted(keys_by_surah):
        parts.append("Surah %d (%d/%s ayahs)" % (s, len(keys_by_surah[s]), expected_by_surah.get(s, "?")))
    return "; ".join(parts)


class ReferenceIndex:
    """Build once from the reference table and reuse for every request."""

    def __init__(self, rows):
        # rows: iterable of (surah_number, ayah_number, arabic_text)
        self.text = {}
        self.ayahs_by_surah = defaultdict(set)
        for s, a, t in rows:
            key = (int(s), int(a))
            self.text[key] = t
            self.ayahs_by_surah[key[0]].add(key[1])
        lines = sorted("%d:%d:%s" % (s, a, canonical(t)) for (s, a), t in self.text.items())
        # Pins exactly which reference edition a certificate was issued against.
        self.fingerprint = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

    def __len__(self):
        return len(self.text)

    def verify(self, rows, ignore_waqf=False):
        details = []
        counts = {"accurate": 0, "partially_accurate": 0, "inaccurate": 0,
                  "reference_not_found": 0, "invalid_row": 0}
        seen = set()
        ignored = 0

        for row in rows:
            up = row.get("arabic_text", "") or ""
            try:
                key = (int(row["surah_number"]), int(row["ayah_number"]))
            except (KeyError, TypeError, ValueError):
                counts["invalid_row"] += 1
                details.append({"surah_number": row.get("surah_number"), "ayah_number": row.get("ayah_number"),
                                "status": "invalid_row", "uploaded_text": up, "reference_text": "",
                                "similarity_percentage": 0, "differences": [],
                                "message": "Surah or ayah number is missing or not a number."})
                continue

            # A standalone basmalah line (not Al-Fatihah) is a surah header, not an ayah.
            if key[0] != 1 and is_basmalah(up):
                ignored += 1
                continue

            if key in seen:
                counts["invalid_row"] += 1
                details.append({"surah_number": key[0], "ayah_number": key[1], "status": "invalid_row",
                                "uploaded_text": up, "reference_text": self.text.get(key, ""),
                                "similarity_percentage": 0, "differences": [],
                                "message": "Duplicate row for this ayah."})
                continue
            seen.add(key)

            ref = self.text.get(key)
            if ref is None:
                shown_ref = ""
                res = {"status": "reference_not_found", "similarity_percentage": 0, "differences": [],
                       "message": "No reference ayah found."}
            else:
                shown_ref = _prep(ref, *key)  # the text that was actually compared
                res = compare_ayah(_prep(up, *key), shown_ref, ignore_waqf=ignore_waqf)
            counts[res["status"]] += 1
            details.append({"surah_number": key[0], "ayah_number": key[1], "uploaded_text": up,
                            "reference_text": shown_ref, **res})

        # Coverage: ayahs of each uploaded surah that the document does not contain.
        uploaded_by_surah = defaultdict(set)
        for s, a in seen:
            if s in self.ayahs_by_surah:
                uploaded_by_surah[s].add(a)
        missing = []
        for s in sorted(uploaded_by_surah):
            for a in sorted(self.ayahs_by_surah[s] - uploaded_by_surah[s]):
                missing.append({"surah_number": s, "ayah_number": a})

        considered = len(details)
        exact = counts["accurate"]
        if considered and exact == considered and not missing:
            status = "accurate"
        elif exact + counts["partially_accurate"] == 0:
            status = "inaccurate"
        else:
            status = "partially_accurate"
        denominator = considered + len(missing)
        summary = {
            "total_uploaded_rows": considered,
            "exact_matches": exact,
            "partial_matches": counts["partially_accurate"],
            "mismatches": counts["inaccurate"],
            "reference_not_found": counts["reference_not_found"],
            "invalid_rows": counts["invalid_row"],
            "missing_ayahs": len(missing),
            "ignored_rows": ignored,
            "accuracy_percentage": round(exact / denominator * 100, 2) if denominator else 0,
            "verification_status": status,
        }
        coverage = {
            "scope": describe_scope(uploaded_by_surah, {s: len(v) for s, v in self.ayahs_by_surah.items()}),
            "surahs": sorted(uploaded_by_surah),
            "missing_count": len(missing),
            "missing": missing[:500],
        }
        return {"summary": summary, "details": details, "coverage": coverage}
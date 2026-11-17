"""utils/report_generator.py - verification report PDF, built as HTML and printed by Chromium.

Why Chromium: Arabic needs letter shaping, right-to-left layout and correct placement of the
diacritics. ReportLab cannot do this (it prints ???? when the font has no Arabic, and misplaces
the marks even when it does). A browser engine does all of it correctly.

Setup (once):  pip install playwright   then   playwright install chromium
Font: assets/fonts/amiri-arabic-400-normal.woff2 (Amiri, SIL Open Font License).
"""
import base64
import html
import io
import os
from datetime import datetime

_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts",
                          "amiri-arabic-400-normal.woff2")
_font_css_cache = None

STATUS_LABELS = {
    "accurate": "Accurate",
    "partially_accurate": "Partially Accurate",
    "inaccurate": "Inaccurate",
    "reference_not_found": "No Reference",
    "invalid_row": "Invalid Row",
}
DIFF_LABELS = {
    "letter": "Different letter",
    "diacritic": "Different diacritic",
    "missing": "Missing from upload",
    "extra": "Extra in upload",
}
MAX_DIFFS_PER_AYAH = 10
MAX_MISSING_LISTED = 200


def _font_css():
    global _font_css_cache
    if _font_css_cache is None:
        with open(_FONT_PATH, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        _font_css_cache = (
            "@font-face{font-family:'AmiriQ';font-weight:400;"
            "src:url(data:font/woff2;base64," + b64 + ") format('woff2');}"
        )
    return _font_css_cache


def _e(value):
    return html.escape("" if value is None else str(value))


def _fmt_date(iso):
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.strftime("%d %B %Y, %H:%M UTC")
    except (TypeError, ValueError):
        return _e(iso) or "N/A"


_CSS = """
*{box-sizing:border-box}
body{font-family:Helvetica,Arial,sans-serif;color:#1f2937;font-size:11px;margin:0}
h1{font-size:20px;margin:0 0 2px}
h2{font-size:13px;margin:18px 0 6px;border-bottom:1px solid #d1d5db;padding-bottom:3px}
.sub{color:#6b7280;margin-bottom:10px}
table{border-collapse:collapse;width:100%}
td,th{padding:3px 6px;text-align:left;vertical-align:top}
.kv td:first-child{color:#6b7280;width:130px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-weight:bold;font-size:10px;color:#fff}
.accurate{background:#15803d}.partially_accurate{background:#b45309}.inaccurate{background:#b91c1c}
.reference_not_found,.invalid_row{background:#6b7280}
.stats td{border:1px solid #e5e7eb;text-align:center;padding:6px}
.stats .n{font-size:16px;font-weight:bold;display:block}
.stats .l{color:#6b7280;font-size:9px}
.card{border:1px solid #e5e7eb;border-radius:6px;padding:8px 10px;margin:8px 0;page-break-inside:avoid}
.card .head{font-weight:bold;margin-bottom:3px}
.msg{color:#6b7280;font-style:italic;margin-bottom:4px}
.lbl{color:#6b7280;font-size:9px;margin-top:4px}
.ar{font-family:'AmiriQ','Amiri','Noto Naskh Arabic',serif;direction:rtl;text-align:right;
    font-size:20px;line-height:2.1;unicode-bidi:isolate}
.txt{white-space:pre-wrap}
.diffs{margin-top:6px;font-size:10px}
.diffs th{color:#6b7280;border-bottom:1px solid #e5e7eb;font-weight:normal}
.diffs .ar{font-size:18px;line-height:1.9}
.cp{font-family:Courier,monospace;font-size:8px;color:#9ca3af;direction:ltr;text-align:left}
.note{color:#6b7280;font-size:10px;margin-top:4px}
"""


def build_report_html(report):
    doc = report.get("document", {}) or {}
    summary = report.get("summary", {}) or {}
    coverage = report.get("coverage") or {}
    cert = report.get("certificate") or {}
    is_quran = doc.get("verification_type") == "quranic_text"
    title = "Quranic Text Verification Report" if is_quran else "Translation Verification Report"
    status = summary.get("verification_status", "unknown")
    text_cls = "ar" if is_quran else "txt"

    parts = ["<!doctype html><html><head><meta charset='utf-8'><style>",
             _font_css(), _CSS, "</style></head><body>"]
    parts.append("<h1>%s</h1><div class='sub'>Automated Verification System for Digital Quranic Text</div>" % _e(title))

    rows = [("File", doc.get("filename")), ("Generated", _fmt_date(report.get("generated_at"))),
            ("Total rows", doc.get("total_rows")), ("Reference source", doc.get("reference_source")),
            ("Reference ayahs", doc.get("reference_ayah_count"))]
    if coverage.get("scope"):
        rows.append(("Scope checked", coverage["scope"]))
    if cert.get("reference_no"):
        rows.append(("Certificate reference", cert["reference_no"]))
    parts.append("<h2>Document details</h2><table class='kv'>")
    for k, v in rows:
        parts.append("<tr><td>%s</td><td>%s</td></tr>" % (_e(k), v if k == "Generated" else _e(v)))
    parts.append("</table>")

    parts.append("<h2>Verification summary</h2>")
    parts.append("<p>Status: <span class='badge %s'>%s</span> &nbsp; Accuracy: <b>%s%%</b></p>" % (
        _e(status), _e(STATUS_LABELS.get(status, status)), _e(summary.get("accuracy_percentage", 0))))
    stats = [("Exact matches", "exact_matches"), ("Partial matches", "partial_matches"),
             ("Mismatches", "mismatches"), ("No reference", "reference_not_found")]
    if is_quran:
        stats += [("Missing ayahs", "missing_ayahs"), ("Invalid rows", "invalid_rows")]
    parts.append("<table class='stats'><tr>")
    for label, key in stats:
        parts.append("<td><span class='n'>%s</span><span class='l'>%s</span></td>" % (_e(summary.get(key, 0)), _e(label)))
    parts.append("</tr></table>")

    missing = coverage.get("missing") or []
    if coverage.get("missing_count"):
        listed = ", ".join("%s:%s" % (m["surah_number"], m["ayah_number"]) for m in missing[:MAX_MISSING_LISTED])
        more = coverage["missing_count"] - min(len(missing), MAX_MISSING_LISTED)
        parts.append("<h2>Ayahs missing from the document (%s)</h2><p>%s%s</p>" % (
            _e(coverage["missing_count"]), _e(listed), (" and %d more" % more) if more > 0 else ""))

    problems = [d for d in (report.get("details") or []) if d.get("status") != "accurate"]
    parts.append("<h2>Mismatch details (%d)</h2>" % len(problems))
    if not problems:
        parts.append("<p>All compared rows matched the reference.</p>")
    for d in problems:
        st = d.get("status", "")
        parts.append("<div class='card'><div class='head'>Surah %s:%s &nbsp;<span class='badge %s'>%s</span> &nbsp;%s%% similar</div>" % (
            _e(d.get("surah_number")), _e(d.get("ayah_number")), _e(st),
            _e(STATUS_LABELS.get(st, st)), _e(d.get("similarity_percentage", 0))))
        if d.get("message"):
            parts.append("<div class='msg'>%s</div>" % _e(d["message"]))
        parts.append("<div class='lbl'>UPLOADED</div><div class='%s'>%s</div>" % (text_cls, _e(d.get("uploaded_text"))))
        if d.get("reference_text"):
            parts.append("<div class='lbl'>REFERENCE</div><div class='%s'>%s</div>" % (text_cls, _e(d["reference_text"])))
        diffs = d.get("differences") or []
        if diffs:
            parts.append("<table class='diffs'><tr><th>Difference</th><th>Uploaded</th><th>Reference</th></tr>")
            for df in diffs[:MAX_DIFFS_PER_AYAH]:
                parts.append(
                    "<tr><td>%s</td><td><div class='%s'>%s</div><div class='cp'>%s</div></td>"
                    "<td><div class='%s'>%s</div><div class='cp'>%s</div></td></tr>" % (
                        _e(DIFF_LABELS.get(df.get("type"), df.get("type"))),
                        text_cls, _e(df.get("uploaded")) or "&mdash;", _e(df.get("uploaded_codepoints")),
                        text_cls, _e(df.get("reference")) or "&mdash;", _e(df.get("reference_codepoints"))))
            parts.append("</table>")
            if len(diffs) > MAX_DIFFS_PER_AYAH:
                parts.append("<div class='note'>%d more differences not shown.</div>" % (len(diffs) - MAX_DIFFS_PER_AYAH))
        parts.append("</div>")

    parts.append("</body></html>")
    return "".join(parts)


def generate_verification_pdf(report):
    """Return a BytesIO with the report PDF. Raises RuntimeError with a clear message if the
    PDF engine is not installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PDF engine missing. Run: pip install playwright && playwright install chromium") from exc

    page_html = build_report_html(report)
    footer = ("<div style='font-size:8px;width:100%;text-align:center;color:#6b7280'>"
              "Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>")
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:
            if "Executable doesn't exist" in str(exc):
                raise RuntimeError("Chromium is not installed. Run: playwright install chromium") from exc
            raise
        try:
            page = browser.new_page()
            page.set_content(page_html, wait_until="load")
            page.evaluate("document.fonts.ready")
            pdf_bytes = page.pdf(format="A4", print_background=True,
                                 margin={"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"},
                                 display_header_footer=True, header_template="<span></span>",
                                 footer_template=footer)
        finally:
            browser.close()
    return io.BytesIO(pdf_bytes)
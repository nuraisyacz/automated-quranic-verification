"""utils/certificate.py - reference numbers and the PDF verification certificate.

The certificate contains no Arabic text (only numbers, English labels and hashes), so it needs
no Arabic font or RTL shaping. Needs: pip install reportlab "qrcode[pil]"
"""
import io
import re
import secrets
import textwrap
from datetime import datetime, timezone

# Crockford base32: no I, L, O, U, so reference numbers are easy to read out and type.
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_REF_RE = re.compile(r"^QV-(\d{8})-([0-9A-HJKMNP-TV-Z]{8})-([0-9A-HJKMNP-TV-Z])$")

TYPE_LABELS = {
    "quranic_text": "Quranic Text",
    "translation": "Quranic Translation",
}

STATUS_TEXT = {
    "accurate": ("VERIFIED", (0.10, 0.50, 0.25)),
    "partially_accurate": ("PARTIALLY VERIFIED", (0.80, 0.50, 0.05)),
    "inaccurate": ("NOT VERIFIED", (0.75, 0.15, 0.15)),
}


def _check_char(body):
    """Luhn mod-32 check character; catches single typos and most swaps."""
    n, factor, total = len(ALPHABET), 2, 0
    for ch in reversed(body):
        addend = factor * ALPHABET.index(ch)
        factor = 1 if factor == 2 else 2
        total += addend // n + addend % n
    return ALPHABET[(n - total % n) % n]


def new_reference_no(now=None):
    """QV-YYYYMMDD-XXXXXXXX-C  (date + 40 random bits + check character)."""
    now = now or datetime.now(timezone.utc)
    body = now.strftime("%Y%m%d") + "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"QV-{body[:8]}-{body[8:]}-{_check_char(body)}"


def is_valid_reference_no(ref):
    """Format and check character only; says nothing about whether it was issued."""
    m = _REF_RE.match((ref or "").strip().upper())
    return bool(m) and _check_char(m.group(1) + m.group(2)) == m.group(3)


def make_qr_png(url):
    import qrcode
    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def build_certificate_pdf(c, verify_url):
    """c: dict of the stored certificate fields (see VerificationCertificate.to_dict())."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    ink, muted = colors.HexColor("#1f2937"), colors.HexColor("#6b7280")
    label, color = STATUS_TEXT.get(c["status"], ("UNKNOWN", (0.3, 0.3, 0.3)))
    stamp = colors.Color(*color)
    vtype = c.get("verification_type") or "quranic_text"
    is_text = vtype == "quranic_text"
    type_label = TYPE_LABELS.get(vtype, "Quranic Content")

    # Double border
    pdf.setStrokeColor(stamp)
    pdf.setLineWidth(2.2)
    pdf.rect(10 * mm, 10 * mm, W - 20 * mm, H - 20 * mm)
    pdf.setLineWidth(0.6)
    pdf.rect(13 * mm, 13 * mm, W - 26 * mm, H - 26 * mm)

    y = H - 34 * mm
    pdf.setFillColor(ink)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(W / 2, y, "CERTIFICATE OF VERIFICATION")
    y -= 7 * mm
    pdf.setFont("Helvetica", 10.5)
    pdf.setFillColor(muted)
    pdf.drawCentredString(W / 2, y, type_label + " Verification")

    y -= 20 * mm
    pdf.setFillColor(stamp)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(W / 2, y, label)

    y -= 14 * mm
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(W / 2, y, "REFERENCE NUMBER")
    y -= 7 * mm
    pdf.setFillColor(ink)
    pdf.setFont("Courier-Bold", 18)
    pdf.drawCentredString(W / 2, y, c["reference_no"])

    # Details
    left, right = 24 * mm, W - 24 * mm
    y -= 14 * mm
    issued = c["issued_at"]
    if hasattr(issued, "strftime"):
        issued = issued.strftime("%d %B %Y, %H:%M UTC")
    rows = [
        ("Document", c["filename"]),
        ("Issued", issued),
        ("Scope checked", c["scope"] or "-"),
        ("Reference source", c["reference_source"]),
        ("Reference ayahs", str(c["reference_ayah_count"])),
    ]
    pdf.setFont("Helvetica", 10)
    for k, v in rows:
        pdf.setFillColor(muted)
        pdf.drawString(left, y, k)
        pdf.setFillColor(ink)
        lines = textwrap.wrap(str(v), 62) or ["-"]
        for line in lines[:3]:
            pdf.drawString(left + 42 * mm, y, line)
            y -= 5.2 * mm
        y -= 1.6 * mm

    # Results table
    y -= 3 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(ink)
    pdf.drawString(left, y, "Verification result")
    y -= 3 * mm
    pdf.setStrokeColor(colors.HexColor("#d1d5db"))
    pdf.setLineWidth(0.5)
    pdf.line(left, y, right, y)
    results = [
        ("Ayahs checked", c["total_rows"]),
        ("Exact matches (letters and diacritics)" if is_text else "Exact matches", c["exact_matches"]),
        ("Diacritic differences only" if is_text else "Partial matches", c["partial_matches"]),
        ("Letter mismatches" if is_text else "Mismatches", c["mismatches"]),
        ("No reference found", c["reference_not_found"]),
        ("Invalid or duplicate rows", c["invalid_rows"]),
    ]
    if is_text:  # translation flow does not report missing ayahs (yet)
        results.append(("Ayahs missing from document", c["missing_ayahs"]))
    results.append(("Overall accuracy", f"{c['accuracy_percentage']}%"))
    pdf.setFont("Helvetica", 10)
    for k, v in results:
        y -= 6.2 * mm
        pdf.setFillColor(ink)
        pdf.drawString(left, y, k)
        pdf.drawRightString(right, y, str(v))
    y -= 3.5 * mm
    pdf.line(left, y, right, y)

    # Hashes
    y -= 9 * mm
    pdf.setFont("Helvetica-Bold", 9)
    pdf.setFillColor(ink)
    pdf.drawString(left, y, "Content hash (SHA-256 of extracted text)")
    pdf.setFont("Courier", 8)
    for chunk in (c["content_sha256"][:32], c["content_sha256"][32:]):
        y -= 4.4 * mm
        pdf.drawString(left, y, chunk)
    y -= 6 * mm
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(left, y, "Reference fingerprint (SHA-256)")
    pdf.setFont("Courier", 8)
    for chunk in (c["reference_fingerprint"][:32], c["reference_fingerprint"][32:]):
        y -= 4.4 * mm
        pdf.drawString(left, y, chunk)
    if c.get("file_sha256"):
        y -= 6 * mm
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(left, y, "Original file hash (SHA-256, reported by uploader)")
        pdf.setFont("Courier", 8)
        for chunk in (c["file_sha256"][:32], c["file_sha256"][32:]):
            y -= 4.4 * mm
            pdf.drawString(left, y, chunk)

    # QR + verify link, bottom right / left
    qr = ImageReader(make_qr_png(verify_url))
    qr_size = 30 * mm
    pdf.drawImage(qr, right - qr_size, 34 * mm, qr_size, qr_size)
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(muted)
    pdf.drawString(left, 53 * mm, "Verify this certificate online:")
    pdf.setFont("Courier", 7.5)
    for i, line in enumerate(textwrap.wrap(verify_url, 52)[:3]):
        pdf.drawString(left, 49 * mm - i * 4 * mm, line)

    pdf.setFont("Helvetica-Oblique", 7.5)
    pdf.setFillColor(muted)
    what = "including diacritics, " if is_text else ""
    note = ("This certificate records that the uploaded text was compared with the reference repository "
            "named above, " + what + "on the date shown. It applies only to the content "
            "identified by the hash above. It is not a religious ruling or endorsement.")
    for i, line in enumerate(textwrap.wrap(note, 105)):
        pdf.drawCentredString(W / 2, 28 * mm - i * 3.8 * mm, line)

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf


# ---- generic helpers any verification type can use ---------------------------------------
def _plain(text):
    return " ".join((text or "").split())


def hash_rows(rows, field, normalize=_plain):
    """SHA-256 of uploaded content in an order-independent form. For Arabic use
    quran_compare.content_hash instead (it applies Arabic-specific cleaning)."""
    import hashlib
    lines = []
    for row in rows:
        try:
            key = (int(row["surah_number"]), int(row["ayah_number"]))
        except (KeyError, TypeError, ValueError):
            key = (0, 0)
        lines.append("%d:%d:%s" % (key[0], key[1], normalize(row.get(field, ""))))
    return hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def fingerprint_items(items, normalize=_plain):
    """SHA-256 fingerprint of a reference table. items: iterable of (surah, ayah, text).
    Pins exactly which version of the reference a certificate was issued against."""
    import hashlib
    lines = sorted("%d:%d:%s" % (int(s), int(a), normalize(t)) for s, a, t in items)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
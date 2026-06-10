"""Generate verification report as PDF."""

from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF


class VerificationReportPDF(FPDF):
    def __init__(self, report_title: str):
        super().__init__()
        self.report_title = report_title

    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, self.report_title, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def _safe_text(text: str, max_len: int = 500) -> str:
    """Sanitize text for PDF output (latin-1 compatible)."""
    if not text:
        return ''
    cleaned = text.replace('\n', ' ').replace('\r', ' ')
    cleaned = cleaned.replace('\u2014', '-').replace('\u2013', '-')
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + '...'
    return cleaned.encode('latin-1', errors='replace').decode('latin-1')


def generate_verification_pdf(report: dict) -> BytesIO:
    """Build a PDF report from verification result JSON."""
    verification_type = report.get('document', {}).get('verification_type', 'translation')
    if verification_type == 'quranic_text':
        title = 'Quranic Text Verification Report'
        content_label = 'Arabic Text'
    else:
        title = 'Quranic Translation Verification Report'
        content_label = 'Translation'

    pdf = VerificationReportPDF(title)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    doc = report.get('document', {})
    summary = report.get('summary', {})
    details = report.get('details', [])

    generated_at = report.get('generated_at') or datetime.now(timezone.utc).isoformat()

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'Document Details', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"File: {_safe_text(doc.get('filename', 'N/A'))}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Generated: {_safe_text(generated_at)}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Total Rows: {doc.get('total_rows', 0)}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'Verification Summary', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)

    status_label = summary.get('verification_status', 'unknown').replace('_', ' ').title()
    pdf.cell(0, 6, f"Status: {status_label}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Accuracy: {summary.get('accuracy_percentage', 0)}%", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Exact Matches: {summary.get('exact_matches', 0)}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Partial Matches: {summary.get('partial_matches', 0)}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Mismatches: {summary.get('mismatches', 0)}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, f"Reference Not Found: {summary.get('reference_not_found', 0)}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'Mismatch Details', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)

    mismatch_rows = [d for d in details if d.get('status') not in ('accurate',)]
    content_width = pdf.epw
    if not mismatch_rows:
        pdf.cell(0, 6, 'All compared rows matched the reference.', new_x='LMARGIN', new_y='NEXT')
    else:
        for item in mismatch_rows[:100]:
            ref = f"{item.get('surah_number')}:{item.get('ayah_number')}"
            status = item.get('status', '').replace('_', ' ').title()
            sim = item.get('similarity_percentage', 0)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 6, f"Surah {ref} - {status} ({sim}% similar)", new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', '', 8)
            pdf.multi_cell(content_width, 4, f"Uploaded {content_label}: {_safe_text(item.get('uploaded_text', ''), 300)}")
            if item.get('reference_text'):
                pdf.multi_cell(content_width, 4, f"Reference {content_label}: {_safe_text(item.get('reference_text', ''), 300)}")
            msg = item.get('message', '')
            if msg:
                pdf.multi_cell(content_width, 4, f"Note: {_safe_text(msg, 200)}")
            pdf.ln(2)

        if len(mismatch_rows) > 100:
            pdf.cell(0, 6, f"... and {len(mismatch_rows) - 100} more mismatches.", new_x='LMARGIN', new_y='NEXT')

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

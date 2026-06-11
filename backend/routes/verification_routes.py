from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

from models import db, QuranTranslation, QuranArabicText
from utils.verification import verify_translation_rows, verify_quranic_text_rows
from utils.seed_data import (
    build_reference_lookup,
    build_arabic_reference_lookup,
    seed_reference_translations,
    seed_reference_arabic_text,
)
from utils.report_generator import generate_verification_pdf

verification_bp = Blueprint('verification', __name__)


@verification_bp.route('/verify/translation', methods=['POST'])
@jwt_required()
def verify_translation():
    """
    POST /api/verify/translation
    Compare uploaded translation rows against the approved reference repository.

    Body JSON:
      {
        "filename": "document.pdf",
        "rows": [
          {"surah_number": 67, "ayah_number": 1, "translation": "..."}
        ]
      }
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400

    rows = payload.get('rows')
    if not rows or not isinstance(rows, list):
        return jsonify({'success': False, 'message': 'Field "rows" must be a non-empty array.'}), 400

    filename = (payload.get('filename') or 'uploaded-document').strip()

    reference_count = QuranTranslation.query.count()
    if reference_count == 0:
        seed_result = seed_reference_translations()
        reference_count = QuranTranslation.query.count()
        if reference_count == 0:
            return jsonify({
                'success': False,
                'message': (
                    'No reference translation data available. '
                    'Please import approved translations via POST /api/quran/import-csv '
                    'or place CSV files in backend/data/.'
                ),
                'seed_result': seed_result,
            }), 503

    reference_lookup = build_reference_lookup()
    result = verify_translation_rows(rows, reference_lookup)

    report = {
        'document': {
            'filename': filename,
            'total_rows': len(rows),
            'verification_type': 'translation',
            'reference_source': 'quran_translations (approved reference repository)',
            'reference_ayah_count': reference_count,
        },
        'summary': result['summary'],
        'details': result['details'],
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }

    return jsonify({'success': True, 'report': report}), 200


@verification_bp.route('/verify/quranic-text', methods=['POST'])
@jwt_required()
def verify_quranic_text():
    """
    POST /api/verify/quranic-text
    Compare uploaded Quranic Arabic text rows against the trusted reference repository.

    Body JSON:
      {
        "filename": "document.pdf",
        "rows": [
          {"surah_number": 102, "ayah_number": 1, "arabic_text": "..."}
        ]
      }
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400

    rows = payload.get('rows')
    if not rows or not isinstance(rows, list):
        return jsonify({'success': False, 'message': 'Field "rows" must be a non-empty array.'}), 400

    filename = (payload.get('filename') or 'uploaded-document').strip()

    reference_count = QuranArabicText.query.count()
    if reference_count == 0:
        seed_result = seed_reference_arabic_text()
        reference_count = QuranArabicText.query.count()
        if reference_count == 0:
            return jsonify({
                'success': False,
                'message': (
                    'No reference Quranic text data available. '
                    'Please import approved Arabic text via POST /api/quran/import-arabic-csv '
                    'or place CSV files in backend/data/.'
                ),
                'seed_result': seed_result,
            }), 503

    reference_lookup = build_arabic_reference_lookup()
    result = verify_quranic_text_rows(rows, reference_lookup)

    report = {
        'document': {
            'filename': filename,
            'total_rows': len(rows),
            'verification_type': 'quranic_text',
            'reference_source': 'quran_arabic_text (trusted reference repository)',
            'reference_ayah_count': reference_count,
        },
        'summary': result['summary'],
        'details': result['details'],
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }

    return jsonify({'success': True, 'report': report}), 200


@verification_bp.route('/verify/translation/report/pdf', methods=['POST'])
@jwt_required()
def download_translation_report_pdf():
    """POST /api/verify/translation/report/pdf — PDF for translation verification."""
    return _download_report_pdf()


@verification_bp.route('/verify/quranic-text/report/pdf', methods=['POST'])
@jwt_required()
def download_quranic_text_report_pdf():
    """POST /api/verify/quranic-text/report/pdf — PDF for Quranic text verification."""
    return _download_report_pdf()


def _download_report_pdf():
    payload = request.get_json(silent=True)
    if not payload or 'report' not in payload:
        return jsonify({'success': False, 'message': 'Field "report" is required.'}), 400

    report = payload['report']
    pdf_buffer = generate_verification_pdf(report)
    safe_name = (report.get('document', {}).get('filename') or 'verification').replace('.', '-')
    verification_type = report.get('document', {}).get('verification_type', 'translation')
    type_suffix = 'quranic-text' if verification_type == 'quranic_text' else 'translation'
    download_name = f"{safe_name}-{type_suffix}-verification-report.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=download_name,
    )


@verification_bp.route('/verify/reference-status', methods=['GET'])
@jwt_required()
def reference_status():
    """
    GET /api/verify/reference-status
    Returns counts of reference data available for verification.
    """
    translation_count = QuranTranslation.query.count()
    arabic_count = QuranArabicText.query.count()

    return jsonify({
        'success': True,
        'translation_reference': {
            'count': translation_count,
            'status': 'ready' if translation_count > 0 else 'empty',
            'note': (
                'Malay translation (Juz 29) loaded from approved CSV reference. '
                'Partners can add more via POST /api/quran/import-csv.'
            ),
        },
        'arabic_text_reference': {
            'count': arabic_count,
            'status': 'ready' if arabic_count > 0 else 'empty',
            'note': (
                'Quranic Arabic text (Juz 30) loaded from trusted CSV reference. '
                'Add more via POST /api/quran/import-arabic-csv.'
            ),
        },
    }), 200

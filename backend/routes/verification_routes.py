import os
import re

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import db, QuranTranslation, QuranArabicText, VerificationCertificate
from utils.verification import verify_translation_rows
from utils.seed_data import (
    build_reference_lookup,
    seed_reference_translations,
    seed_reference_arabic_text,
)
from utils.report_generator import generate_verification_pdf
from utils.quran_compare import ReferenceIndex, content_hash
from utils.certificate import (
    new_reference_no, is_valid_reference_no, build_certificate_pdf, hash_rows, fingerprint_items,
)
from utils.result_contract import contract_problems

verification_bp = Blueprint('verification', __name__)

# Base URL of the React app; the certificate QR code links to <base>/certificate/<reference_no>.
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:5173').rstrip('/')
REFERENCE_SOURCE_NAME = 'MyQuranKDN (quran_arabic_text)'

_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
_index_cache = {'key': None, 'index': None}


def get_arabic_reference_index():
    """Load the reference table once and rebuild only when it changes."""
    count, last_update = db.session.query(
        func.count(QuranArabicText.id), func.max(QuranArabicText.updated_at)
    ).one()
    key = (count, last_update)
    if _index_cache['key'] != key:
        rows = db.session.query(
            QuranArabicText.surah_number, QuranArabicText.ayah_number, QuranArabicText.arabic_text
        ).all()
        _index_cache['index'] = ReferenceIndex(rows)
        _index_cache['key'] = key
    return _index_cache['index']


def _current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def _clean_sha256(payload):
    value = (payload.get('file_sha256') or '').strip().lower()
    return value if _SHA256_RE.match(value) else None


def _issue_certificate(*, verification_type, filename, file_sha256, content_sha256, summary,
                       scope, reference_source, reference_count, reference_fingerprint):
    """Shared by every verification type. Stores the result server-side and returns the record.
    Call it ONLY when summary['verification_status'] == 'accurate' (100% accurate)."""
    for _ in range(5):  # retry on the (very unlikely) reference-number collision
        cert = VerificationCertificate(
            reference_no=new_reference_no(),
            user_id=_current_user_id(),
            filename=filename[:255],
            verification_type=verification_type,
            status=summary['verification_status'],
            scope=scope,
            reference_source=reference_source,
            reference_ayah_count=reference_count,
            reference_fingerprint=reference_fingerprint,
            content_sha256=content_sha256,
            file_sha256=file_sha256,
            total_rows=int(summary.get('total_uploaded_rows', 0) or 0),
            exact_matches=int(summary.get('exact_matches', 0) or 0),
            partial_matches=int(summary.get('partial_matches', 0) or 0),
            mismatches=int(summary.get('mismatches', 0) or 0),
            reference_not_found=int(summary.get('reference_not_found', 0) or 0),
            invalid_rows=int(summary.get('invalid_rows', 0) or 0),
            missing_ayahs=int(summary.get('missing_ayahs', 0) or 0),
            accuracy_percentage=float(summary.get('accuracy_percentage', 0) or 0),
        )
        db.session.add(cert)
        try:
            db.session.commit()
            return cert
        except IntegrityError:
            db.session.rollback()
    raise RuntimeError('Could not allocate a unique certificate reference number.')


def _certificate_summary(cert):
    """The small block the page needs to show the certificate (or None when none was issued)."""
    if not cert:
        return None
    return {
        'reference_no': cert.reference_no,
        'issued_at': cert.issued_at.isoformat(),
        'verify_url': f'{PUBLIC_BASE_URL}/certificate/{cert.reference_no}',
    }


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

    # Checks that the result has the shape the report page, PDF and certificate expect.
    # Problems are only logged (see utils/result_contract.py), they never block the request.
    for problem in contract_problems(result):
        current_app.logger.warning('translation result contract: %s', problem)

    # ---- CERTIFICATE (same template as Quranic text) -------------------------------------
    # Issued only when the result is 100% accurate. For this to be correct, your
    # verify_translation_rows must set summary['verification_status'] = 'accurate' ONLY when
    # every row is an exact match.
    cert = None
    if result['summary'].get('verification_status') == 'accurate':
        try:
            cert = _issue_certificate(
                verification_type='translation',
                filename=filename,
                file_sha256=_clean_sha256(payload),
                content_sha256=hash_rows(rows, 'translation'),
                summary=result['summary'],
                scope=(result.get('coverage') or {}).get('scope', ''),
                reference_source='quran_translations (approved reference repository)',
                reference_count=reference_count,
                reference_fingerprint=fingerprint_items(
                    db.session.query(QuranTranslation.surah_number, QuranTranslation.ayah_number,
                                     QuranTranslation.translation).all()),
            )
        except RuntimeError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 500

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
        'certificate': _certificate_summary(cert),
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

    index = get_arabic_reference_index()
    result = index.verify(rows)

    # A certificate is issued ONLY when the document is 100% accurate: every row an exact match
    # (letters and diacritics), nothing missing, no invalid or duplicate rows.
    cert = None
    if result['summary']['verification_status'] == 'accurate':
        try:
            cert = _issue_certificate(
                verification_type='quranic_text',
                filename=filename,
                file_sha256=_clean_sha256(payload),
                content_sha256=content_hash(rows),
                summary=result['summary'],
                scope=result['coverage']['scope'],
                reference_source=REFERENCE_SOURCE_NAME,
                reference_count=len(index),
                reference_fingerprint=index.fingerprint,
            )
        except RuntimeError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 500

    report = {
        'document': {
            'filename': filename,
            'total_rows': len(rows),
            'verification_type': 'quranic_text',
            'reference_source': 'quran_arabic_text (trusted reference repository)',
            'reference_ayah_count': reference_count,
        },
        'summary': result['summary'],
        'coverage': result['coverage'],
        'details': result['details'],
        'certificate': _certificate_summary(cert),
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }

    return jsonify({'success': True, 'report': report}), 200


@verification_bp.route('/verify/certificate/<reference_no>', methods=['GET'])
def check_certificate(reference_no):
    """PUBLIC (no login): confirm a certificate reference number is genuine and show its result."""
    ref = reference_no.strip().upper()
    if not is_valid_reference_no(ref):
        return jsonify({'success': True, 'valid': False,
                        'message': 'This is not a valid certificate reference number.'}), 200
    cert = VerificationCertificate.query.filter_by(reference_no=ref).first()
    if not cert:
        return jsonify({'success': True, 'valid': False,
                        'message': 'No certificate was issued with this reference number.'}), 200
    return jsonify({'success': True, 'valid': True, 'certificate': cert.to_public_dict()}), 200


@verification_bp.route('/verify/certificate/<reference_no>/pdf', methods=['GET'])
@jwt_required()
def download_certificate_pdf(reference_no):
    """Certificate PDF, rebuilt from the stored record. Only the user who ran the verification."""
    ref = reference_no.strip().upper()
    cert = VerificationCertificate.query.filter_by(reference_no=ref).first()
    if not cert:
        return jsonify({'success': False, 'message': 'Certificate not found.'}), 404
    uid = _current_user_id()
    if cert.user_id is not None and cert.user_id != uid:
        return jsonify({'success': False, 'message': 'You can only download your own certificates.'}), 403

    try:
        pdf = build_certificate_pdf(cert.to_dict(), f'{PUBLIC_BASE_URL}/certificate/{cert.reference_no}')
    except ImportError as exc:
        current_app.logger.exception('Certificate PDF failed (missing package)')
        return jsonify({'success': False,
                        'message': f'Missing Python package ({exc.name}). Run: pip install reportlab "qrcode[pil]"'}), 500
    except Exception as exc:
        current_app.logger.exception('Certificate PDF failed')
        return jsonify({'success': False, 'message': f'Certificate generation failed: {exc}'}), 500
    return send_file(pdf, mimetype='application/pdf', as_attachment=True,
                     download_name=f'{cert.reference_no}-certificate.pdf')


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
    try:
        pdf_buffer = generate_verification_pdf(report)
    except Exception as exc:  # e.g. PDF engine (playwright/chromium) not installed
        current_app.logger.exception('Report PDF generation failed')
        return jsonify({'success': False, 'message': f'PDF generation failed: {exc}'}), 500
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
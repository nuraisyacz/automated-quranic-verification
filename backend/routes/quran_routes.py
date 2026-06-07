from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from io import TextIOWrapper
import csv
from models import db, QuranTranslation
from datetime import datetime, timezone

quran_bp = Blueprint('quran', __name__)


@quran_bp.route('/import-csv', methods=['POST'])
def import_csv():
    """POST /api/quran/import-csv
    Accepts multipart/form-data with a file field named 'file'.
    Imports rows with columns: surah_number, ayah_number, translation
    Avoids duplicates based on surah_number + ayah_number.
    Returns inserted and skipped counts.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    if filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    # Try reading as utf-8, fallback to latin-1 if decode error
    inserted = 0
    skipped = 0
    line_no = 0
    try:
        stream = TextIOWrapper(file.stream, encoding='utf-8', errors='replace')
        reader = csv.DictReader(stream)
    except Exception:
        return jsonify({'success': False, 'message': 'Failed to parse CSV file'}), 400

    required_fields = {'surah_number', 'ayah_number', 'translation'}
    for row in reader:
        line_no += 1
        # Validate presence of required fields
        if not required_fields.issubset(set(k.strip() for k in row.keys())):
            skipped += 1
            continue

        try:
            surah_raw = row.get('surah_number')
            ayah_raw = row.get('ayah_number')
            translation = (row.get('translation') or '').strip()

            surah_number = int(surah_raw) if surah_raw and str(surah_raw).strip() != '' else None
            ayah_number = int(ayah_raw) if ayah_raw and str(ayah_raw).strip() != '' else None

            if surah_number is None or ayah_number is None or translation == '':
                skipped += 1
                continue

        except Exception:
            skipped += 1
            continue

        # Check for duplicates
        exists = QuranTranslation.query.filter_by(surah_number=surah_number, ayah_number=ayah_number).first()
        if exists:
            skipped += 1
            continue

        # Insert
        try:
            new_row = QuranTranslation(surah_number=surah_number, ayah_number=ayah_number, translation=translation)
            db.session.add(new_row)
            db.session.flush()  # ensure id assigned
            inserted += 1
        except Exception:
            db.session.rollback()
            skipped += 1
            continue

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database commit failed: {str(e)}'}), 500

    return jsonify({'success': True, 'inserted': inserted, 'skipped': skipped}), 200


@quran_bp.route('/search', methods=['GET'])
def search_translations():
    """GET /api/quran/search
    Query parameters:
      - surah_number
      - ayah_number
      - keyword
    Returns matching translation records.
    """
    try:
        surah = request.args.get('surah_number', type=int)
        ayah = request.args.get('ayah_number', type=int)
        keyword = request.args.get('keyword', type=str)

        query = QuranTranslation.query

        if surah is not None:
            query = query.filter(QuranTranslation.surah_number == surah)
        if ayah is not None:
            query = query.filter(QuranTranslation.ayah_number == ayah)
        if keyword:
            kw = keyword.strip()
            if kw != '':
                ilike_pattern = f"%{kw}%"
                query = query.filter(QuranTranslation.translation.ilike(ilike_pattern))

        results = query.order_by(QuranTranslation.surah_number, QuranTranslation.ayah_number).all()
        out = [r.to_dict() for r in results]
        if not out:
            return jsonify({'success': True, 'count': 0, 'results': [], 'message': 'No matching translation found'}), 200

        return jsonify({'success': True, 'count': len(out), 'results': out}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

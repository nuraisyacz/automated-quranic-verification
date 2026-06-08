import csv
import os
import re
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from config import Config

# Load one juzuk of Quranic Arabic text for the search demo
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'quranic_text_juzuk_30.csv')
QURANIC_TEXT_DATA = []
with open(DATA_FILE_PATH, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        QURANIC_TEXT_DATA.append({
            'juz_number': int(row.get('juz_number') or 0),
            'surah_number': int(row.get('surah_number') or 0),
            'surah_name': row.get('surah_name', '').strip(),
            'ayah_number': int(row.get('ayah_number') or 0),
            'arabic_text': row.get('arabic_text', '').strip()
        })

# Define blueprint for dashboard routes
dashboard_bp = Blueprint('dashboard', __name__)


def allowed_file(filename):
    """Return True when the filename has an allowed document extension."""
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in Config.ALLOWED_UPLOAD_EXTENSIONS


def is_arabic_text(value):
    if not value:
        return False
    return bool(re.search(r'[\u0600-\u06FF]', value))


def is_translation_text(value):
    if not value:
        return False
    return bool(re.search(r'[A-Za-z]', value))


def make_safe_output_filename(source_filename):
    base_name = secure_filename(source_filename) if source_filename else 'extracted'
    name, _ = os.path.splitext(base_name)
    return f"{name}_extracted_{uuid4().hex}.csv"


def extract_rows_from_csv(file_path):
    rows = []
    with open(file_path, encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        potential_arabic_keys = {'arabic_text', 'arabic', 'quranic_text', 'text_arabic', 'arabic verse'}
        potential_translation_keys = {'translation', 'english', 'bahasa', 'bahasa_melayu', 'malay', 'translation_text'}

        for row in reader:
            row_keys = {k.strip().lower() for k in row.keys() if k}
            arabic_text = ''
            translation_text = ''
            for key in row_keys:
                if key in potential_arabic_keys:
                    arabic_text = row.get(key, '').strip()
                if key in potential_translation_keys:
                    translation_text = row.get(key, '').strip()

            if not arabic_text or not is_arabic_text(arabic_text):
                for key in row_keys:
                    candidate = row.get(key, '').strip()
                    if is_arabic_text(candidate):
                        arabic_text = candidate
                        break

            if not translation_text:
                for key in row_keys:
                    candidate = row.get(key, '').strip()
                    if is_translation_text(candidate):
                        translation_text = candidate
                        break

            if arabic_text or translation_text:
                rows.append({
                    'arabic_text': arabic_text,
                    'translation': translation_text
                })
    return rows


def extract_rows_from_text(file_path):
    rows = []
    with open(file_path, encoding='utf-8', errors='replace') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    current_arabic = ''
    for line in lines:
        if is_arabic_text(line) and not is_translation_text(line):
            current_arabic = line
            continue

        if is_translation_text(line) and not is_arabic_text(line):
            if current_arabic:
                rows.append({'arabic_text': current_arabic, 'translation': line})
                current_arabic = ''
            else:
                rows.append({'arabic_text': '', 'translation': line})
            continue

        if is_arabic_text(line) and is_translation_text(line):
            arabic_part = ''.join([char for char in line if re.search(r'[\u0600-\u06FF]', char)])
            translation_part = ''.join([char for char in line if not re.search(r'[\u0600-\u06FF]', char)]).strip(' -:')
            rows.append({'arabic_text': arabic_part.strip(), 'translation': translation_part.strip()})
            current_arabic = ''
            continue

        if current_arabic:
            rows.append({'arabic_text': current_arabic, 'translation': line})
            current_arabic = ''
        else:
            rows.append({'arabic_text': '', 'translation': line})

    return rows


def write_extracted_csv(rows, output_path):
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['arabic_text', 'translation'])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                'arabic_text': row.get('arabic_text', ''),
                'translation': row.get('translation', '')
            })


@dashboard_bp.route('/verify-document', methods=['GET'])
@jwt_required()
def verify_document_placeholder():
    """
    GET /api/verify-document
    Protected placeholder route.
    """
    return jsonify({
        'message': 'Document verification module will be developed in the next phase.'
    }), 200


@dashboard_bp.route('/extracted-file/<path:filename>', methods=['GET'])
@jwt_required()
def serve_extracted_file(filename):
    """Serve extracted CSV files from the uploads directory."""
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        return jsonify({'success': False, 'message': 'Invalid filename.'}), 400

    return send_from_directory(Config.UPLOAD_FOLDER, filename, as_attachment=False, mimetype='text/csv')


@dashboard_bp.route('/extract-document', methods=['POST'])
@jwt_required()
def extract_uploaded_document():
    """Extract Arabic Quranic text and translation from an uploaded document."""
    payload = request.get_json(silent=True) or {}
    stored_filename = payload.get('stored_filename')

    if not stored_filename:
        return jsonify({'success': False, 'message': 'Stored filename is required for extraction.'}), 400

    if '..' in stored_filename or '/' in stored_filename or '\\' in stored_filename:
        return jsonify({'success': False, 'message': 'Invalid stored filename.'}), 400

    upload_folder = Config.UPLOAD_FOLDER
    source_path = os.path.join(upload_folder, secure_filename(stored_filename))
    if not os.path.exists(source_path):
        return jsonify({'success': False, 'message': 'Uploaded document not found.'}), 404

    extension = stored_filename.rsplit('.', 1)[-1].lower()
    extracted_rows = []

    if extension == 'csv':
        extracted_rows = extract_rows_from_csv(source_path)
    elif extension == 'txt':
        extracted_rows = extract_rows_from_text(source_path)
    else:
        try:
            extracted_rows = extract_rows_from_text(source_path)
        except Exception:
            extracted_rows = []

    if not extracted_rows:
        return jsonify({
            'success': False,
            'message': 'Unable to extract Quranic text and translation from the uploaded document.'
        }), 400

    output_filename = make_safe_output_filename(stored_filename)
    output_path = os.path.join(upload_folder, output_filename)
    write_extracted_csv(extracted_rows, output_path)

    return jsonify({
        'success': True,
        'message': 'Extraction completed. The CSV file is ready to view.',
        'extracted_count': len(extracted_rows),
        'download_url': f'/api/extracted-file/{output_filename}'
    }), 200


def allowed_file(filename):
    """Return True when the filename has an allowed document extension."""
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in Config.ALLOWED_UPLOAD_EXTENSIONS


@dashboard_bp.route('/verify-document', methods=['POST'])
@jwt_required()
def upload_quranic_document():
    """POST /api/verify-document
    Accepts a Quranic document upload and stores it temporarily for verification.
    """
    if 'document' not in request.files:
        return jsonify({'success': False, 'message': 'No file part found in the request.'}), 400

    document = request.files['document']
    if document.filename == '':
        return jsonify({'success': False, 'message': 'No file selected for upload.'}), 400

    if not allowed_file(document.filename):
        allowed_types = ', '.join(sorted(Config.ALLOWED_UPLOAD_EXTENSIONS))
        return jsonify({
            'success': False,
            'message': f'Unsupported file format. Allowed formats: {allowed_types}.'
        }), 400

    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)

    safe_filename = secure_filename(document.filename)
    unique_filename = f"{uuid4().hex}_{safe_filename}"
    destination_path = os.path.join(upload_folder, unique_filename)

    try:
        document.save(destination_path)
    except Exception as exc:
        return jsonify({
            'success': False,
            'message': 'Unable to save the uploaded file. Please try again.',
            'error': str(exc)
        }), 500

    return jsonify({
        'success': True,
        'message': 'Document uploaded and stored temporarily for verification.',
        'stored_filename': unique_filename
    }), 200

@dashboard_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    GET /api/dashboard
    Protected route returning welcome information.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401
        
    return jsonify({
        'welcome_message': f"Welcome, {user.full_name}",
        'description': "This system helps verify digital Quranic text and translations using trusted reference data.",
        'user': user.to_dict()
    }), 200


@dashboard_bp.route('/verify-document', methods=['GET'])
@jwt_required()
def verify_document_placeholder():
    """
    GET /api/verify-document
    Protected placeholder route.
    """
    return jsonify({
        'message': 'Document verification module will be developed in the next phase.'
    }), 200


@dashboard_bp.route('/search-quranic-text', methods=['GET'])
@jwt_required()
def search_quranic_text():
    """
    GET /api/search-quranic-text
    Protected Quranic text search route.
    Supports optional query parameters:
      - surah_number
      - ayah_number
      - juz_number
      - keyword
    """
    surah = request.args.get('surah_number', type=int)
    ayah = request.args.get('ayah_number', type=int)
    juz = request.args.get('juz_number', type=int)
    keyword = request.args.get('keyword', type=str)

    if surah is None and ayah is None and juz is None and not keyword:
        return jsonify({'success': False, 'message': 'Please provide at least one search parameter.'}), 400

    matches = QURANIC_TEXT_DATA

    if juz is not None:
        matches = [item for item in matches if item.get('juz_number') == juz]
    if surah is not None:
        matches = [item for item in matches if item.get('surah_number') == surah]
    if ayah is not None:
        matches = [item for item in matches if item.get('ayah_number') == ayah]
    if keyword:
        kw = keyword.strip()
        if kw != '':
            matches = [
                item for item in matches
                if kw in item.get('arabic_text', '') or kw in item.get('surah_name', '')
            ]

    ordered = sorted(matches, key=lambda item: (item.get('surah_number', 0), item.get('ayah_number', 0)))
    return jsonify({
        'success': True,
        'count': len(ordered),
        'results': ordered,
        'juz_number': 30,
        'message': 'Quranic text search completed.'
    }), 200

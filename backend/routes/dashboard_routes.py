import csv
import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User

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

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User

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
def search_quranic_text_placeholder():
    """
    GET /api/search-quranic-text
    Protected placeholder route.
    """
    return jsonify({
        'message': 'Quranic text search module will be developed in the next phase.'
    }), 200

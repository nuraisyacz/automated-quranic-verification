import csv
import os
import psycopg2
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User

# =========================
# BLUEPRINT
# =========================
dashboard_bp = Blueprint('dashboard', __name__)

# =========================
# DB CONNECTION
# =========================
def get_conn():
    return psycopg2.connect(
        dbname="quran_verification",
        user="postgres",
        password="Nurulizzani20.",
        host="localhost",
        port="5432"
    )

# =========================
# DASHBOARD
# =========================
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


# =========================
# VERIFY PLACEHOLDER
# =========================
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


# =========================
# SEARCH QURANIC TEXT
# =========================
@dashboard_bp.route('/search-quranic-text', methods=['GET'])
@jwt_required()
def search_quranic_text():

    try:

        juz = request.args.get('juz_number', type=int)
        surah = request.args.get('surah_number', type=int)
        ayah = request.args.get('ayah_number', type=int)

        if juz is None and surah is None and ayah is None:
            return jsonify({
                "success": False,
                "message": "Provide juz_number, surah_number or ayah_number"
            }), 400

        conn = get_conn()
        cur = conn.cursor()

        # 🔥 DEBUG: confirm real database Flask is using
        cur.execute("""
            SELECT current_database(), current_user, inet_server_addr(), inet_server_port();
        """)
        print("🔥 ACTUAL DB:", cur.fetchone())

        print("SEARCHING JUZ:", juz)

        query = """
            SELECT id, juz_number, surah_number, surah_name,
                ayah_number, arabic_text
            FROM quran_arabic_text
        """

        conditions = []
        params = []

        if juz is not None:
            conditions.append("juz_number = %s")
            params.append(juz)

        if surah is not None:
            conditions.append("surah_number = %s")
            params.append(surah)

        if ayah is not None:
            conditions.append("ayah_number = %s")
            params.append(ayah)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY surah_number, ayah_number"

        print(query)
        print(params)

        cur.execute(query, params)

        rows = cur.fetchall()

        print("ROWS FOUND:", len(rows))

        conn.close()

        return jsonify({
            "success": True,
            "juz_number": juz,
            "count": len(rows),
            "results": [
                {
                    "id": r[0],
                    "juz_number": r[1],
                    "surah_number": r[2],
                    "surah_name": r[3],
                    "ayah_number": r[4],
                    "arabic_text": r[5],
                }
                for r in rows
            ]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
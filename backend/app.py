import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.quran_routes import quran_bp

def create_app():
    """
    App factory to build and configure the Flask Application.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable Cross-Origin Resource Sharing (CORS)
    # Allows our frontend (Vite/React running on another port like 5173) to communicate with this API
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Bind SQLAlchemy database instance to Flask application
    db.init_app(app)

    # Setup JWT Manager for route authentication
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'message': 'Your session has expired. Please login again.',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'message': 'Signature verification failed. Please log in again.',
            'error': 'token_invalid'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'message': 'Request does not contain an access token. Please log in.',
            'error': 'authorization_required'
        }), 401

    # Register blueprints (routing modules)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(quran_bp, url_prefix='/api/quran')

    # Basic root route for verification
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'system_name': 'Automated Digital Quranic Text and Translation Verification System API',
            'status': 'Online',
            'version': '1.0.0-FYP-Prototype'
        }), 200

    # Auto-create database tables on startup
    with app.app_context():
        try:
            db.create_all()
            print("Successfully verified PostgreSQL connection and initialized tables.")
        except Exception as e:
            print("\n" + "="*80, file=sys.stderr)
            print("DATABASE SETUP WARNING:", file=sys.stderr)
            print("Could not connect to the PostgreSQL database.", file=sys.stderr)
            print(f"Error: {e}", file=sys.stderr)
            print("\nPlease make sure that:", file=sys.stderr)
            print("1. PostgreSQL is installed and running on your system.", file=sys.stderr)
            print("2. You have created a database named 'quran_verification'.", file=sys.stderr)
            print("3. The connection string in backend/.env is correct.", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)

    return app

app = create_app()

if __name__ == '__main__':
    # Start the Flask development server on port 5001
    app.run(host='0.0.0.0', port=5001, debug=True)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from utils.auth_utils import hash_password, check_password, is_valid_email

# Define blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Registers a new user account with validations.
    """
    data = request.get_json() or {}
    
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    # 1. Validation: Please fill in all required fields
    if not full_name or not email or not password or not confirm_password:
        return jsonify({'message': 'Please fill in all required fields'}), 400
        
    # 2. Validation: Email must be in valid email format
    if not is_valid_email(email):
        return jsonify({'message': 'Please enter a valid email address'}), 400
        
    # 3. Validation: Password must be at least 8 characters
    if len(password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
        
    # 4. Validation: Passwords do not match
    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400
        
    # 5. Validation: Email must be unique in the database
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'Email already registered'}), 400

    # If validations pass, hash password and save user
    hashed = hash_password(password)
    new_user = User()
    new_user.full_name = full_name
    new_user.email = email
    new_user.password_hash = hashed
    new_user.role = 'user'
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'message': 'Registration successful. Please login.',
            'user': new_user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Server error during registration: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authenticates a user and returns a JWT token.
    """
    data = request.get_json() or {}
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Validation: Email and password cannot be empty
    if not email:
        return jsonify({'message': 'Please enter your email'}), 400
    if not password:
        return jsonify({'message': 'Please enter your password'}), 400
        
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    # Verify user exists and password is correct
    if not user or not check_password(user.password_hash, password):
        return jsonify({'message': 'Invalid email or password'}), 401
        
    # Generate JWT token using user's email as the identity
    access_token = create_access_token(identity=str(user.user_id))
    
    return jsonify({
        'message': 'Login successful.',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    Instructs the client to clear their authentication state.
    """
    # Since we are using stateless JWT, the main logout action happens on client-side (clearing localStorage).
    # Here, we can optionally provide a response to confirm the logout endpoint call.
    return jsonify({'message': 'Logout successful. Please clear token on client side.'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    GET /api/auth/me
    Retrieves the currently authenticated user's details.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 444
        
    return jsonify({
        'user': user.to_dict()
    }), 200

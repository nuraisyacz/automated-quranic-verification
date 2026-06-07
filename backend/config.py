import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Flask application settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fyp_quran_verification_secret_key_12345')
    
    # Database configuration
    # Defaulting to local PostgreSQL database named 'quran_verification'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/quran_verification'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt_fyp_secret_key_67890')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)  # Token valid for 2 hours
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

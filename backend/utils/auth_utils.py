import re
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using Werkzeug's default pbkdf2:sha256 algorithm.
    """
    return generate_password_hash(password)

def check_password(password_hash: str, password: str) -> bool:
    """
    Verifies a plain text password against its corresponding hash stored in the DB.
    """
    return check_password_hash(password_hash, password)

def is_valid_email(email: str) -> bool:
    """
    Validates email format.
    Allows common RFC 5322 special characters before '@':
    ! # $ % & ' * + - / = ? ^ _ ` { | } ~ .
    """
    if not email:
        return False

    email_regex = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(email_regex, email))
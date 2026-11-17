from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __init__(self, full_name=None, email=None, password_hash=None, role='user'):
        if full_name is not None:
            self.full_name = full_name
        if email is not None:
            self.email = email
        if password_hash is not None:
            self.password_hash = password_hash
        self.role = role

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class QuranTranslation(db.Model):
    __tablename__ = "quran_translation_bm"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    surah_number = db.Column(db.Integer, nullable=False)
    ayah_number = db.Column(db.Integer, nullable=False)
    translation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __init__(self, surah_number=None, ayah_number=None, translation=None):
        if surah_number is not None:
            self.surah_number = surah_number
        if ayah_number is not None:
            self.ayah_number = ayah_number
        if translation is not None:
            self.translation = translation

    def to_dict(self):
        return {
            "id": self.id,
            "surah_number": self.surah_number,
            "ayah_number": self.ayah_number,
            "translation": self.translation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<QuranTranslation Surah {self.surah_number}, Ayah {self.ayah_number}>"


class QuranArabicText(db.Model):
    """
    Trusted reference repository for Quranic Arabic text verification.
    Placeholder model — partner can populate via CSV import (import-arabic-csv endpoint).
    """
    __tablename__ = "quran_arabic_text"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    juz_number = db.Column(db.Integer, nullable=True)
    surah_number = db.Column(db.Integer, nullable=False)
    surah_name = db.Column(db.String(100), nullable=True)
    ayah_number = db.Column(db.Integer, nullable=False)
    arabic_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    clean_arabic_text = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "juz_number": self.juz_number,
            "surah_number": self.surah_number,
            "surah_name": self.surah_name,
            "ayah_number": self.ayah_number,
            "arabic_text": self.arabic_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<QuranArabicText Surah {self.surah_number}, Ayah {self.ayah_number}>"

class VerificationCertificate(db.Model):
    """One row per completed Quranic text verification. The certificate PDF is always
    generated from this stored record, never from data posted by the browser."""
    __tablename__ = "verification_certificates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reference_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    verification_type = db.Column(db.String(30), nullable=False, default='quranic_text')
    status = db.Column(db.String(30), nullable=False)
    scope = db.Column(db.Text, nullable=True)
    reference_source = db.Column(db.String(200), nullable=False)
    reference_ayah_count = db.Column(db.Integer, nullable=False, default=0)
    reference_fingerprint = db.Column(db.String(64), nullable=False)
    content_sha256 = db.Column(db.String(64), nullable=False)
    file_sha256 = db.Column(db.String(64), nullable=True)  # reported by the browser, not checked
    total_rows = db.Column(db.Integer, nullable=False, default=0)
    exact_matches = db.Column(db.Integer, nullable=False, default=0)
    partial_matches = db.Column(db.Integer, nullable=False, default=0)
    mismatches = db.Column(db.Integer, nullable=False, default=0)
    reference_not_found = db.Column(db.Integer, nullable=False, default=0)
    invalid_rows = db.Column(db.Integer, nullable=False, default=0)
    missing_ayahs = db.Column(db.Integer, nullable=False, default=0)
    accuracy_percentage = db.Column(db.Float, nullable=False, default=0)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_public_dict(self):
        """What the public check page may show: no filename, no user."""
        return {
            "reference_no": self.reference_no,
            "verification_type": self.verification_type,
            "status": self.status,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "scope": self.scope,
            "reference_source": self.reference_source,
            "content_sha256": self.content_sha256,
            "total_rows": self.total_rows,
            "exact_matches": self.exact_matches,
            "partial_matches": self.partial_matches,
            "mismatches": self.mismatches,
            "reference_not_found": self.reference_not_found,
            "invalid_rows": self.invalid_rows,
            "missing_ayahs": self.missing_ayahs,
            "accuracy_percentage": self.accuracy_percentage,
        }
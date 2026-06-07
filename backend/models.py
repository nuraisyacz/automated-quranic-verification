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
    __tablename__ = "quran_translations"

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
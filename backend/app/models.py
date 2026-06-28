from datetime import datetime, timezone
from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # null for Google-only accounts
    is_active = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    email_verified = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

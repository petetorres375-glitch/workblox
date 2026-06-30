from datetime import datetime, timezone
from . import db


class Contact(db.Model):
    __tablename__ = "contacts"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    first_name   = db.Column(db.String(100), nullable=False, default="")
    last_name    = db.Column(db.String(100), nullable=False, default="")
    middle_init  = db.Column(db.String(10),  nullable=True)
    company      = db.Column(db.String(200), nullable=True)
    contact_type = db.Column(db.String(50),  nullable=False, default="Client")
    phones       = db.Column(db.Text, nullable=True)   # JSON array
    emails       = db.Column(db.Text, nullable=True)   # JSON array
    street       = db.Column(db.String(200), nullable=True)
    apt          = db.Column(db.String(50),  nullable=True)
    city         = db.Column(db.String(100), nullable=True)
    state        = db.Column(db.String(50),  nullable=True)
    zip          = db.Column(db.String(20),  nullable=True)
    notes        = db.Column(db.Text, nullable=True)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # null for Google-only accounts
    is_active = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    email_verified = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    plan = db.Column(db.String(50), nullable=False, default="free", server_default="free")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

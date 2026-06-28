import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    RATELIMIT_STORAGE_URI = "memory://"
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    MAIL_FROM = os.environ.get("MAIL_FROM", "")
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///workblox.db")
    # Railway exposes postgres:// but SQLAlchemy requires postgresql://
    SQLALCHEMY_DATABASE_URI = _db_url.replace("postgres://", "postgresql://", 1) if _db_url.startswith("postgres://") else _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

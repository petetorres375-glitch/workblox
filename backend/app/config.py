import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app


def create_token(sub, name, hours=168):
    payload = {
        "sub": sub,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=["HS256"],
    )


def create_verification_token(email):
    payload = {
        "sub": email,
        "kind": "verify",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_verification_token(token):
    payload = jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=["HS256"],
    )
    if payload.get("kind") != "verify":
        raise ValueError("Invalid token type")
    return payload["sub"]

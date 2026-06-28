import json
import urllib.request

from flask import current_app

from .auth import create_verification_token


def send_verification_email(email, name):
    api_key = current_app.config.get("SENDGRID_API_KEY", "")
    mail_from = current_app.config.get("MAIL_FROM", "")
    if not api_key or not mail_from:
        return False

    token = create_verification_token(email)
    app_url = current_app.config.get("APP_URL", "http://localhost:5000")
    verify_url = f"{app_url}/api/auth/verify/{token}"

    payload = json.dumps({
        "personalizations": [{"to": [{"email": email, "name": name}]}],
        "from": {"email": mail_from, "name": "Workblox"},
        "subject": "Verify your Workblox email",
        "content": [
            {
                "type": "text/plain",
                "value": (
                    f"Hi {name},\n\n"
                    f"Verify your Workblox email:\n{verify_url}\n\n"
                    "This link expires in 24 hours."
                ),
            },
            {
                "type": "text/html",
                "value": f"""<!DOCTYPE html>
<html>
<body style="font-family:Inter,system-ui,sans-serif;max-width:480px;margin:40px auto;padding:0 24px;color:#111">
  <p style="font-size:1rem;font-weight:800">Torres<span style="color:#FF6B00">Tech</span> Remote &mdash; Workblox</p>
  <h2 style="margin-top:0">Verify your email</h2>
  <p>Hi {name},</p>
  <p>Click the button below to verify your email address and complete your Workblox signup.</p>
  <a href="{verify_url}"
     style="display:inline-block;background:#FF6B00;color:#fff;padding:12px 28px;
            text-decoration:none;border-radius:8px;font-weight:700;margin:16px 0">
    Verify Email
  </a>
  <p style="color:#666;font-size:0.85rem">
    Link expires in 24 hours. If you didn't sign up for Workblox, ignore this email.
  </p>
</body>
</html>""",
            },
        ],
    }).encode()

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as res:
            return res.status == 202
    except Exception:
        return False

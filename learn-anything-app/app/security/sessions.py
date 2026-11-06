"""Legacy signed-token helpers; foundation HTTP auth uses LoginSession records."""
# app/security/sessions.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


def create_session_token(user_id: str, secret: str) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps({"uid": user_id})


def validate_session_token(token: str, secret: str, max_age: int) -> str | None:
    s = URLSafeTimedSerializer(secret)
    try:
        data = s.loads(token, max_age=max_age)
        return data.get("uid")
    except (BadSignature, SignatureExpired):
        return None

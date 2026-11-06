from itsdangerous import URLSafeTimedSerializer
from app.security.sessions import create_session_token, validate_session_token


def test_create_and_validate():
    token = create_session_token("user-123", secret="test-secret")
    user_id = validate_session_token(token, secret="test-secret", max_age=3600)
    assert user_id == "user-123"


def test_invalid_token():
    result = validate_session_token("garbage", secret="test-secret", max_age=3600)
    assert result is None

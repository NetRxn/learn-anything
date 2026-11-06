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


# --- FastAPI dependencies for auth ---

from fastapi import Request, HTTPException, Depends


async def get_current_user_id(request: Request) -> str | None:
    """Extract user ID from session cookie. Returns None if not authenticated."""
    from app.config import settings
    token = request.cookies.get("session")
    if not token:
        return None
    return validate_session_token(token, secret=settings.secret_key, max_age=settings.session_max_age)


async def require_auth(user_id: str | None = Depends(get_current_user_id)) -> str:
    """Dependency: require authenticated user. Raises 401 if not logged in."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


async def require_admin(user_id: str = Depends(require_auth)) -> str:
    """Dependency: require admin user. Raises 403 if not admin.
    In production, look up User.is_admin from DB. Simplified for Plan 1.
    """
    # TODO: Query User model to check is_admin. For now, first user is admin.
    return user_id

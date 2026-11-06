# app/security/oauth.py
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.security.sessions import create_session_token
from app.config import settings

oauth = OAuth()
router = APIRouter(prefix="/auth/oauth", tags=["oauth"])


def configure_oauth(google_client_id: str = "", google_client_secret: str = "",
                    github_client_id: str = "", github_client_secret: str = ""):
    """Call during setup or on app start when OAuth config exists in DB."""
    if google_client_id and google_client_secret:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    if github_client_id and github_client_secret:
        oauth.register(
            name="github",
            client_id=github_client_id,
            client_secret=github_client_secret,
            authorize_url="https://github.com/login/oauth/authorize",
            access_token_url="https://github.com/login/oauth/access_token",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )


@router.get("/google")
async def google_login(request: Request):
    client = oauth.create_client("google")
    if client is None:
        return RedirectResponse("/auth/login?error=google_not_configured")
    redirect_uri = request.url_for("google_callback")
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    client = oauth.create_client("google")
    if client is None:
        return RedirectResponse("/auth/login?error=google_not_configured")
    token = await client.authorize_access_token(request)
    userinfo = token.get("userinfo", {})
    email = userinfo.get("email")
    if not email:
        return RedirectResponse("/auth/login?error=no_email")
    # Find or create user by email + provider=google + oauth_id
    # For now, create session directly (full DB lookup in later integration)
    session_token = create_session_token(email, secret=settings.secret_key)
    resp = RedirectResponse("/")
    resp.set_cookie("session", session_token, httponly=True, samesite="lax", max_age=settings.session_max_age)
    return resp


@router.get("/github")
async def github_login(request: Request):
    client = oauth.create_client("github")
    if client is None:
        return RedirectResponse("/auth/login?error=github_not_configured")
    redirect_uri = request.url_for("github_callback")
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request):
    client = oauth.create_client("github")
    if client is None:
        return RedirectResponse("/auth/login?error=github_not_configured")
    token = await client.authorize_access_token(request)
    resp_user = await client.get("user", token=token)
    user_data = resp_user.json()
    email = user_data.get("email")
    if not email:
        # GitHub may not include email in profile — fetch from emails endpoint
        resp_emails = await client.get("user/emails", token=token)
        emails = resp_emails.json()
        primary = next((e for e in emails if e.get("primary")), None)
        email = primary["email"] if primary else None
    if not email:
        return RedirectResponse("/auth/login?error=no_email")
    session_token = create_session_token(email, secret=settings.secret_key)
    resp = RedirectResponse("/")
    resp.set_cookie("session", session_token, httponly=True, samesite="lax", max_age=settings.session_max_age)
    return resp

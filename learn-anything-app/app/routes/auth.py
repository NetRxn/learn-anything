# app/routes/auth.py
from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import RedirectResponse
from app.templating import templates
from app.security.passwords import hash_password, verify_password
from app.security.sessions import create_session_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    # TODO: Task 3 models + DB lookup — for now return error
    return templates.TemplateResponse(request, "auth/login.html", {"error": "Not implemented"})


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html")


@router.post("/register")
async def register(
    response: Response,
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
):
    # Placeholder — full DB integration in later step
    token = create_session_token("temp-user", secret=settings.secret_key)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("session", token, httponly=True, samesite="lax", max_age=settings.session_max_age)
    return resp

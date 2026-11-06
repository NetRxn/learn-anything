# app/routes/setup.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.templating import templates

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("")
async def welcome(request: Request):
    return templates.TemplateResponse(request, "setup/welcome.html", {"step": 1})


@router.get("/database")
async def database_step(request: Request):
    return templates.TemplateResponse(request, "setup/database.html", {"step": 2})


@router.post("/database")
async def database_save(request: Request, database_url: str = Form("")):
    # Validate connection, store config
    return RedirectResponse("/setup/llm", status_code=303)


@router.get("/llm")
async def llm_step(request: Request):
    return templates.TemplateResponse(request, "setup/llm.html", {"step": 3})


@router.post("/llm")
async def llm_save(request: Request, api_key: str = Form(""), model: str = Form("claude-sonnet-4-6")):
    return RedirectResponse("/setup/auth", status_code=303)


@router.get("/auth")
async def auth_step(request: Request):
    return templates.TemplateResponse(request, "setup/auth.html", {"step": 4})


@router.post("/auth")
async def auth_save(request: Request):
    return RedirectResponse("/setup/account", status_code=303)


@router.get("/account")
async def account_step(request: Request):
    return templates.TemplateResponse(request, "setup/account.html", {"step": 5})


@router.post("/account")
async def account_save(
    request: Request,
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
):
    # Create admin user, mark setup complete
    return RedirectResponse("/", status_code=303)

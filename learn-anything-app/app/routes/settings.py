# app/routes/settings.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.templating import templates

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def settings_page(request: Request):
    # In production: read all config from AppConfig, mask encrypted values
    return templates.TemplateResponse(request, "settings/index.html", {
        "llm_provider": "Anthropic Claude",
        "llm_model": "claude-sonnet-4-6",
        "llm_key_masked": "sk-ant-...****",
        "google_configured": False,
        "github_configured": False,
        "single_user": False,
    })


@router.post("/llm")
async def update_llm(request: Request, api_key: str = Form(""), model: str = Form("claude-sonnet-4-6")):
    # In production: encrypt api_key via SecretStore, save to AppConfig
    return RedirectResponse("/settings", status_code=303)


@router.post("/auth")
async def update_auth(request: Request):
    # In production: save OAuth config, toggle single_user
    return RedirectResponse("/settings", status_code=303)

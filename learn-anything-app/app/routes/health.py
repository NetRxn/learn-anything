# app/routes/health.py
import structlog
from fastapi import APIRouter
from sqlalchemy import text
from app.config import settings

log = structlog.get_logger()
router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    db_status = "not_configured"
    if settings.database_url:
        try:
            from app.database import SessionLocal
            if SessionLocal is not None:
                async with SessionLocal() as session:
                    await session.execute(text("SELECT 1"))
                db_status = "connected"
            else:
                db_status = "not_initialized"
        except Exception as exc:
            log.warning("health_db_check_failed", error=str(exc))
            db_status = "unreachable"

    return {
        "status": "ok" if db_status in ("connected", "not_configured") else "degraded",
        "version": "0.1.0",
        "state_backend": settings.state_backend,
        "database": db_status,
    }

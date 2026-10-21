"""Health check router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.session import get_db
from configs.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """System health check — verifies DB connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "database": db_status,
        "disclaimer": (
            "MANAS is a computational research platform. Results are "
            "statistical analyses of public research datasets."
        ),
    }

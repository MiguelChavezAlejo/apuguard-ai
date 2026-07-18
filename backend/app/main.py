from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "running",
        "version": settings.app_version,
    }


@app.get("/health/database", tags=["Health"])
def database_health(
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "database": "postgresql",
        "status": "connected",
    }
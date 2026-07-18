from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/database")
def database_health(
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "database": "postgresql",
        "status": "connected",
    }
from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    prefix="",
    tags=["System"],
)


@router.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "development",
        "version": settings.app_version,
    }
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.system import router as system_router
from app.core.config import settings
from app.database.database import Base, engine
from app.models import User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Plataforma autónoma de pentesting inteligente y generación "
        "de reportes de vulnerabilidades basada en OWASP Top 10."
    ),
    lifespan=lifespan,
)


app.include_router(system_router)
app.include_router(health_router)
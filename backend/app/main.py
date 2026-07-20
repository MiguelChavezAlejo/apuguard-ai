from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.system import router as system_router
from app.core.config import settings
from app.database.database import Base, engine
from app.models import Project, Scan, User, Vulnerability  # noqa: F401
from app.api.routes.scans import router as scans_router
from app.api.routes.reports import router as reports_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.admin import router as admin_router


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(scans_router)
app.include_router(reports_router)
app.include_router(admin_router)
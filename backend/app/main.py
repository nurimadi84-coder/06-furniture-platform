"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()

# furniture_platform/frontend — works for local uvicorn and Docker layout
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if not FRONTEND_DIR.is_dir():
    FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

origins = (
    ["*"]
    if settings.CORS_ORIGINS.strip() == "*"
    else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
)

# Wildcard origins are incompatible with credentialed CORS in browsers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/")
async def serve_index() -> FileResponse:
    """Landing page — open http://127.0.0.1:8000/ to see the site."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/track.html")
async def serve_track() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "track.html")


if FRONTEND_DIR.is_dir():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


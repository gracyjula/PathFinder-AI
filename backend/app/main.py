"""
NeuraLearn AI - Main FastAPI Application
AI-Powered Personalized Learning Operating System
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.api.routes import auth, profile, chat, roadmap, analytics, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Personalized Learning Operating System",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Vite dev server (5173), any other common local ports, and whatever
# FRONTEND_URL is set to in .env (defaults to http://localhost:5173).

_CORS_ORIGINS = list(
    {
        settings.FRONTEND_URL,           # from .env  (default: http://localhost:5173)
        "http://localhost:5173",          # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",          # CRA / other
        "http://127.0.0.1:3000",
        "http://localhost:4173",          # Vite preview
        "http://127.0.0.1:4173",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── API Routes ───────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router,      prefix=API_PREFIX)
app.include_router(profile.router,   prefix=API_PREFIX)
app.include_router(chat.router,      prefix=API_PREFIX)
app.include_router(roadmap.router,   prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(admin.router,     prefix=API_PREFIX)


# ─── Health / Root ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="Root health check")
async def root():
    """Returns a simple health confirmation. Open http://localhost:5173 for the UI."""
    return {"message": "NeuraLearn API is running"}


@app.get("/health", tags=["Health"], summary="Detailed health check")
async def health_check():
    return {
        "status": "healthy",
        "message": "NeuraLearn API is running",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "http://localhost:8000/api/docs",
        "frontend": "http://localhost:5173",
    }


@app.get("/api/v1/health", tags=["Health"], summary="Versioned health check")
async def health_v1():
    """Health check reachable at the API prefix — useful for readiness probes."""
    return {"message": "NeuraLearn API is running", "version": settings.APP_VERSION}


# ─── 404 catch-all (must be last) ─────────────────────────────────────────────
# When someone opens http://localhost:8000/login or /dashboard in their browser
# they get a helpful JSON message instead of the default {"detail":"Not Found"}.

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    path = request.url.path
    # Paths that look like React SPA routes (no dot = not a static file)
    spa_hint = not any(path.startswith(p) for p in ["/api", "/health", "/docs", "/redoc"])
    if spa_hint:
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Not Found",
                "hint": (
                    f"'{path}' is a React frontend route, not a backend API endpoint. "
                    "Open the React dev server at http://localhost:5173 instead. "
                    "API docs are at http://localhost:8000/api/docs"
                ),
            },
        )
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

"""
RunBait FastAPI application entry point.

Usage:
    # Development
    uvicorn main:app --reload --port 8000

    # Production
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from core.config import get_settings
from routers import auth, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="RunBait API",
    description="AI-driven automated QA pipeline for pull requests.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------

# SessionMiddleware is required by authlib for storing the OAuth state
# between the /login and /callback requests.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET,
    https_only=False,   # set True in production (HTTPS only)
    same_site="lax",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(users.router)


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "runbait-api"}

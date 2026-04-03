"""
main.py
────────
FastAPI application entry point.

Startup tasks:
  1. Create all DB tables
  2. Seed the default admin account (if not present)

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config.database import init_db, AsyncSessionLocal
from app.config.settings import settings
from app.routes import auth, users, gigs, orders, reviews, messages, admin


# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    await init_db()
    await _seed_admin()
    yield
    # ── SHUTDOWN (add cleanup here if needed) ────────────────────────────────


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A production-ready REST API for the Student Freelancing Marketplace.\n\n"
        "**Roles**: Student (seller) · Client (buyer) · Admin\n\n"
        "**Auth**: JWT Bearer tokens — obtain via `/auth/login`."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploaded images served at /uploads/*) ──────────────────────
import os, pathlib
pathlib.Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth.router,     prefix=API_PREFIX)
app.include_router(users.router,    prefix=API_PREFIX)
app.include_router(gigs.router,     prefix=API_PREFIX)
app.include_router(orders.router,   prefix=API_PREFIX)
app.include_router(reviews.router,  prefix=API_PREFIX)
app.include_router(messages.router, prefix=API_PREFIX)
app.include_router(admin.router,    prefix=API_PREFIX)


# ── Global exception handlers ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        import traceback
        detail = traceback.format_exc()
    else:
        detail = "An unexpected error occurred."
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error.", "detail": detail},
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# ── Seed helper ───────────────────────────────────────────────────────────────
async def _seed_admin():
    """Create the default admin account on first run if it does not exist."""
    from sqlalchemy import select
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        if result.scalar_one_or_none():
            return   # already exists

        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Platform Admin",
            role=UserRole.ADMIN,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        print(f"[SEED] Admin account created: {settings.ADMIN_EMAIL}")

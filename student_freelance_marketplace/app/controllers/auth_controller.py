"""
controllers/auth_controller.py
───────────────────────────────
Business logic for student/client signup, login, and token refresh.
All functions are called from routes/auth.py.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.controllers.schemas import (
    StudentSignupRequest, ClientSignupRequest, LoginRequest,
    TokenResponse, UserOut, RefreshRequest,
)


async def _get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


def _build_token_response(user: User) -> dict:
    return {
        "access_token":  create_access_token(user.id, user.role.value),
        "refresh_token": create_refresh_token(user.id),
        "token_type":    "bearer",
        "user":          UserOut.model_validate(user).model_dump(mode="json"),
    }


# ── Student signup ────────────────────────────────────────────────────────────
async def register_student(payload: StudentSignupRequest, db: AsyncSession) -> dict:
    """Create a new student account. Raises 409 if email already exists."""
    if await _get_user_by_email(payload.email, db):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered.")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.STUDENT,
        skills=payload.skills,
        bio=payload.bio,
    )
    db.add(user)
    await db.flush()   # get the generated UUID without committing yet
    return _build_token_response(user)


# ── Client signup ─────────────────────────────────────────────────────────────
async def register_client(payload: ClientSignupRequest, db: AsyncSession) -> dict:
    """Create a new client account. Raises 409 if email already exists."""
    if await _get_user_by_email(payload.email, db):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered.")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.CLIENT,
    )
    db.add(user)
    await db.flush()
    return _build_token_response(user)


# ── Login (shared for all roles) ──────────────────────────────────────────────
async def login(payload: LoginRequest, db: AsyncSession) -> dict:
    """Authenticate any user. Raises 401 for wrong credentials."""
    user = await _get_user_by_email(payload.email, db)

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")

    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account banned. Contact support.")

    return _build_token_response(user)


# ── Refresh access token ──────────────────────────────────────────────────────
async def refresh_access_token(payload: RefreshRequest, db: AsyncSession) -> dict:
    """Issue a new access token using a valid refresh token."""
    decoded = decode_token(payload.refresh_token)

    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.")

    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(decoded["sub"])))
    user: User | None = result.scalar_one_or_none()

    if not user or user.is_banned:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or banned.")

    return {
        "access_token":  create_access_token(user.id, user.role.value),
        "refresh_token": create_refresh_token(user.id),   # rotate refresh token
        "token_type":    "bearer",
        "user":          UserOut.model_validate(user).model_dump(mode="json"),
    }

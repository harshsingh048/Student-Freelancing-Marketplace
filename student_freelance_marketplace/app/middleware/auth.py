"""
middleware/auth.py
──────────────────
FastAPI dependency functions for JWT authentication.

Usage in routes:
    current_user: User = Depends(get_current_user)
    _: User = Depends(require_student)
    _: User = Depends(require_admin)
"""

from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_token

# ── Bearer token extractor ────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated. Provide a valid Bearer token.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT, fetch the user from DB, and return it.
    Raises 401 if token is missing, invalid, or expired.
    Raises 403 if user is banned.
    """
    if not credentials:
        raise _UNAUTHORIZED

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise _UNAUTHORIZED

    user_id: str = payload.get("sub")
    if not user_id:
        raise _UNAUTHORIZED

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise _UNAUTHORIZED

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been banned. Contact support.",
        )

    return user


# ── Role guard factories ──────────────────────────────────────────────────────

def _role_guard(*allowed_roles: UserRole):
    """Higher-order function that produces a role-checking dependency."""
    async def guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in allowed_roles]}",
            )
        return user
    return guard


# Pre-built role dependencies
require_student = _role_guard(UserRole.STUDENT)
require_client  = _role_guard(UserRole.CLIENT)
require_admin   = _role_guard(UserRole.ADMIN)
require_student_or_client = _role_guard(UserRole.STUDENT, UserRole.CLIENT)

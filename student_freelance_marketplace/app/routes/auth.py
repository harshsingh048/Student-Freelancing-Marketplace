"""
routes/auth.py
───────────────
POST /auth/signup/student
POST /auth/signup/client
POST /auth/login
POST /auth/refresh
GET  /auth/me
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers import auth_controller
from app.controllers.schemas import (
    ClientSignupRequest, LoginRequest,
    RefreshRequest, StudentSignupRequest,
)
from app.middleware.auth import get_current_user
from app.models.user import User
from app.utils.responses import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup/student", status_code=201, summary="Register a new student account")
async def signup_student(payload: StudentSignupRequest, db: AsyncSession = Depends(get_db)):
    data = await auth_controller.register_student(payload, db)
    return success_response(data, "Student registered successfully.", 201)


@router.post("/signup/client", status_code=201, summary="Register a new client account")
async def signup_client(payload: ClientSignupRequest, db: AsyncSession = Depends(get_db)):
    data = await auth_controller.register_client(payload, db)
    return success_response(data, "Client registered successfully.", 201)


@router.post("/login", summary="Login with email & password (any role)")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    data = await auth_controller.login(payload, db)
    return success_response(data, "Login successful.")


@router.post("/refresh", summary="Get a new access token using a refresh token")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = await auth_controller.refresh_access_token(payload, db)
    return success_response(data, "Token refreshed.")


@router.get("/me", summary="Get the currently authenticated user")
async def me(current_user: User = Depends(get_current_user)):
    from app.controllers.schemas import UserOut
    return success_response(
        UserOut.model_validate(current_user).model_dump(mode="json"),
        "Current user fetched.",
    )

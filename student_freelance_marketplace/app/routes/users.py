"""
routes/users.py
────────────────
GET    /users/students         – Browse students (public)
GET    /users/{user_id}        – Public profile
PUT    /users/me               – Update own profile
POST   /users/me/avatar        – Upload avatar
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config.database import get_db
from app.controllers import user_controller
from app.controllers.schemas import UpdateProfileRequest
from app.middleware.auth import get_current_user
from app.models.user import User
from app.utils.responses import paginated_response, success_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/students", summary="Browse active students (filterable by skill)")
async def list_students(
    page:      int           = Query(1, ge=1),
    page_size: int           = Query(10, ge=1, le=50),
    skill:     Optional[str] = Query(None, description="Filter by a specific skill"),
    db: AsyncSession         = Depends(get_db),
):
    result = await user_controller.get_student_list(page, page_size, skill, db)
    return paginated_response(result["items"], result["total"], page, page_size)


@router.get("/me", summary="Get your own detailed profile")
async def get_own_profile(current_user: User = Depends(get_current_user)):
    from app.controllers.schemas import UserOut
    return success_response(UserOut.model_validate(current_user).model_dump(mode="json"))


@router.put("/me", summary="Update your profile")
async def update_profile(
    payload:      UpdateProfileRequest,
    current_user: User             = Depends(get_current_user),
    db:           AsyncSession     = Depends(get_db),
):
    data = await user_controller.update_profile(current_user, payload, db)
    return success_response(data, "Profile updated.")


@router.post("/me/avatar", summary="Upload / replace your avatar image")
async def upload_avatar(
    file:         UploadFile    = File(...),
    current_user: User          = Depends(get_current_user),
    db:           AsyncSession  = Depends(get_db),
):
    data = await user_controller.upload_avatar(current_user, file, db)
    return success_response(data, "Avatar uploaded.")


@router.get("/{user_id}", summary="Get a user's public profile")
async def get_user_profile(user_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await user_controller.get_profile(user_id, db)
    return success_response(data)

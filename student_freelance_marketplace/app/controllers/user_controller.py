"""
controllers/user_controller.py
───────────────────────────────
Profile management for authenticated users.
"""

from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.controllers.schemas import UpdateProfileRequest, UserOut
from app.utils.file_upload import save_upload_file, delete_upload_file


async def get_profile(user_id: UUID, db: AsyncSession) -> dict:
    """Fetch any user's public profile by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    return UserOut.model_validate(user).model_dump(mode="json")


async def update_profile(
    current_user: User,
    payload: UpdateProfileRequest,
    db: AsyncSession,
) -> dict:
    """Update the calling user's own profile fields."""
    update_data = payload.model_dump(exclude_unset=True)

    # Serialize portfolio items to plain dicts
    if "portfolio_links" in update_data:
        update_data["portfolio_links"] = [
            item if isinstance(item, dict) else item.model_dump()
            for item in update_data["portfolio_links"]
        ]

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    return UserOut.model_validate(current_user).model_dump(mode="json")


async def upload_avatar(current_user: User, file: UploadFile, db: AsyncSession) -> dict:
    """Replace the user's avatar with a new uploaded image."""
    # Delete old avatar if present
    if current_user.avatar_url:
        delete_upload_file(current_user.avatar_url)

    url = await save_upload_file(file, sub_dir="avatars")
    current_user.avatar_url = url
    db.add(current_user)
    return {"avatar_url": url}


async def get_student_list(
    page: int,
    page_size: int,
    skill: str | None,
    db: AsyncSession,
) -> dict:
    """Return a paginated list of active students (for client browsing)."""
    from app.models.user import UserRole
    from sqlalchemy import func

    query = select(User).where(
        User.role == UserRole.STUDENT,
        User.is_active.is_(True),
        User.is_banned.is_(False),
    )

    if skill:
        # PostgreSQL ARRAY contains check
        query = query.where(User.skills.any(skill))

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Fetch page
    result = await db.execute(
        query.order_by(User.average_rating.desc())
              .offset((page - 1) * page_size)
              .limit(page_size)
    )
    users = result.scalars().all()

    return {
        "items": [UserOut.model_validate(u).model_dump(mode="json") for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

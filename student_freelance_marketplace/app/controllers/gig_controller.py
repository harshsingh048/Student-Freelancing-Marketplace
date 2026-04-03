"""
controllers/gig_controller.py
──────────────────────────────
Business logic for Gig creation, retrieval, update, and deletion.
Only students can create/edit/delete their own gigs.
"""

from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.gig  import Gig, GigCategory
from app.models.user import User, UserRole
from app.controllers.schemas import GigCreateRequest, GigUpdateRequest, GigOut
from app.utils.file_upload import save_upload_file, delete_upload_file


async def create_gig(
    payload: GigCreateRequest,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Create a new gig. Caller must be a student."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can create gigs.")

    gig = Gig(
        student_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        delivery_days=payload.delivery_days,
        revision_count=payload.revision_count,
    )
    db.add(gig)
    await db.flush()
    return GigOut.model_validate(gig).model_dump(mode="json")


async def get_gig(gig_id: UUID, db: AsyncSession) -> dict:
    """Fetch a single gig with its owner's profile."""
    result = await db.execute(
        select(Gig).where(Gig.id == gig_id, Gig.is_active.is_(True))
    )
    gig = result.scalar_one_or_none()
    if not gig:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gig not found.")
    return GigOut.model_validate(gig).model_dump(mode="json")


async def list_gigs(
    page: int,
    page_size: int,
    category: GigCategory | None,
    min_price: float | None,
    max_price: float | None,
    search: str | None,
    db: AsyncSession,
) -> dict:
    """Return paginated, filterable gig listings."""
    query = select(Gig).where(Gig.is_active.is_(True))

    if category:
        query = query.where(Gig.category == category)
    if min_price is not None:
        query = query.where(Gig.price >= min_price)
    if max_price is not None:
        query = query.where(Gig.price <= max_price)
    if search:
        query = query.where(
            Gig.title.ilike(f"%{search}%") | Gig.description.ilike(f"%{search}%")
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    result = await db.execute(
        query.order_by(Gig.created_at.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
    )
    gigs = result.scalars().all()

    return {
        "items": [GigOut.model_validate(g).model_dump(mode="json") for g in gigs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def list_my_gigs(student: User, db: AsyncSession) -> list:
    """Return all gigs belonging to the current student (active + inactive)."""
    result = await db.execute(
        select(Gig).where(Gig.student_id == student.id).order_by(Gig.created_at.desc())
    )
    return [GigOut.model_validate(g).model_dump(mode="json") for g in result.scalars().all()]


async def update_gig(
    gig_id: UUID,
    payload: GigUpdateRequest,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Update a gig. Only the owning student may do this."""
    gig = await _get_owned_gig(gig_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(gig, field, value)
    db.add(gig)
    return GigOut.model_validate(gig).model_dump(mode="json")


async def upload_gig_thumbnail(
    gig_id: UUID,
    file: UploadFile,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Upload / replace the thumbnail image for a gig."""
    gig = await _get_owned_gig(gig_id, current_user.id, db)
    if gig.thumbnail_url:
        delete_upload_file(gig.thumbnail_url)
    gig.thumbnail_url = await save_upload_file(file, sub_dir="thumbnails")
    db.add(gig)
    return {"thumbnail_url": gig.thumbnail_url}


async def delete_gig(
    gig_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> dict:
    """Soft-delete a gig (sets is_active=False)."""
    gig = await _get_owned_gig(gig_id, current_user.id, db)
    gig.is_active = False
    db.add(gig)
    return {"message": "Gig deactivated successfully."}


# ── Internal helper ───────────────────────────────────────────────────────────
async def _get_owned_gig(gig_id: UUID, student_id: UUID, db: AsyncSession) -> Gig:
    result = await db.execute(select(Gig).where(Gig.id == gig_id))
    gig = result.scalar_one_or_none()
    if not gig:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gig not found.")
    if gig.student_id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not own this gig.")
    return gig

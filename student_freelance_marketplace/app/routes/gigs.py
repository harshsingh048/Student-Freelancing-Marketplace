"""
routes/gigs.py
───────────────
GET    /gigs                – Public gig listing with filters
GET    /gigs/my             – Student's own gigs
GET    /gigs/{gig_id}       – Single gig detail
POST   /gigs                – Create gig (student only)
PUT    /gigs/{gig_id}       – Update gig (owner only)
POST   /gigs/{gig_id}/thumbnail – Upload thumbnail
DELETE /gigs/{gig_id}       – Soft-delete gig (owner only)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers import gig_controller
from app.controllers.schemas import GigCreateRequest, GigUpdateRequest
from app.middleware.auth import get_current_user, require_student
from app.models.gig  import GigCategory
from app.models.user import User
from app.utils.responses import paginated_response, success_response

router = APIRouter(prefix="/gigs", tags=["Gigs"])


@router.get("", summary="List gigs with optional filters")
async def list_gigs(
    page:      int                   = Query(1, ge=1),
    page_size: int                   = Query(10, ge=1, le=50),
    category:  Optional[GigCategory] = Query(None),
    min_price: Optional[float]       = Query(None, ge=0),
    max_price: Optional[float]       = Query(None, ge=0),
    search:    Optional[str]         = Query(None),
    db: AsyncSession                 = Depends(get_db),
):
    result = await gig_controller.list_gigs(
        page, page_size, category, min_price, max_price, search, db
    )
    return paginated_response(result["items"], result["total"], page, page_size)


@router.get("/my", summary="Get all gigs created by the current student")
async def my_gigs(
    student: User          = Depends(require_student),
    db:      AsyncSession  = Depends(get_db),
):
    gigs = await gig_controller.list_my_gigs(student, db)
    return success_response(gigs)


@router.get("/{gig_id}", summary="Get a single gig by ID")
async def get_gig(gig_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await gig_controller.get_gig(gig_id, db)
    return success_response(data)


@router.post("", status_code=201, summary="Create a new gig (student only)")
async def create_gig(
    payload:  GigCreateRequest,
    student:  User          = Depends(require_student),
    db:       AsyncSession  = Depends(get_db),
):
    data = await gig_controller.create_gig(payload, student, db)
    return success_response(data, "Gig created.", 201)


@router.put("/{gig_id}", summary="Update a gig (owner only)")
async def update_gig(
    gig_id:  UUID,
    payload: GigUpdateRequest,
    student: User          = Depends(require_student),
    db:      AsyncSession  = Depends(get_db),
):
    data = await gig_controller.update_gig(gig_id, payload, student, db)
    return success_response(data, "Gig updated.")


@router.post("/{gig_id}/thumbnail", summary="Upload a thumbnail image for a gig")
async def upload_thumbnail(
    gig_id:  UUID,
    file:    UploadFile  = File(...),
    student: User        = Depends(require_student),
    db:      AsyncSession = Depends(get_db),
):
    data = await gig_controller.upload_gig_thumbnail(gig_id, file, student, db)
    return success_response(data, "Thumbnail uploaded.")


@router.delete("/{gig_id}", summary="Deactivate (soft-delete) a gig")
async def delete_gig(
    gig_id:  UUID,
    student: User         = Depends(require_student),
    db:      AsyncSession = Depends(get_db),
):
    data = await gig_controller.delete_gig(gig_id, student, db)
    return success_response(data)

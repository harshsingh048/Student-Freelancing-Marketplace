"""
routes/reviews.py
──────────────────
POST /reviews                          – Submit a review (client only)
GET  /reviews/student/{student_id}     – Get reviews for a student
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers import review_controller
from app.controllers.schemas import ReviewCreateRequest
from app.middleware.auth import require_client
from app.models.user import User
from app.utils.responses import paginated_response, success_response

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", status_code=201, summary="Submit a review for a completed order")
async def create_review(
    payload: ReviewCreateRequest,
    client:  User          = Depends(require_client),
    db:      AsyncSession  = Depends(get_db),
):
    data = await review_controller.create_review(payload, client, db)
    return success_response(data, "Review submitted.", 201)


@router.get("/student/{student_id}", summary="Get all reviews for a student")
async def student_reviews(
    student_id: UUID,
    page:       int  = Query(1, ge=1),
    page_size:  int  = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await review_controller.get_student_reviews(student_id, page, page_size, db)
    return paginated_response(result["items"], result["total"], page, page_size)

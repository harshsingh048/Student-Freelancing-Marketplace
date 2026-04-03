"""
controllers/review_controller.py
─────────────────────────────────
Clients can review a student once per completed order.
After every new review the student's average_rating is recomputed.
"""

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order  import Order, OrderStatus
from app.models.review import Review
from app.models.user   import User
from app.controllers.schemas import ReviewCreateRequest, ReviewOut


async def create_review(
    payload: ReviewCreateRequest,
    client: User,
    db: AsyncSession,
) -> dict:
    """
    Client submits a review for a completed order.
    One review per order is enforced at DB level (unique constraint on order_id).
    """
    # 1. Fetch the order
    result = await db.execute(select(Order).where(Order.id == payload.order_id))
    order: Order | None = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")

    # 2. Only the ordering client may review
    if order.client_id != client.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You did not place this order.")

    # 3. Order must be completed
    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You can only review a COMPLETED order.",
        )

    # 4. Check duplicate review
    existing = await db.execute(select(Review).where(Review.order_id == payload.order_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already reviewed this order.")

    # 5. Create review
    review = Review(
        order_id=payload.order_id,
        client_id=client.id,
        student_id=order.student_id,
        gig_id=order.gig_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    await db.flush()

    # 6. Recompute student's average rating
    await _recalculate_rating(order.student_id, db)

    return ReviewOut.model_validate(review).model_dump(mode="json")


async def get_student_reviews(
    student_id: UUID,
    page: int,
    page_size: int,
    db: AsyncSession,
) -> dict:
    """Return paginated reviews for a student."""
    query = select(Review).where(Review.student_id == student_id)
    total = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(Review.created_at.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
    )
    reviews = result.scalars().all()

    return {
        "items": [ReviewOut.model_validate(r).model_dump(mode="json") for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── Private helpers ────────────────────────────────────────────────────────────
async def _recalculate_rating(student_id: UUID, db: AsyncSession) -> None:
    """
    Recompute and persist the student's average_rating and total_reviews
    based on ALL reviews in the database.
    """
    agg = await db.execute(
        select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("count"),
        ).where(Review.student_id == student_id)
    )
    row = agg.one()
    avg   = float(row.avg_rating or 0.0)
    count = int(row.count or 0)

    student_result = await db.execute(select(User).where(User.id == student_id))
    student = student_result.scalar_one_or_none()
    if student:
        student.average_rating = round(avg, 2)
        student.total_reviews  = count
        db.add(student)

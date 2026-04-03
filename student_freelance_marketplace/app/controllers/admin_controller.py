"""
controllers/admin_controller.py
────────────────────────────────
Admin-only operations:
  • List / search users
  • Ban / unban users
  • View all orders (with filters)
  • Resolve disputed orders (release or refund)
"""

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.user  import User, UserRole
from app.controllers.schemas import BanUserRequest, OrderOut, UserOut
from app.utils.payment import refund_payment, release_payment


# ── Users ─────────────────────────────────────────────────────────────────────
async def list_users(
    page: int,
    page_size: int,
    role: UserRole | None,
    search: str | None,
    db: AsyncSession,
) -> dict:
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if search:
        query = query.where(
            User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(User.created_at.desc())
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


async def get_user(user_id: UUID, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    return UserOut.model_validate(user).model_dump(mode="json")


async def ban_user(
    user_id: UUID,
    payload: BanUserRequest,
    db: AsyncSession,
) -> dict:
    """Ban a user. Admins cannot ban other admins."""
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot ban another admin.")

    user.is_banned = True
    user.is_active = False
    db.add(user)
    return {"message": f"User {user.email} has been banned.", "reason": payload.reason}


async def unban_user(user_id: UUID, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    user.is_banned = False
    user.is_active = True
    db.add(user)
    return {"message": f"User {user.email} has been unbanned."}


# ── Orders ────────────────────────────────────────────────────────────────────
async def list_all_orders(
    page: int,
    page_size: int,
    order_status: OrderStatus | None,
    db: AsyncSession,
) -> dict:
    query = select(Order)
    if order_status:
        query = query.where(Order.status == order_status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(Order.created_at.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
    )
    orders = result.scalars().all()

    return {
        "items": [OrderOut.model_validate(o).model_dump(mode="json") for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def resolve_dispute(
    order_id: UUID,
    decision: str,           # "release" → pay student  |  "refund" → pay client
    db: AsyncSession,
) -> dict:
    """
    Admin resolves a DISPUTED order.
    decision='release' → mark complete, transfer to student.
    decision='refund'  → cancel order, refund client.
    """
    if decision not in ("release", "refund"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "decision must be 'release' or 'refund'.")

    result = await db.execute(select(Order).where(Order.id == order_id))
    order: Order | None = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    if order.status != OrderStatus.DISPUTED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order is not in DISPUTED state.")

    if decision == "release":
        release_payment(order.razorpay_payment_id or "mock")
        order.status         = OrderStatus.COMPLETED
        order.payment_status = PaymentStatus.RELEASED
        msg = "Dispute resolved: payment released to student."
    else:
        refund_payment(order.razorpay_payment_id or "mock", float(order.amount))
        order.status         = OrderStatus.CANCELLED
        order.payment_status = PaymentStatus.REFUNDED
        msg = "Dispute resolved: client refunded."

    db.add(order)
    return {"message": msg}


# ── Dashboard stats ───────────────────────────────────────────────────────────
async def get_stats(db: AsyncSession) -> dict:
    """Quick admin dashboard numbers."""
    total_users    = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_students = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.STUDENT))).scalar_one()
    total_clients  = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.CLIENT))).scalar_one()
    total_orders   = (await db.execute(select(func.count(Order.id)))).scalar_one()
    completed      = (await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.COMPLETED))).scalar_one()
    disputed       = (await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.DISPUTED))).scalar_one()

    revenue_result = await db.execute(
        select(func.sum(Order.platform_fee)).where(Order.payment_status == PaymentStatus.RELEASED)
    )
    total_revenue = float(revenue_result.scalar_one() or 0.0)

    return {
        "users": {
            "total": total_users,
            "students": total_students,
            "clients": total_clients,
        },
        "orders": {
            "total": total_orders,
            "completed": completed,
            "disputed": disputed,
        },
        "platform_revenue": total_revenue,
    }

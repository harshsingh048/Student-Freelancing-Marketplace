"""
controllers/order_controller.py
────────────────────────────────
Full order lifecycle:
  1.  Client creates order          → status=PENDING,    payment=UNPAID
  2.  Client pays (mock Razorpay)   → status=IN_PROGRESS, payment=HELD  (escrow)
  3.  Student delivers              → status=DELIVERED
  4a. Client approves               → status=COMPLETED,  payment=RELEASED
  4b. Client disputes               → status=DISPUTED
  5.  Admin resolves dispute (via admin controller)
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.gig   import Gig
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.user  import User, UserRole
from app.controllers.schemas import (
    OrderCreateRequest, OrderDeliverRequest,
    OrderOut, PaymentVerifyRequest,
)
from app.utils.payment import (
    calculate_fees, create_order as payment_create_order,
    verify_payment, release_payment, refund_payment,
)


# ── 1. Place order ─────────────────────────────────────────────────────────────
async def place_order(
    payload: OrderCreateRequest,
    client: User,
    db: AsyncSession,
) -> dict:
    """Client places an order for a gig. Returns order + Razorpay order details."""
    # Fetch the gig
    result = await db.execute(select(Gig).where(Gig.id == payload.gig_id, Gig.is_active.is_(True)))
    gig: Gig | None = result.scalar_one_or_none()
    if not gig:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gig not found or inactive.")

    # Client cannot order their own gig (edge case)
    if gig.student_id == client.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot order your own gig.")

    # Calculate fees
    platform_fee, student_earnings = calculate_fees(float(gig.price))

    # Create mock Razorpay order (escrow initiation)
    payment_order = payment_create_order(
        amount_rupees=float(gig.price),
        receipt=f"order_{client.id}",
    )

    # Compute expected delivery date
    expected = datetime.now(timezone.utc) + timedelta(days=gig.delivery_days)

    order = Order(
        gig_id=gig.id,
        client_id=client.id,
        student_id=gig.student_id,
        amount=float(gig.price),
        platform_fee=platform_fee,
        student_earnings=student_earnings,
        requirements=payload.requirements,
        razorpay_order_id=payment_order.razorpay_order_id,
        expected_delivery=expected,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.UNPAID,
    )
    db.add(order)
    await db.flush()

    return {
        "order": OrderOut.model_validate(order).model_dump(mode="json"),
        "payment_details": {
            "razorpay_order_id": payment_order.razorpay_order_id,
            "amount_paise":      payment_order.amount_paise,
            "currency":          payment_order.currency,
            "key_id":            "rzp_test_mock_key",   # expose public key to frontend
        },
    }


# ── 2. Verify payment & move to IN_PROGRESS (escrow held) ─────────────────────
async def verify_order_payment(
    payload: PaymentVerifyRequest,
    client: User,
    db: AsyncSession,
) -> dict:
    """
    Verify Razorpay payment signature.
    On success: payment status → HELD (escrow), order status → IN_PROGRESS.
    """
    order = await _get_order_for_client(payload.order_id, client.id, db)

    if order.status != OrderStatus.PENDING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order is not in PENDING state.")

    result = verify_payment(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
    if not result.success:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, f"Payment verification failed: {result.message}")

    order.razorpay_payment_id = payload.razorpay_payment_id
    order.razorpay_signature  = payload.razorpay_signature
    order.payment_status      = PaymentStatus.HELD
    order.status              = OrderStatus.IN_PROGRESS
    db.add(order)

    return {"message": "Payment verified. Order is now in progress.", "order_id": str(order.id)}


# ── 3. Student delivers work ───────────────────────────────────────────────────
async def deliver_order(
    order_id: UUID,
    payload: OrderDeliverRequest,
    student: User,
    db: AsyncSession,
) -> dict:
    """Student marks an order as delivered."""
    order = await _get_order_for_student(order_id, student.id, db)

    if order.status != OrderStatus.IN_PROGRESS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order must be IN_PROGRESS to deliver.")

    order.delivery_note = payload.delivery_note
    order.status        = OrderStatus.DELIVERED
    db.add(order)

    return {"message": "Order marked as delivered. Awaiting client approval."}


# ── 4a. Client approves delivery ──────────────────────────────────────────────
async def approve_delivery(
    order_id: UUID,
    client: User,
    db: AsyncSession,
) -> dict:
    """
    Client approves the delivery.
    Payment released from escrow → student_earnings transferred.
    """
    order = await _get_order_for_client(order_id, client.id, db)

    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order must be DELIVERED to approve.")

    # Release escrow
    release_payment(order.razorpay_payment_id or "mock_payment")

    order.status         = OrderStatus.COMPLETED
    order.payment_status = PaymentStatus.RELEASED
    order.completed_at   = datetime.now(timezone.utc)
    db.add(order)

    return {"message": "Order completed. Payment released to student."}


# ── 4b. Client raises dispute ─────────────────────────────────────────────────
async def dispute_order(
    order_id: UUID,
    client: User,
    db: AsyncSession,
) -> dict:
    """Client raises a dispute. Admin must resolve it."""
    order = await _get_order_for_client(order_id, client.id, db)

    if order.status not in (OrderStatus.IN_PROGRESS, OrderStatus.DELIVERED):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot dispute this order in its current state.")

    order.status = OrderStatus.DISPUTED
    db.add(order)

    return {"message": "Dispute raised. Admin will review the order."}


# ── Client cancel (only when PENDING) ────────────────────────────────────────
async def cancel_order(
    order_id: UUID,
    client: User,
    db: AsyncSession,
) -> dict:
    """Client cancels a pending (unpaid) order."""
    order = await _get_order_for_client(order_id, client.id, db)

    if order.status != OrderStatus.PENDING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PENDING orders can be cancelled.")

    order.status = OrderStatus.CANCELLED
    db.add(order)
    return {"message": "Order cancelled."}


# ── Fetch helpers (client or student) ────────────────────────────────────────
async def get_my_orders_as_client(client: User, db: AsyncSession) -> list:
    result = await db.execute(
        select(Order).where(Order.client_id == client.id).order_by(Order.created_at.desc())
    )
    return [OrderOut.model_validate(o).model_dump(mode="json") for o in result.scalars().all()]


async def get_my_orders_as_student(student: User, db: AsyncSession) -> list:
    result = await db.execute(
        select(Order).where(Order.student_id == student.id).order_by(Order.created_at.desc())
    )
    return [OrderOut.model_validate(o).model_dump(mode="json") for o in result.scalars().all()]


async def get_order_detail(order_id: UUID, current_user: User, db: AsyncSession) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order: Order | None = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    if order.client_id != current_user.id and order.student_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    return OrderOut.model_validate(order).model_dump(mode="json")


# ── Private helpers ───────────────────────────────────────────────────────────
async def _get_order_for_client(order_id: UUID, client_id: UUID, db: AsyncSession) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    if order.client_id != client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    return order


async def _get_order_for_student(order_id: UUID, student_id: UUID, db: AsyncSession) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    if order.student_id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    return order

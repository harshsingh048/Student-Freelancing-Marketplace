"""
routes/orders.py
─────────────────
POST   /orders                       – Place order (client)
POST   /orders/verify-payment        – Confirm payment (client)
GET    /orders/my/client             – My orders as client
GET    /orders/my/student            – My orders as student
GET    /orders/{order_id}            – Order detail
POST   /orders/{order_id}/deliver    – Mark delivered (student)
POST   /orders/{order_id}/approve    – Approve delivery (client)
POST   /orders/{order_id}/dispute    – Raise dispute (client)
POST   /orders/{order_id}/cancel     – Cancel pending order (client)
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers import order_controller
from app.controllers.schemas import (
    OrderCreateRequest, OrderDeliverRequest, PaymentVerifyRequest,
)
from app.middleware.auth import get_current_user, require_client, require_student
from app.models.user import User
from app.utils.responses import success_response

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=201, summary="Place an order for a gig")
async def place_order(
    payload: OrderCreateRequest,
    client:  User          = Depends(require_client),
    db:      AsyncSession  = Depends(get_db),
):
    data = await order_controller.place_order(payload, client, db)
    return success_response(data, "Order placed. Proceed to payment.", 201)


@router.post("/verify-payment", summary="Verify Razorpay payment and activate order")
async def verify_payment(
    payload: PaymentVerifyRequest,
    client:  User          = Depends(require_client),
    db:      AsyncSession  = Depends(get_db),
):
    data = await order_controller.verify_order_payment(payload, client, db)
    return success_response(data)


@router.get("/my/client", summary="Get all orders placed by me (as client)")
async def my_orders_client(
    client: User         = Depends(require_client),
    db:     AsyncSession = Depends(get_db),
):
    data = await order_controller.get_my_orders_as_client(client, db)
    return success_response(data)


@router.get("/my/student", summary="Get all orders assigned to me (as student)")
async def my_orders_student(
    student: User        = Depends(require_student),
    db:      AsyncSession = Depends(get_db),
):
    data = await order_controller.get_my_orders_as_student(student, db)
    return success_response(data)


@router.get("/{order_id}", summary="Get order details (accessible by both parties)")
async def get_order(
    order_id:     UUID,
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    data = await order_controller.get_order_detail(order_id, current_user, db)
    return success_response(data)


@router.post("/{order_id}/deliver", summary="Student: mark order as delivered")
async def deliver(
    order_id: UUID,
    payload:  OrderDeliverRequest,
    student:  User          = Depends(require_student),
    db:       AsyncSession  = Depends(get_db),
):
    data = await order_controller.deliver_order(order_id, payload, student, db)
    return success_response(data)


@router.post("/{order_id}/approve", summary="Client: approve delivery and release payment")
async def approve(
    order_id: UUID,
    client:   User         = Depends(require_client),
    db:       AsyncSession = Depends(get_db),
):
    data = await order_controller.approve_delivery(order_id, client, db)
    return success_response(data)


@router.post("/{order_id}/dispute", summary="Client: raise a dispute")
async def dispute(
    order_id: UUID,
    client:   User         = Depends(require_client),
    db:       AsyncSession = Depends(get_db),
):
    data = await order_controller.dispute_order(order_id, client, db)
    return success_response(data)


@router.post("/{order_id}/cancel", summary="Client: cancel a pending order")
async def cancel(
    order_id: UUID,
    client:   User         = Depends(require_client),
    db:       AsyncSession = Depends(get_db),
):
    data = await order_controller.cancel_order(order_id, client, db)
    return success_response(data)

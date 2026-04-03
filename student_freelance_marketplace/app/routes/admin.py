"""
routes/admin.py
────────────────
All routes require admin role.

GET    /admin/stats
GET    /admin/users
GET    /admin/users/{user_id}
POST   /admin/users/{user_id}/ban
POST   /admin/users/{user_id}/unban
GET    /admin/orders
POST   /admin/orders/{order_id}/resolve-dispute
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers import admin_controller
from app.controllers.schemas import BanUserRequest
from app.middleware.auth import require_admin
from app.models.order import OrderStatus
from app.models.user  import User, UserRole
from app.utils.responses import paginated_response, success_response

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", summary="Platform-wide dashboard statistics")
async def stats(
    _admin: User         = Depends(require_admin),
    db:     AsyncSession = Depends(get_db),
):
    data = await admin_controller.get_stats(db)
    return success_response(data)


@router.get("/users", summary="List all users (filterable by role / search)")
async def list_users(
    page:      int                  = Query(1, ge=1),
    page_size: int                  = Query(20, ge=1, le=100),
    role:      Optional[UserRole]   = Query(None),
    search:    Optional[str]        = Query(None),
    _admin:    User                 = Depends(require_admin),
    db:        AsyncSession         = Depends(get_db),
):
    result = await admin_controller.list_users(page, page_size, role, search, db)
    return paginated_response(result["items"], result["total"], page, page_size)


@router.get("/users/{user_id}", summary="Get a specific user's full details")
async def get_user(
    user_id: UUID,
    _admin:  User         = Depends(require_admin),
    db:      AsyncSession = Depends(get_db),
):
    data = await admin_controller.get_user(user_id, db)
    return success_response(data)


@router.post("/users/{user_id}/ban", summary="Ban a user")
async def ban_user(
    user_id: UUID,
    payload: BanUserRequest,
    _admin:  User         = Depends(require_admin),
    db:      AsyncSession = Depends(get_db),
):
    data = await admin_controller.ban_user(user_id, payload, db)
    return success_response(data)


@router.post("/users/{user_id}/unban", summary="Unban a user")
async def unban_user(
    user_id: UUID,
    _admin:  User         = Depends(require_admin),
    db:      AsyncSession = Depends(get_db),
):
    data = await admin_controller.unban_user(user_id, db)
    return success_response(data)


@router.get("/orders", summary="View all orders with optional status filter")
async def list_orders(
    page:         int                    = Query(1, ge=1),
    page_size:    int                    = Query(20, ge=1, le=100),
    order_status: Optional[OrderStatus]  = Query(None),
    _admin:       User                   = Depends(require_admin),
    db:           AsyncSession           = Depends(get_db),
):
    result = await admin_controller.list_all_orders(page, page_size, order_status, db)
    return paginated_response(result["items"], result["total"], page, page_size)


@router.post("/orders/{order_id}/resolve-dispute", summary="Resolve a disputed order")
async def resolve_dispute(
    order_id: UUID,
    decision: str,    # 'release' or 'refund'  (passed as query param for simplicity)
    _admin:   User         = Depends(require_admin),
    db:       AsyncSession = Depends(get_db),
):
    data = await admin_controller.resolve_dispute(order_id, decision, db)
    return success_response(data)

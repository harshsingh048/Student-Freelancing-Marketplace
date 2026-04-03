"""
routes/messages.py
───────────────────
POST /messages                        – Send a message
POST /messages/with-attachment        – Send message with file
GET  /messages/inbox                  – Conversation list (latest per contact)
GET  /messages/{other_user_id}        – Full conversation thread
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers import message_controller
from app.controllers.schemas import MessageSendRequest
from app.middleware.auth import get_current_user
from app.models.user import User
from app.utils.responses import paginated_response, success_response

router = APIRouter(prefix="/messages", tags=["Chat / Messages"])


@router.post("", status_code=201, summary="Send a direct message")
async def send_message(
    payload:      MessageSendRequest,
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    data = await message_controller.send_message(payload, current_user, db)
    return success_response(data, "Message sent.", 201)


@router.post("/with-attachment", status_code=201, summary="Send a message with a file attachment")
async def send_with_attachment(
    receiver_id:  UUID       = Form(...),
    content:      str        = Form(..., min_length=1, max_length=2000),
    file:         UploadFile = File(...),
    current_user: User       = Depends(get_current_user),
    db: AsyncSession         = Depends(get_db),
):
    data = await message_controller.send_message_with_attachment(
        receiver_id, content, file, current_user, db
    )
    return success_response(data, "Message with attachment sent.", 201)


@router.get("/inbox", summary="Get recent conversations (one entry per contact)")
async def inbox(
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    data = await message_controller.get_inbox(current_user, db)
    return success_response(data)


@router.get("/{other_user_id}", summary="Get full conversation with a specific user")
async def conversation(
    other_user_id: UUID,
    page:          int  = Query(1, ge=1),
    page_size:     int  = Query(20, ge=1, le=100),
    current_user:  User         = Depends(get_current_user),
    db:            AsyncSession = Depends(get_db),
):
    result = await message_controller.get_conversation(
        other_user_id, current_user, page, page_size, db
    )
    return paginated_response(result["items"], result["total"], page, page_size)

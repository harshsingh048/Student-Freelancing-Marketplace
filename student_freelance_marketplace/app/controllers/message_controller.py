"""
controllers/message_controller.py
──────────────────────────────────
Simple direct-message (chat) between any two authenticated users.
"""

from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.user    import User
from app.controllers.schemas import MessageOut, MessageSendRequest
from app.utils.file_upload import save_upload_file


async def send_message(
    payload: MessageSendRequest,
    sender: User,
    db: AsyncSession,
) -> dict:
    """Send a text message to another user."""
    if payload.receiver_id == sender.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot message yourself.")

    # Check receiver exists
    result = await db.execute(select(User).where(User.id == payload.receiver_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receiver not found.")

    msg = Message(
        sender_id=sender.id,
        receiver_id=payload.receiver_id,
        content=payload.content,
    )
    db.add(msg)
    await db.flush()
    return MessageOut.model_validate(msg).model_dump(mode="json")


async def send_message_with_attachment(
    receiver_id: UUID,
    content: str,
    file: UploadFile,
    sender: User,
    db: AsyncSession,
) -> dict:
    """Send a message with a file attachment."""
    if receiver_id == sender.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot message yourself.")

    url = await save_upload_file(file, sub_dir="chat_attachments")

    msg = Message(
        sender_id=sender.id,
        receiver_id=receiver_id,
        content=content,
        attachment_url=url,
    )
    db.add(msg)
    await db.flush()
    return MessageOut.model_validate(msg).model_dump(mode="json")


async def get_conversation(
    other_user_id: UUID,
    current_user: User,
    page: int,
    page_size: int,
    db: AsyncSession,
) -> dict:
    """
    Fetch all messages exchanged between the current user and another user,
    sorted oldest-first.  Also marks unread messages as read.
    """
    me = current_user.id

    base_filter = or_(
        and_(Message.sender_id == me,           Message.receiver_id == other_user_id),
        and_(Message.sender_id == other_user_id, Message.receiver_id == me),
    )

    total = (await db.execute(select(func.count()).where(base_filter))).scalar_one()

    result = await db.execute(
        select(Message)
        .where(base_filter)
        .order_by(Message.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()

    # Mark incoming unread messages as read
    for msg in messages:
        if msg.receiver_id == me and not msg.is_read:
            msg.is_read = True
            db.add(msg)

    return {
        "items": [MessageOut.model_validate(m).model_dump(mode="json") for m in messages],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_inbox(current_user: User, db: AsyncSession) -> list:
    """
    Return a list of recent conversations (one entry per unique contact),
    showing the latest message in each thread.
    """
    me = current_user.id

    # Subquery: latest message timestamp per (sender, receiver) pair
    # This is a simplified approach — production would use a window function
    result = await db.execute(
        select(Message)
        .where(or_(Message.sender_id == me, Message.receiver_id == me))
        .order_by(Message.created_at.desc())
        .limit(100)   # cap to avoid full-table scans on large datasets
    )
    all_msgs = result.scalars().all()

    # Deduplicate by contact
    seen: set[UUID] = set()
    threads: list[dict] = []
    for msg in all_msgs:
        contact_id = msg.receiver_id if msg.sender_id == me else msg.sender_id
        if contact_id not in seen:
            seen.add(contact_id)
            threads.append(MessageOut.model_validate(msg).model_dump(mode="json"))

    return threads

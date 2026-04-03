"""
controllers/schemas.py
───────────────────────
All Pydantic v2 request/response schemas.
Kept in one file for discoverability; split per domain as project grows.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.gig   import GigCategory
from app.models.order import OrderStatus, PaymentStatus
from app.models.user  import UserRole


# ════════════════════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════════════════════

class StudentSignupRequest(BaseModel):
    full_name: str   = Field(..., min_length=2, max_length=150)
    email:     EmailStr
    password:  str   = Field(..., min_length=8, max_length=72)
    skills:    List[str] = Field(default_factory=list)
    bio:       Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class ClientSignupRequest(BaseModel):
    full_name: str  = Field(..., min_length=2, max_length=150)
    email:     EmailStr
    password:  str  = Field(..., min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


# ════════════════════════════════════════════════════════════════════════════
#  USER / PROFILE
# ════════════════════════════════════════════════════════════════════════════

class PortfolioItem(BaseModel):
    title:     str
    url:       str
    image_url: Optional[str] = None


class UserOut(BaseModel):
    id:             uuid.UUID
    email:          str
    full_name:      str
    role:           UserRole
    avatar_url:     Optional[str]
    bio:            Optional[str]
    skills:         Optional[List[str]]
    portfolio_links: Optional[List[Any]]
    average_rating: float
    total_reviews:  int
    is_active:      bool
    is_banned:      bool
    created_at:     datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name:       Optional[str]            = Field(None, min_length=2, max_length=150)
    bio:             Optional[str]            = None
    skills:          Optional[List[str]]      = None
    portfolio_links: Optional[List[PortfolioItem]] = None
    phone:           Optional[str]            = None


# ════════════════════════════════════════════════════════════════════════════
#  GIG
# ════════════════════════════════════════════════════════════════════════════

class GigCreateRequest(BaseModel):
    title:          str           = Field(..., min_length=10, max_length=200)
    description:    str           = Field(..., min_length=30)
    category:       GigCategory
    price:          float         = Field(..., gt=0, le=100_000)
    delivery_days:  int           = Field(..., ge=1, le=365)
    revision_count: int           = Field(1, ge=0, le=10)


class GigUpdateRequest(BaseModel):
    title:          Optional[str]         = Field(None, min_length=10, max_length=200)
    description:    Optional[str]         = Field(None, min_length=30)
    category:       Optional[GigCategory] = None
    price:          Optional[float]       = Field(None, gt=0, le=100_000)
    delivery_days:  Optional[int]         = Field(None, ge=1, le=365)
    revision_count: Optional[int]         = Field(None, ge=0, le=10)
    is_active:      Optional[bool]        = None


class GigOut(BaseModel):
    id:             uuid.UUID
    student_id:     uuid.UUID
    title:          str
    description:    str
    category:       GigCategory
    price:          float
    delivery_days:  int
    revision_count: int
    thumbnail_url:  Optional[str]
    is_active:      bool
    created_at:     datetime
    student:        Optional[UserOut] = None

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════════════════════
#  ORDER
# ════════════════════════════════════════════════════════════════════════════

class OrderCreateRequest(BaseModel):
    gig_id:       uuid.UUID
    requirements: Optional[str] = Field(None, max_length=2000)


class PaymentVerifyRequest(BaseModel):
    order_id:            uuid.UUID
    razorpay_order_id:   str
    razorpay_payment_id: str
    razorpay_signature:  str


class OrderDeliverRequest(BaseModel):
    delivery_note: str = Field(..., min_length=10)


class OrderOut(BaseModel):
    id:                  uuid.UUID
    gig_id:              Optional[uuid.UUID]
    client_id:           uuid.UUID
    student_id:          uuid.UUID
    amount:              float
    platform_fee:        float
    student_earnings:    float
    status:              OrderStatus
    payment_status:      PaymentStatus
    razorpay_order_id:   Optional[str]
    requirements:        Optional[str]
    delivery_note:       Optional[str]
    expected_delivery:   Optional[datetime]
    created_at:          datetime
    completed_at:        Optional[datetime]

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════════════════════
#  REVIEW
# ════════════════════════════════════════════════════════════════════════════

class ReviewCreateRequest(BaseModel):
    order_id: uuid.UUID
    rating:   int     = Field(..., ge=1, le=5)
    comment:  Optional[str] = Field(None, max_length=1000)


class ReviewOut(BaseModel):
    id:         uuid.UUID
    order_id:   uuid.UUID
    client_id:  uuid.UUID
    student_id: uuid.UUID
    gig_id:     Optional[uuid.UUID]
    rating:     int
    comment:    Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════════════════════
#  MESSAGE / CHAT
# ════════════════════════════════════════════════════════════════════════════

class MessageSendRequest(BaseModel):
    receiver_id: uuid.UUID
    content:     str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id:             uuid.UUID
    sender_id:      uuid.UUID
    receiver_id:    uuid.UUID
    content:        str
    attachment_url: Optional[str]
    is_read:        bool
    created_at:     datetime

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ════════════════════════════════════════════════════════════════════════════

class BanUserRequest(BaseModel):
    reason: Optional[str] = None

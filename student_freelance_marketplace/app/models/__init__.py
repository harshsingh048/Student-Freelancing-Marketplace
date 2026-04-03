"""models/__init__.py – expose all models for Alembic auto-detection."""
from app.models.user    import User, UserRole
from app.models.gig     import Gig, GigCategory
from app.models.order   import Order, OrderStatus, PaymentStatus
from app.models.review  import Review
from app.models.message import Message

__all__ = [
    "User", "UserRole",
    "Gig", "GigCategory",
    "Order", "OrderStatus", "PaymentStatus",
    "Review",
    "Message",
]

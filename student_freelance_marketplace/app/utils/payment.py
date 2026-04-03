"""
utils/payment.py
─────────────────
Mock Razorpay payment gateway simulation.

In production replace the mock_ functions with actual Razorpay SDK calls:
    import razorpay
    client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

Escrow flow:
    1. Client initiates payment  → create_order()   → status HELD
    2. Student delivers work     → (order status update in controller)
    3. Client approves           → release_payment() → status RELEASED
    4. Client disputes / cancels → refund_payment()  → status REFUNDED
"""

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from typing import Optional

from app.config.settings import settings


@dataclass
class PaymentOrder:
    razorpay_order_id: str
    amount_paise: int          # Razorpay uses smallest currency unit (paise = 1/100 rupee)
    currency: str
    receipt: str


@dataclass
class PaymentVerification:
    success: bool
    payment_id: Optional[str] = None
    message: str = ""


def create_order(amount_rupees: float, receipt: str) -> PaymentOrder:
    """
    Simulate Razorpay order creation.
    In production: client.order.create(data={...})
    """
    mock_order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
    return PaymentOrder(
        razorpay_order_id=mock_order_id,
        amount_paise=int(amount_rupees * 100),
        currency="INR",
        receipt=receipt,
    )


def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> PaymentVerification:
    """
    Verify Razorpay webhook signature.
    Real implementation uses HMAC-SHA256 over 'order_id|payment_id'.
    For mocks we accept any payment_id that starts with 'pay_mock_'.
    """
    # ── Production signature check ──────────────────────────────────────────
    expected_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    # In mock mode accept the special prefix OR valid HMAC
    if razorpay_payment_id.startswith("pay_mock_") or hmac.compare_digest(
        expected_sig, razorpay_signature
    ):
        return PaymentVerification(success=True, payment_id=razorpay_payment_id)

    return PaymentVerification(success=False, message="Signature mismatch – payment invalid")


def release_payment(payment_id: str) -> bool:
    """
    Simulate releasing escrowed funds to student.
    Production: trigger payout via Razorpay Transfers API.
    """
    # Mock: always succeeds
    return True


def refund_payment(payment_id: str, amount_rupees: float) -> bool:
    """
    Simulate refunding client.
    Production: client.payment.refund(payment_id, {'amount': int(amount*100)})
    """
    # Mock: always succeeds
    return True


def calculate_fees(amount: float) -> tuple[float, float]:
    """
    Return (platform_fee, student_earnings) for a given order amount.
    Platform takes PLATFORM_FEE_PERCENT % (default 10 %).
    """
    fee = round(amount * settings.PLATFORM_FEE_PERCENT / 100, 2)
    earnings = round(amount - fee, 2)
    return fee, earnings

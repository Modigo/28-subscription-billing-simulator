"""Payment simulation service."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment_attempt import PaymentAttempt
from app.utils.clock import Clock


class PaymentService:
    """Business logic for simulated payments."""

    @staticmethod
    def simulate_payment(
        db: Session, invoice: Invoice, outcome: str, failure_reason: str | None = None
    ) -> PaymentAttempt:
        """
        Simulate a payment attempt on an invoice.
        Updates invoice status and records the attempt.
        """
        now = Clock.now()
        attempt_number = invoice.attempt_count + 1

        attempt = PaymentAttempt(
            invoice_id=invoice.id,
            attempt_number=attempt_number,
            outcome=outcome,
            failure_reason=failure_reason,
            attempted_at=now,
        )

        if outcome == "success":
            invoice.status = "paid"
            invoice.paid_at = now
            invoice.next_retry_at = None
        else:
            invoice.status = "failed"

        invoice.attempt_count = attempt_number
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def get_payment_attempts(
        db: Session, invoice_id: int
    ) -> list[PaymentAttempt]:
        """Get all payment attempts for an invoice."""
        return (
            db.query(PaymentAttempt)
            .filter(PaymentAttempt.invoice_id == invoice_id)
            .order_by(PaymentAttempt.attempt_number)
            .all()
        )

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import (
    Invoice,
    InvoiceStatus,
    PaymentAttempt,
    Subscription,
    SubStatus,
    DunningLog,
)


# Retry schedule: 3, 7, and 14 days.
RETRY_SCHEDULE = [3, 7, 14]
MAX_RETRIES = len(RETRY_SCHEDULE)


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime.

    This matches the datetime format used by the existing database models.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def process_payment(
    db: Session,
    invoice_id: int,
    succeed: bool,
    now: datetime | None = None,
    message: str | None = None,
) -> PaymentAttempt:
    """Record a simulated payment result without contacting a real provider."""

    now = now or utcnow()

    invoice = db.get(Invoice, invoice_id)

    if invoice is None:
        raise ValueError("Invoice not found.")

    if invoice.status == InvoiceStatus.PAID.value:
        raise ValueError("Invoice is already paid.")

    previous = (
        db.query(PaymentAttempt)
        .filter_by(invoice_id=invoice_id)
        .count()
    )

    attempt_number = previous + 1

    if attempt_number > MAX_RETRIES + 1:
        raise ValueError("Maximum payment attempts reached.")

    status = "succeeded" if succeed else "failed"

    attempt = PaymentAttempt(
        invoice_id=invoice_id,
        attempt_number=attempt_number,
        status=status,
        message=message or (
            "Payment succeeded" if succeed else "Payment failed"
        ),
        attempted_at=now,
    )

    db.add(attempt)

    if succeed:
        invoice.status = InvoiceStatus.PAID.value

        # Reactivate the subscription if it was past due.
        sub = db.get(Subscription, invoice.subscription_id)

        if sub and sub.status == SubStatus.PAST_DUE.value:
            sub.status = SubStatus.ACTIVE.value

    else:
        invoice.status = InvoiceStatus.FAILED.value

        if attempt_number <= MAX_RETRIES:
            next_retry = now + timedelta(
                days=RETRY_SCHEDULE[attempt_number - 1]
            )
        else:
            next_retry = None

            sub = db.get(Subscription, invoice.subscription_id)

            if sub:
                sub.status = SubStatus.PAST_DUE.value

        dunning_log = DunningLog(
            invoice_id=invoice.id,
            attempt_number=attempt_number,
            message=attempt.message,
            next_retry_at=next_retry,
        )

        db.add(dunning_log)

    db.commit()
    db.refresh(attempt)

    return attempt


def process_due_retries(
    db: Session,
    now: datetime | None = None,
) -> list[DunningLog]:
    """Return retry logs that are due for unpaid invoices.

    This function does not execute payments. It only returns retry
    opportunities for the application to display or process.
    """

    now = now or utcnow()

    due_logs = (
        db.query(DunningLog)
        .join(Invoice, DunningLog.invoice_id == Invoice.id)
        .filter(
            DunningLog.next_retry_at.is_not(None),
            DunningLog.next_retry_at <= now,
            Invoice.status != InvoiceStatus.PAID.value,
        )
        .order_by(DunningLog.id)
        .all()
    )

    return due_logs

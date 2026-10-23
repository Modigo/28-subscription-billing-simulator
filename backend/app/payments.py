from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Invoice, InvoiceStatus, PaymentAttempt, Subscription, SubStatus, DunningLog

# Matches the current Member 4 retry-code contract: retries after 3, 7 and 14 days.
RETRY_SCHEDULE = [3, 7, 14]
MAX_RETRIES = len(RETRY_SCHEDULE)

def process_payment(db: Session, invoice_id: int, succeed: bool,
                    now: datetime | None = None, message: str | None = None) -> PaymentAttempt:
    """Record a simulated payment result; no real payment provider is called."""
    now = now or datetime.utcnow()
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found.")
    if invoice.status == InvoiceStatus.PAID.value:
        raise ValueError("Invoice is already paid.")
    previous = db.query(PaymentAttempt).filter_by(invoice_id=invoice_id).count()
    attempt_number = previous + 1
    if attempt_number > MAX_RETRIES + 1:
        raise ValueError("Maximum payment attempts reached.")
    status = "succeeded" if succeed else "failed"
    attempt = PaymentAttempt(invoice_id=invoice_id, attempt_number=attempt_number,
                             status=status, message=message or ("Payment succeeded" if succeed else "Payment failed"),
                             attempted_at=now)
    db.add(attempt)
    if succeed:
        invoice.status = InvoiceStatus.PAID.value
        sub = db.get(Subscription, invoice.subscription_id)
        if sub and sub.status == SubStatus.PAST_DUE.value:
            sub.status = SubStatus.ACTIVE.value
    else:
        invoice.status = InvoiceStatus.FAILED.value
        if attempt_number <= MAX_RETRIES:
            next_retry = now + timedelta(days=RETRY_SCHEDULE[attempt_number - 1])
        else:
            next_retry = None
            sub = db.get(Subscription, invoice.subscription_id)
            if sub:
                sub.status = SubStatus.PAST_DUE.value
        db.add(DunningLog(invoice_id=invoice.id, attempt_number=attempt_number,
                          message=attempt.message, next_retry_at=next_retry))
    db.commit()
    db.refresh(attempt)
    return attempt

def process_due_retries(db: Session, now: datetime | None = None) -> list[PaymentAttempt]:
    """Record due retry attempts as failed by default for deterministic simulation.

    In the MVP dashboard, users can explicitly simulate success/failure using
    process_payment. This worker marks retry opportunities as logs, not real charges.
    """
    now = now or datetime.utcnow()
    due_logs = db.query(DunningLog).filter(
        DunningLog.next_retry_at.is_not(None),
        DunningLog.next_retry_at <= now
    ).order_by(DunningLog.id).all()
    # Return due retry logs so the caller can surface them; avoid fabricating outcomes.
    return due_logs
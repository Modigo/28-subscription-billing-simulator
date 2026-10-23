from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models import Invoice, InvoiceStatus, Subscription


def calculate_invoice_amount(plan_price_kobo: int) -> int:
    if not isinstance(plan_price_kobo, int) or plan_price_kobo < 0:  # type: ignore
        raise ValueError("plan_price_kobo must be a non-negative integer.")
    return plan_price_kobo


def invoice_exists(db: Session, subscription_id: int,
                   billing_period_start: datetime, billing_period_end: datetime) -> bool:
    return db.query(Invoice.id).filter_by(
        subscription_id=subscription_id,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end
    ).first() is not None


def generate_invoice(db: Session, subscription_id: int, plan_price_kobo: int,
                     billing_period_start: datetime, billing_period_end: datetime,
                     issue_date: datetime, due_date: datetime) -> Invoice:
    if billing_period_end <= billing_period_start:
        raise ValueError("Billing period end must be after its start.")
    if due_date < issue_date:
        raise ValueError("Due date cannot be earlier than issue date.")
    subscription = db.get(Subscription, subscription_id)
    if subscription is None:
        raise ValueError("Subscription not found.")
    existing = db.query(Invoice).filter_by(
        subscription_id=subscription_id,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end
    ).first()
    if existing:
        return existing
    invoice = Invoice(
        invoice_number=f"INV-{uuid4().hex[:12].upper()}",
        subscription_id=subscription_id,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        issue_date=issue_date,
        due_date=due_date,
        amount_kobo=calculate_invoice_amount(plan_price_kobo),
        status=InvoiceStatus.PENDING.value
    )
    db.add(invoice)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # If two scheduler workers race, return the row created by the other worker.
        existing = db.query(Invoice).filter_by(
            subscription_id=subscription_id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end
        ).first()
        if existing:
            return existing
        raise
    db.refresh(invoice)
    return invoice


def get_invoice(db: Session, invoice_id: int) -> Invoice | None:
    return db.get(Invoice, invoice_id)


def get_invoices(db: Session, subscription_id: int | None = None) -> list[Invoice]:
    query = db.query(Invoice)
    if subscription_id is not None:
        query = query.filter(Invoice.subscription_id == subscription_id)
    return query.order_by(Invoice.id.desc()).all()


def update_invoice_status(db: Session, invoice_id: int, status: str) -> Invoice:
    allowed = {s.value for s in InvoiceStatus}
    if status not in allowed:
        raise ValueError(f"Invalid invoice status: {status}")
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found.")
    invoice.status = status
    db.commit()
    db.refresh(invoice)
    return invoice

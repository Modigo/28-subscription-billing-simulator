from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Invoice, InvoiceStatus


def calculate_invoice_amount(plan_price_kobo: int) -> int:
    if not isinstance(plan_price_kobo, int) or isinstance(plan_price_kobo, bool) or plan_price_kobo < 0:
        raise ValueError("Plan price must be a non-negative integer.")
    return plan_price_kobo


def invoice_exists(
    db: Session,
    subscription_id: int,
    billing_period_start: datetime,
    billing_period_end: datetime,
) -> bool:
    return (
        db.query(Invoice.id)
        .filter_by(
            subscription_id=subscription_id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
        )
        .first()
        is not None
    )


def generate_invoice(
    db: Session,
    subscription_id: int,
    plan_price_kobo: int,
    billing_period_start: datetime,
    billing_period_end: datetime,
    issue_date: datetime,
    due_date: datetime,
) -> Invoice:
    amount = calculate_invoice_amount(plan_price_kobo)

    existing_invoice = (
        db.query(Invoice)
        .filter_by(
            subscription_id=subscription_id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
        )
        .first()
    )

    if existing_invoice:
        return existing_invoice

    invoice = Invoice(
        invoice_number=f"INV-{uuid4().hex[:12].upper()}",
        subscription_id=subscription_id,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        issue_date=issue_date,
        due_date=due_date,
        amount_kobo=amount,
        status=InvoiceStatus.PENDING.value,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice


def get_invoices(
    db: Session,
    subscription_id: int | None = None,
) -> list[Invoice]:
    query = db.query(Invoice)

    if subscription_id is not None:
        query = query.filter_by(subscription_id=subscription_id)

    return query.order_by(Invoice.id).all()

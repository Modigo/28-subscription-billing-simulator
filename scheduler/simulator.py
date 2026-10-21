from calendar import monthrange
from datetime import date, datetime

from sqlalchemy.orm import Session

from models import Invoice, InvoiceStatus, SubStatus
from dunning import schedule_initial_retry, record_retry_result


def next_month(billing_date):
    """Advance a billing date by one month, preserving its day when possible."""

    year = billing_date.year
    month = billing_date.month + 1

    if month > 12:
        month = 1
        year += 1

    day = min(
        billing_date.day,
        monthrange(year, month)[1],
    )

    return billing_date.replace(
        year=year,
        month=month,
        day=day,
    )


def simulate_billing(
    db: Session,
    subscription,
    payment_success: bool,
):
    """Create an invoice and simulate its initial payment."""

    if subscription.status != SubStatus.ACTIVE:
        return {
            "status": "Skipped",
            "message": "The subscription is not active.",
        }

    if subscription.next_billing_date is None:
        return {
            "status": "Skipped",
            "message": "The subscription has no billing date.",
        }

    if subscription.plan is None:
        raise ValueError("The subscription has no associated plan.")

    invoice = Invoice(
        subscription_id=subscription.id,
        customer_name=subscription.customer_name,
        amount_due=subscription.plan.price,
        retry_count=0,
        status=(
            InvoiceStatus.PAID
            if payment_success
            else InvoiceStatus.FAILED
        ),
        next_retry_date=None,
    )

    try:
        db.add(invoice)
        db.flush()

        if payment_success:
            subscription.next_billing_date = next_month(
                subscription.next_billing_date
            )

            db.commit()
            db.refresh(invoice)

            return {
                "status": "Paid",
                "customer": subscription.customer_name,
                "invoice_id": invoice.id,
                "amount": str(invoice.amount_due),
                "message": "Initial payment successful.",
            }

        # The dunning module records the failure time,
        # schedules the first retry, and commits the invoice.
        result = schedule_initial_retry(db, invoice)

        return {
            "status": "Failed",
            "customer": subscription.customer_name,
            "invoice_id": invoice.id,
            "amount": str(invoice.amount_due),
            "message": "Initial payment failed.",
            "dunning": result,
        }

    except Exception:
        db.rollback()
        raise


def simulate_retry_payment(
    db: Session,
    invoice: Invoice,
    payment_success: bool,
):
    """Simulate a retry payment and record its outcome."""

    return record_retry_result(
        db=db,
        invoice=invoice,
        succeeded=payment_success,
    )
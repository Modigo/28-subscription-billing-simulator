from datetime import date, datetime

from sqlalchemy.orm import Session

from models import (
    Invoice,
    Subscription,
    InvoiceStatus,
    SubStatus,
)
from simulator import simulate_billing


def find_due_subscriptions(
    db: Session,
    today: date,
):
    """Find active subscriptions whose billing dates have arrived."""

    subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.status == SubStatus.ACTIVE,
            Subscription.next_billing_date.isnot(None),
        )
        .all()
    )

    due_subscriptions = []

    for subscription in subscriptions:
        billing_date = subscription.next_billing_date

        if isinstance(billing_date, datetime):
            billing_date = billing_date.date()

        if billing_date > today:
            continue

        existing_invoice = (
            db.query(Invoice)
            .filter(
                Invoice.subscription_id == subscription.id,
                Invoice.status.in_(
                    [
                        InvoiceStatus.FAILED,
                        InvoiceStatus.RETRYING,
                    ]
                ),
            )
            .first()
        )

        if existing_invoice is not None:
            continue

        due_subscriptions.append(subscription)

    return due_subscriptions


def run_scheduler(
    db: Session,
    today: date | None = None,
    payment_outcomes: dict | None = None,
):
    """Process subscriptions due for billing."""

    today = today or date.today()
    payment_outcomes = payment_outcomes or {}

    due_subscriptions = find_due_subscriptions(db, today)

    if not due_subscriptions:
        return {
            "status": "Success",
            "message": "No subscriptions are due for billing.",
            "processed": 0,
            "results": [],
        }

    results = []

    for subscription in due_subscriptions:
        payment_success = payment_outcomes.get(
            subscription.customer_name,
            True,
        )

        result = simulate_billing(
            db=db,
            subscription=subscription,
            payment_success=payment_success,
        )

        results.append(result)

    return {
        "status": "Billing Completed",
        "processed": len(results),
        "results": results,
    }
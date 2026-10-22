from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Subscription, SubStatus
from app.subscriptions import period_end
from app.invoice import generate_invoice

def run_billing_cycle(db: Session, now: datetime | None = None,
                      invoice_due_days: int = 7) -> list:
    """Create one invoice for each active subscription due by `now`.

    A production scheduler should invoke this periodically. Payment processing is
    intentionally separate and can be called by the retry/payment module.
    """
    now = now or datetime.utcnow()
    due = db.query(Subscription).filter(
        Subscription.status == SubStatus.ACTIVE.value,
        Subscription.next_billing_date <= now
    ).order_by(Subscription.id).all()
    created_or_existing = []
    for sub in due:
        start = sub.current_period_start
        end = sub.current_period_end
        invoice = generate_invoice(
            db=db,
            subscription_id=sub.id,
            plan_price_kobo=sub.plan.price_kobo,
            billing_period_start=start,
            billing_period_end=end,
            issue_date=now,
            due_date=now + timedelta(days=invoice_due_days),
        )
        created_or_existing.append(invoice)
        # Move to the next period only once invoice for this period exists.
        sub.current_period_start = end
        sub.current_period_end = period_end(end, sub.plan.billing_interval)
        sub.next_billing_date = sub.current_period_end
    if due:
        db.commit()
    return created_or_existing

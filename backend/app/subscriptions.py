from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import Customer, Plan, Subscription, SubStatus

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def add_months(value: datetime, months: int = 1) -> datetime:
    # Calendar-aware month advancement, clamping dates such as Jan 31 to month end.
    import calendar
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)

def period_end(start: datetime, interval: str) -> datetime:
    return add_months(start, 12) if interval == "yearly" else add_months(start, 1)

def create_subscription(db: Session, customer_id: int, plan_id: int,
                        now: datetime | None = None) -> Subscription:
    now = now or utcnow()
    customer = db.get(Customer, customer_id)
    plan = db.get(Plan, plan_id)
    if customer is None:
        raise ValueError("Customer not found.")
    if plan is None or not plan.is_active:
        raise ValueError("Active plan not found.")
    end = period_end(now, plan.billing_interval)
    sub = Subscription(customer_id=customer_id, plan_id=plan_id,
                       status=SubStatus.ACTIVE.value, started_at=now,
                       current_period_start=now, current_period_end=end,
                       next_billing_date=end)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

def cancel_subscription(db: Session, subscription_id: int) -> Subscription:
    sub = db.get(Subscription, subscription_id)
    if sub is None:
        raise ValueError("Subscription not found.")
    sub.status = SubStatus.CANCELED.value
    sub.canceled_at = utcnow()
    db.commit()
    db.refresh(sub)
    return sub

def get_subscriptions(db: Session) -> list[Subscription]:
    return db.query(Subscription).order_by(Subscription.id).all()
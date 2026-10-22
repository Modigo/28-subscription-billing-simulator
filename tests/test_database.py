from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adjust these imports according to your project structure
from app.database import Base
from app.models import Customer, Plan, Subscription, SubStatus
from app.subscriptions import (
    add_months,
    period_end,
    create_subscription,
    cancel_subscription,
    get_subscriptions,
)
from app.plans import create_plan, get_plans, deactivate_plan


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_add_months_standard():
    start = datetime(2026, 1, 15)
    result = add_months(start, 1)
    assert result == datetime(2026, 2, 15)


def test_add_months_clamping():
    # January 31 plus 1 month should clamp to February 28 (or 29 in leap year)
    start = datetime(2026, 1, 31)
    result = add_months(start, 1)
    assert result.month == 2
    assert result.day == 28  # 2026 is not a leap year


def test_period_end_intervals():
    start = datetime(2026, 6, 1)
    assert period_end(start, "monthly") == datetime(2026, 7, 1)
    assert period_end(start, "yearly") == datetime(2027, 6, 1)


def test_create_and_get_plan(db_session):
    plan = create_plan(db_session, name="Pro Plan", price_kobo=500000, billing_interval="monthly")
    assert plan.id is not None
    assert plan.name == "Pro Plan"
    assert plan.price_kobo == 500000
    assert plan.billing_interval == "monthly"
    assert plan.is_active is True

    plans = get_plans(db_session, active_only=True)
    assert len(plans) == 1
    assert plans[0].id == plan.id


def test_plan_validation(db_session):
    with pytest.raises(ValueError, match="Plan name is required"):
        create_plan(db_session, name="   ", price_kobo=1000)

    with pytest.raises(ValueError, match="Plan price cannot be negative"):
        create_plan(db_session, name="Bad Plan", price_kobo=-100)

    with pytest.raises(ValueError, match="billing_interval must be monthly or yearly"):
        create_plan(db_session, name="Weird Plan", price_kobo=1000, billing_interval="weekly")


def test_deactivate_plan(db_session):
    plan = create_plan(db_session, name="Basic", price_kobo=100000)
    assert plan.is_active is True

    deactivated = deactivate_plan(db_session, plan.id)
    assert deactivated.is_active is False

    active_plans = get_plans(db_session, active_only=True)
    assert len(active_plans) == 0

    all_plans = get_plans(db_session, active_only=False)
    assert len(all_plans) == 1


def test_create_subscription(db_session):
    customer = Customer(name="Jane Doe", email="jane@example.com")
    db_session.add(customer)
    db_session.commit()

    plan = create_plan(db_session, name="Annual Plan", price_kobo=1200000, billing_interval="yearly")

    now = datetime(2026, 1, 1, 0, 0, 0)
    sub = create_subscription(db_session, customer_id=customer.id, plan_id=plan.id, now=now)

    assert sub.id is not None
    assert sub.customer_id == customer.id
    assert sub.plan_id == plan.id
    assert sub.status == SubStatus.ACTIVE.value
    assert sub.started_at == now
    assert sub.current_period_start == now
    assert sub.current_period_end == datetime(2027, 1, 1, 0, 0, 0)
    assert sub.next_billing_date == datetime(2027, 1, 1, 0, 0, 0)


def test_create_subscription_invalid_references(db_session):
    plan = create_plan(db_session, name="Monthly Plan", price_kobo=10000)

    # Invalid customer
    with pytest.raises(ValueError, match="Customer not found"):
        create_subscription(db_session, customer_id=999, plan_id=plan.id)

    # Inactive plan
    customer = Customer(name="John Smith", email="john@example.com")
    db_session.add(customer)
    db_session.commit()

    deactivate_plan(db_session, plan.id)
    with pytest.raises(ValueError, match="Active plan not found"):
        create_subscription(db_session, customer_id=customer.id, plan_id=plan.id)


def test_cancel_subscription(db_session):
    customer = Customer(name="Bob Test", email="bob@example.com")
    db_session.add(customer)
    db_session.commit()

    plan = create_plan(db_session, name="Monthly", price_kobo=5000)
    sub = create_subscription(db_session, customer_id=customer.id, plan_id=plan.id)

    assert sub.status == SubStatus.ACTIVE.value
    assert sub.canceled_at is None

    canceled_sub = cancel_subscription(db_session, sub.id)
    assert canceled_sub.status == SubStatus.CANCELED.value
    assert canceled_sub.canceled_at is not None

    all_subs = get_subscriptions(db_session)
    assert len(all_subs) == 1
    assert all_subs[0].status == SubStatus.CANCELED.value


def test_cancel_subscription_not_found(db_session):
    with pytest.raises(ValueError, match="Subscription not found"):
        cancel_subscription(db_session, subscription_id=9999)
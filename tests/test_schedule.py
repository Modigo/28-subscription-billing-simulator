import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Customer, Plan, Subscription, Invoice, SubStatus, InvoiceStatus
from app.subscriptions import create_subscription, cancel_subscription, period_end
from app.invoice import generate_invoice, update_invoice_status
from app.scheduler import run_billing_cycle

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_create_subscription(db_session):
    customer = Customer(name="John Doe", email="john@example.com")
    plan = Plan(name="Pro Monthly", price_kobo=5000, billing_interval="monthly")
    db_session.add_all([customer, plan])
    db_session.commit()

    sub = create_subscription(db_session, customer.id, plan.id)
    assert sub.id is not None
    assert sub.status == SubStatus.ACTIVE.value
    assert sub.customer_id == customer.id
    assert sub.plan_id == plan.id
    assert sub.next_billing_date > sub.started_at

def test_generate_invoice(db_session):
    customer = Customer(name="Jane Doe", email="jane@example.com")
    plan = Plan(name="Pro Yearly", price_kobo=50000, billing_interval="yearly")
    db_session.add_all([customer, plan])
    db_session.commit()

    sub = create_subscription(db_session, customer.id, plan.id)
    
    now = utcnow()
    invoice = generate_invoice(
        db=db_session,
        subscription_id=sub.id,
        plan_price_kobo=plan.price_kobo,
        billing_period_start=sub.current_period_start,
        billing_period_end=sub.current_period_end,
        issue_date=now,
        due_date=now + timedelta(days=7)
    )

    assert invoice.id is not None
    assert invoice.amount_kobo == 50000
    assert invoice.status == InvoiceStatus.PENDING.value

    # Test idempotency (generating invoice for the same period returns the existing one)
    invoice_dup = generate_invoice(
        db=db_session,
        subscription_id=sub.id,
        plan_price_kobo=plan.price_kobo,
        billing_period_start=sub.current_period_start,
        billing_period_end=sub.current_period_end,
        issue_date=now,
        due_date=now + timedelta(days=7)
    )
    assert invoice_dup.id == invoice.id

def test_run_billing_cycle(db_session):
    customer = Customer(name="Bob Smith", email="bob@example.com")
    plan = Plan(name="Basic Monthly", price_kobo=2000, billing_interval="monthly")
    db_session.add_all([customer, plan])
    db_session.commit()

    # Create subscription in the past so it is due for billing
    past_date = utcnow() - timedelta(days=35)
    sub = create_subscription(db_session, customer.id, plan.id, now=past_date)

    now = utcnow()
    invoices = run_billing_cycle(db_session, now=now)

    assert len(invoices) == 1
    assert invoices[0].subscription_id == sub.id
    assert invoices[0].amount_kobo == 2000

    # Subscription period and next billing date should have advanced
    db_session.refresh(sub)
    assert sub.next_billing_date > now

def test_cancel_subscription(db_session):
    customer = Customer(name="Alice", email="alice@example.com")
    plan = Plan(name="Standard", price_kobo=3000)
    db_session.add_all([customer, plan])
    db_session.commit()

    sub = create_subscription(db_session, customer.id, plan.id)
    canceled = cancel_subscription(db_session, sub.id)

    assert canceled.status == SubStatus.CANCELED.value
    assert canceled.canceled_at is not None

def test_update_invoice_status(db_session):
    customer = Customer(name="Charlie", email="charlie@example.com")
    plan = Plan(name="Basic", price_kobo=1000)
    db_session.add_all([customer, plan])
    db_session.commit()

    sub = create_subscription(db_session, customer.id, plan.id)
    now = utcnow()
    invoice = generate_invoice(
        db=db_session,
        subscription_id=sub.id,
        plan_price_kobo=plan.price_kobo,
        billing_period_start=sub.current_period_start,
        billing_period_end=sub.current_period_end,
        issue_date=now,
        due_date=now + timedelta(days=7)
    )

    updated = update_invoice_status(db_session, invoice.id, InvoiceStatus.PAID.value)
    assert updated.status == InvoiceStatus.PAID.value
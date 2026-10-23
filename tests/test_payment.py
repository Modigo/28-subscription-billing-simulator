from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Customer, Plan, Subscription, Invoice, DunningLog,
    InvoiceStatus, SubStatus
)
from app.payments import process_payment, process_due_retries


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(bind=engine)
    SessionTest = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    db = SessionTest()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_setup(db_session):
    """Seed test customer, plan, subscription, and invoice."""
    customer = Customer(name="Jane Doe", email="jane@example.com")
    plan = Plan(name="Pro Plan", price_kobo=500000, billing_interval="monthly")
    db_session.add_all([customer, plan])
    db_session.commit()

    now = datetime(2026, 1, 1, 12, 0, 0)
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status=SubStatus.ACTIVE.value,
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        next_billing_date=now + timedelta(days=30)
    )
    db_session.add(subscription)
    db_session.commit()

    invoice = Invoice(
        invoice_number="INV-001",
        subscription_id=subscription.id,
        billing_period_start=now,
        billing_period_end=now + timedelta(days=30),
        issue_date=now,
        due_date=now + timedelta(days=7),
        amount_kobo=500000,
        status=InvoiceStatus.PENDING.value
    )
    db_session.add(invoice)
    db_session.commit()

    return {"customer": customer, "plan": plan, "subscription": subscription, "invoice": invoice, "now": now}


def test_process_payment_success(db_session, sample_setup):
    invoice = sample_setup["invoice"]
    now = sample_setup["now"]

    attempt = process_payment(db_session, invoice.id, succeed=True, now=now)

    assert attempt.status == "succeeded"
    assert attempt.attempt_number == 1
    assert invoice.status == InvoiceStatus.PAID.value

    logs = db_session.query(DunningLog).filter_by(invoice_id=invoice.id).all()
    assert len(logs) == 0


def test_process_payment_failure_and_retry_scheduling(db_session, sample_setup):
    invoice = sample_setup["invoice"]
    subscription = sample_setup["subscription"]
    now = sample_setup["now"]

    attempt1 = process_payment(db_session, invoice.id, succeed=False, now=now, message="Card declined")

    assert attempt1.status == "failed"
    assert attempt1.attempt_number == 1
    assert invoice.status == InvoiceStatus.FAILED.value
    assert subscription.status == SubStatus.ACTIVE.value

    dunning_log1 = db_session.query(DunningLog).filter_by(invoice_id=invoice.id, attempt_number=1).first()
    assert dunning_log1 is not None
    assert dunning_log1.next_retry_at == now + timedelta(days=3)

    now2 = now + timedelta(days=3)
    attempt2 = process_payment(db_session, invoice.id, succeed=False, now=now2)
    assert attempt2.attempt_number == 2
    dunning_log2 = db_session.query(DunningLog).filter_by(invoice_id=invoice.id, attempt_number=2).first()
    assert dunning_log2.next_retry_at == now2 + timedelta(days=7)


def test_max_retries_reaches_past_due(db_session, sample_setup):
    invoice = sample_setup["invoice"]
    subscription = sample_setup["subscription"]
    now = sample_setup["now"]

    process_payment(db_session, invoice.id, succeed=False, now=now)                 # Attempt 1
    now = now + timedelta(days=3)
    process_payment(db_session, invoice.id, succeed=False, now=now)                 # Attempt 2
    now = now + timedelta(days=7)
    process_payment(db_session, invoice.id, succeed=False, now=now)                 # Attempt 3
    now = now + timedelta(days=14)
    process_payment(db_session, invoice.id, succeed=False, now=now)                 # Attempt 4 (Exhausts retries)

    assert subscription.status == SubStatus.PAST_DUE.value

    with pytest.raises(ValueError, match="Maximum payment attempts reached."):
        process_payment(db_session, invoice.id, succeed=False, now=now)


def test_process_due_retries(db_session, sample_setup):
    invoice = sample_setup["invoice"]
    now = sample_setup["now"]

    process_payment(db_session, invoice.id, succeed=False, now=now)

    due_logs_early = process_due_retries(db_session, now=now + timedelta(days=2))
    assert len(due_logs_early) == 0

    due_logs_due = process_due_retries(db_session, now=now + timedelta(days=3))
    assert len(due_logs_due) == 1
    assert due_logs_due[0].attempt_number == 1
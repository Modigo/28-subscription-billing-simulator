import pytest
from datetime import datetime, timedelta
from app.models import Customer, InvoiceStatus, PaymentAttempt
from app.plans import create_plan
from app.subscriptions import create_subscription
from app.invoice import generate_invoice, get_invoices
from app.scheduler import run_billing_cycle
from app.payments import process_payment
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app import models  # noqa


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False,
                           expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def seed(db, now):
    customer = Customer(name="Ada Example", email="ada@example.com")
    db.add(customer)
    db.commit()
    plan = create_plan(db, "Starter", 250000, "monthly")
    sub = create_subscription(db, customer.id, plan.id, now=now)
    return customer, plan, sub


def test_create_subscription_and_invoice(db):
    now = datetime(2026, 1, 1)
    _, plan, sub = seed(db, now)
    invoice = generate_invoice(
        db, sub.id, plan.price_kobo, now, sub.current_period_end,
        now, now + timedelta(days=7)
    )
    assert invoice.amount_kobo == 250000
    assert invoice.status == InvoiceStatus.PENDING.value
    assert invoice.invoice_number.startswith("INV-")


def test_invoice_is_idempotent(db):
    now = datetime(2026, 1, 1)
    _, plan, sub = seed(db, now)
    args = (sub.id, plan.price_kobo, now,
            sub.current_period_end, now, now + timedelta(days=7))
    first = generate_invoice(db, *args)
    second = generate_invoice(db, *args)
    assert first.id == second.id
    assert len(get_invoices(db, sub.id)) == 1


def test_scheduler_generates_due_invoice(db):
    now = datetime(2026, 1, 1)
    _, _, sub = seed(db, now)
    invoices = run_billing_cycle(
        db, now=sub.next_billing_date + timedelta(seconds=1))
    assert len(invoices) == 1


def test_successful_payment_marks_invoice_paid(db):
    now = datetime(2026, 1, 1)
    _, plan, sub = seed(db, now)
    invoice = generate_invoice(db, sub.id, plan.price_kobo, now, sub.current_period_end,
                               now, now + timedelta(days=7))
    attempt = process_payment(db, invoice.id, True, now=now)
    assert attempt.status == "succeeded"
    assert invoice.status == InvoiceStatus.PAID.value


def test_failed_payment_records_attempt_and_retry_log(db):
    now = datetime(2026, 1, 1)
    _, plan, sub = seed(db, now)
    invoice = generate_invoice(db, sub.id, plan.price_kobo, now, sub.current_period_end,
                               now, now + timedelta(days=7))
    attempt = process_payment(db, invoice.id, False, now=now)
    assert attempt.status == "failed"
    assert db.query(PaymentAttempt).filter_by(
        invoice_id=invoice.id).count() == 1
    assert invoice.dunning_logs[0].next_retry_at == now + timedelta(days=3)

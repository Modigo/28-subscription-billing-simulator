from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
import dunning


@pytest.fixture
def db_session():
    """Create an isolated in-memory database for each test."""

    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    models.Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_test_invoice(db_session, now):
    """Create a plan, subscription, and failed invoice for testing."""

    plan = models.Plan(
        name="Test Tier",
        price=10.0,
    )
    db_session.add(plan)
    db_session.commit()

    subscription = models.Subscription(
        customer_name="Test User",
        plan_id=plan.id,
        next_billing_date=now,
    )
    db_session.add(subscription)
    db_session.commit()

    invoice = models.Invoice(
        subscription_id=subscription.id,
        customer_name="Test User",
        amount_due=10.0,
        retry_count=0,
        status=models.InvoiceStatus.FAILED,
    )
    db_session.add(invoice)
    db_session.commit()

    return invoice, subscription


def test_dunning_sweep_empty_queue(db_session):
    """An empty queue should be handled without errors."""

    result = dunning.execute_system_dunning_sweep(
        db_session,
        now=datetime(2026, 1, 1, 12, 0),
    )

    assert result["status"] == "Success"
    assert result["processed"] == 0
    assert result["actions"] == []


def test_schedule_initial_retry(db_session):
    """The first retry should be scheduled three days after failure."""

    now = datetime(2026, 1, 1, 12, 0)
    invoice, _ = create_test_invoice(db_session, now)

    result = dunning.schedule_initial_retry(
        db_session,
        invoice,
        now=now,
    )

    assert result["status"] == "Success"
    assert invoice.retry_count == 0
    assert invoice.status == models.InvoiceStatus.FAILED
    assert invoice.next_retry_date == now + timedelta(days=3)


def test_retry_not_executed_before_due_date(db_session):
    """A retry must not run before its scheduled date."""

    now = datetime(2026, 1, 1, 12, 0)
    invoice, _ = create_test_invoice(db_session, now)

    dunning.schedule_initial_retry(db_session, invoice, now=now)

    result = dunning.execute_system_dunning_sweep(
        db_session,
        now=now + timedelta(days=2),
    )

    assert result["processed"] == 0
    assert invoice.retry_count == 0
    assert invoice.status == models.InvoiceStatus.FAILED
    assert invoice.next_retry_date == now + timedelta(days=3)


def test_retry_schedule_progression(db_session):
    """Retries should be scheduled for days 3, 7, and 14."""

    start = datetime(2026, 1, 1, 12, 0)
    invoice, _ = create_test_invoice(db_session, start)

    dunning.schedule_initial_retry(db_session, invoice, now=start)

    expected_dates = [
        start + timedelta(days=3),
        start + timedelta(days=7),
        start + timedelta(days=14),
    ]

    assert invoice.next_retry_date == expected_dates[0]

    for attempt in range(1, 4):
        result = dunning.execute_system_dunning_sweep(
            db_session,
            now=expected_dates[attempt - 1],
        )

        assert result["status"] == "Sweep Completed"
        assert invoice.retry_count == attempt
        assert invoice.status == models.InvoiceStatus.RETRYING

        if attempt < 3:
            assert invoice.next_retry_date == expected_dates[attempt]
        else:
            assert invoice.next_retry_date is None

            # The final attempt has started, but its outcome
            # has not yet been recorded. It must not be suspended.
            assert invoice.status == models.InvoiceStatus.RETRYING


def test_failed_retries_suspend_subscription(db_session):
    """Three failed retries should suspend the invoice and subscription."""

    start = datetime(2026, 1, 1, 12, 0)
    invoice, subscription = create_test_invoice(db_session, start)

    dunning.schedule_initial_retry(db_session, invoice, now=start)

    retry_dates = [
        start + timedelta(days=3),
        start + timedelta(days=7),
        start + timedelta(days=14),
    ]

    for attempt, retry_date in enumerate(retry_dates, start=1):
        dunning.execute_system_dunning_sweep(
            db_session,
            now=retry_date,
        )

        assert invoice.retry_count == attempt
        assert invoice.status == models.InvoiceStatus.RETRYING

        result = dunning.record_retry_result(
            db_session,
            invoice,
            succeeded=False,
        )

        if attempt < 3:
            assert result["status"] == "Retry Scheduled"
            assert invoice.status == models.InvoiceStatus.RETRYING
            assert invoice.next_retry_date == retry_dates[attempt]
        else:
            assert result["status"] == "Exhausted"
            assert invoice.status == models.InvoiceStatus.SUSPENDED
            assert invoice.next_retry_date is None
            assert subscription.status == models.SubStatus.SUSPENDED


def test_successful_retry_stops_future_retries(db_session):
    """A successful retry should mark the invoice as paid."""

    start = datetime(2026, 1, 1, 12, 0)
    invoice, subscription = create_test_invoice(db_session, start)

    dunning.schedule_initial_retry(db_session, invoice, now=start)

    first_retry_date = start + timedelta(days=3)

    dunning.execute_system_dunning_sweep(
        db_session,
        now=first_retry_date,
    )

    assert invoice.retry_count == 1
    assert invoice.status == models.InvoiceStatus.RETRYING

    result = dunning.record_retry_result(
        db_session,
        invoice,
        succeeded=True,
    )

    assert result["status"] == "Success"
    assert invoice.status == models.InvoiceStatus.PAID
    assert invoice.next_retry_date is None

    # A later sweep must not retry a paid invoice.
    later_result = dunning.execute_system_dunning_sweep(
        db_session,
        now=start + timedelta(days=30),
    )

    assert later_result["processed"] == 0
    assert invoice.retry_count == 1
    assert invoice.status == models.InvoiceStatus.PAID


def test_retry_result_rejected_for_non_retrying_invoice(db_session):
    """A retry result must not be recorded for an invoice not retrying."""

    start = datetime(2026, 1, 1, 12, 0)
    invoice, _ = create_test_invoice(db_session, start)

    with pytest.raises(ValueError):
        dunning.record_retry_result(
            db_session,
            invoice,
            succeeded=False,
        )

    assert invoice.retry_count == 0
    assert invoice.status == models.InvoiceStatus.FAILED

from datetime import datetime, timedelta

import pytest

from app.models import (
    Customer,
    Plan,
    Subscription,
    Invoice,
    InvoiceStatus,
    PaymentAttempt,
    SubStatus,
    DunningLog,
)

from app.payments import (
    process_payment,
    process_due_retries,
    RETRY_SCHEDULE,
    MAX_RETRIES,
)


# Create sample data for testing
def create_invoice_data(db):
    now = datetime(2026, 10, 22, 12, 0, 0)

    customer = Customer(
        name="Test Customer",
        email="test@example.com",
    )

    plan = Plan(
        name="Test Plan",
        price_kobo=500000,
        billing_interval="monthly",
    )

    db.add_all([customer, plan])
    db.flush()

    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status=SubStatus.ACTIVE.value,
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        next_billing_date=now + timedelta(days=30),
    )

    db.add(subscription)
    db.flush()

    invoice = Invoice(
        invoice_number="TEST-INV-001",
        subscription_id=subscription.id,
        billing_period_start=now,
        billing_period_end=now + timedelta(days=30),
        issue_date=now,
        due_date=now + timedelta(days=7),
        amount_kobo=500000,
        status=InvoiceStatus.PENDING.value,
    )

    db.add(invoice)
    db.commit()

    return subscription, invoice, now


# Test 1: Successful payment
def test_successful_payment(db):
    subscription, invoice, now = create_invoice_data(db)

    attempt = process_payment(
        db,
        invoice.id,
        succeed=True,
        now=now,
    )

    db.refresh(invoice)

    assert attempt.status == "succeeded"
    assert attempt.attempt_number == 1
    assert invoice.status == InvoiceStatus.PAID.value


# Test 2: Failed payment
def test_failed_payment(db):
    subscription, invoice, now = create_invoice_data(db)

    attempt = process_payment(
        db,
        invoice.id,
        succeed=False,
        now=now,
    )

    db.refresh(invoice)

    assert attempt.status == "failed"
    assert invoice.status == InvoiceStatus.FAILED.value


# Test 3: First failure schedules a retry after 3 days
def test_retry_scheduled_after_three_days(db):
    subscription, invoice, now = create_invoice_data(db)

    process_payment(
        db,
        invoice.id,
        succeed=False,
        now=now,
    )

    log = db.query(DunningLog).filter_by(
        invoice_id=invoice.id
    ).one()

    assert log.next_retry_at == now + timedelta(days=3)


# Test 4: Retry schedule is correct
def test_retry_schedule():
    assert RETRY_SCHEDULE == [3, 7, 14]
    assert MAX_RETRIES == 3


# Test 5: Successful payment reactivates a past-due subscription
def test_success_reactivates_subscription(db):
    subscription, invoice, now = create_invoice_data(db)

    subscription.status = SubStatus.PAST_DUE.value
    db.commit()

    process_payment(
        db,
        invoice.id,
        succeed=True,
        now=now,
    )

    db.refresh(subscription)

    assert subscription.status == SubStatus.ACTIVE.value


# Test 6: Four failures mark the subscription as past due
def test_four_failures_mark_subscription_past_due(db):
    subscription, invoice, now = create_invoice_data(db)

    for _ in range(4):
        process_payment(
            db,
            invoice.id,
            succeed=False,
            now=now,
        )

    db.refresh(subscription)

    assert subscription.status == SubStatus.PAST_DUE.value

    attempts = db.query(PaymentAttempt).filter_by(
        invoice_id=invoice.id
    ).count()

    assert attempts == 4


# Test 7: Nonexistent invoice raises an error
def test_nonexistent_invoice(db):
    with pytest.raises(ValueError, match="Invoice not found"):
        process_payment(
            db,
            invoice_id=99999,
            succeed=True,
        )


# Test 8: A paid invoice cannot be paid again
def test_paid_invoice_cannot_be_paid_again(db):
    subscription, invoice, now = create_invoice_data(db)

    process_payment(
        db,
        invoice.id,
        succeed=True,
        now=now,
    )

    with pytest.raises(ValueError, match="already paid"):
        process_payment(
            db,
            invoice.id,
            succeed=True,
            now=now,
        )


# Test 9: Fifth payment attempt is rejected
def test_fifth_attempt_rejected(db):
    subscription, invoice, now = create_invoice_data(db)

    for _ in range(4):
        process_payment(
            db,
            invoice.id,
            succeed=False,
            now=now,
        )

    with pytest.raises(
        ValueError,
        match="Maximum payment attempts reached",
    ):
        process_payment(
            db,
            invoice.id,
            succeed=False,
            now=now,
        )


# Test 10: Due retries are returned
def test_due_retry_is_returned(db):
    subscription, invoice, now = create_invoice_data(db)

    process_payment(
        db,
        invoice.id,
        succeed=False,
        now=now,
    )

    due_time = now + timedelta(days=3)

    results = process_due_retries(
        db,
        now=due_time,
    )

    assert len(results) == 1
    assert results[0].invoice_id == invoice.id

def test_paid_invoice_is_excluded_from_due_retries(db):
    subscription, invoice, now = create_invoice_data(db)

    # Simulate a failed payment, which schedules a retry.
    process_payment(
        db,
        invoice.id,
        succeed=False,
        now=now,
    )

    # Simulate a successful payment one hour later.
    process_payment(
        db,
        invoice.id,
        succeed=True,
        now=now + timedelta(hours=1),
    )

    # Check for due retries four days after the initial failure.
    results = process_due_retries(
        db,
        now=now + timedelta(days=4),
    )

    # A paid invoice must not appear in the retry results.
    assert all(
        retry.invoice_id != invoice.id
        for retry in results
    )

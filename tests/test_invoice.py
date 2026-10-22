import pytest
import app.database as database

from app.database import initialize_database
from app.invoice import (
    generate_invoice,
    get_invoice,
    get_invoices,
    update_invoice_status,
)


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Give each test its own temporary SQLite database."""

    test_database = tmp_path / "test_billing.db"

    monkeypatch.setattr(
        database,
        "DATABASE_NAME",
        str(test_database),
    )

    initialize_database()

    yield


def create_test_invoice(
    subscription_id="SUB-001",
    start="2026-10-20",
    end="2026-11-20",
    price=500000,
    issue_date="2026-10-20",
    due_date="2026-10-27",
):
    """Create a test invoice using the real invoice function."""

    return generate_invoice(
        subscription_id=subscription_id,
        plan_price_kobo=price,
        billing_period_start=start,
        billing_period_end=end,
        issue_date=issue_date,
        due_date=due_date,
    )


def test_get_invoices_returns_empty_list(db):
    assert get_invoices() == []


def test_get_invoices_returns_all_invoices(db):
    create_test_invoice(subscription_id="SUB-001")
    create_test_invoice(
        subscription_id="SUB-002",
        start="2026-11-20",
        end="2026-12-20",
    )
    invoices = get_invoices()

    assert len(invoices) == 2
    assert all(invoice.invoice_id for invoice in invoices)


def test_filter_invoices_by_subscription(db):
    create_test_invoice(subscription_id="SUB-001")
    create_test_invoice(
        subscription_id="SUB-002",
        start="2026-11-20",
        end="2026-12-20",
    )

    invoices = get_invoices(subscription_id="SUB-001")

    assert len(invoices) == 1
    assert invoices[0].subscription_id == "SUB-001"


def test_filter_invoices_by_status(db):
    create_test_invoice()

    # Simulate a successful payment status update.
    connection = database.get_connection()

    try:
        connection.execute(
            """
            UPDATE invoices
            SET status = ?
            WHERE subscription_id = ?
            """,
            ("paid", "SUB-001"),
        )
        connection.commit()
    finally:
        connection.close()

    assert get_invoices(status="pending") == []
    assert len(get_invoices(status="paid")) == 1


def test_filter_by_subscription_and_status(db):
    create_test_invoice(subscription_id="SUB-001")
    create_test_invoice(
        subscription_id="SUB-002",
        start="2026-11-20",
        end="2026-12-20",
    )

    connection = database.get_connection()

    try:
        connection.execute(
            "UPDATE invoices SET status = ? WHERE subscription_id = ?",
            ("paid", "SUB-002"),
        )
        connection.commit()

    finally:
        connection.close()

    invoices = get_invoices(
        subscription_id="SUB-001",
        status="pending",
    )

    assert len(invoices) == 1
    assert invoices[0].subscription_id == "SUB-001"
    assert invoices[0].status == "pending"


def test_get_invoice_returns_none_for_unknown_id(db):
    assert get_invoice("INV-DOES-NOT-EXIST") is None


def test_duplicate_generation_returns_same_invoice(db):
    first = create_test_invoice()
    second = create_test_invoice()

    assert first.invoice_id == second.invoice_id
    assert len(get_invoices()) == 1


def test_invalid_billing_period_is_rejected(db):
    with pytest.raises(ValueError):
        get_invoices(subscription_id="  ")


def test_update_invoice_status_to_paid(db):
    invoice = create_test_invoice()

    updated = update_invoice_status(invoice.invoice_id, "paid")

    assert updated is not None
    assert updated.status == "paid"
    assert get_invoice(invoice.invoice_id).status == "paid"


def test_update_unknown_invoice_returns_none(db):
    result = update_invoice_status("INV-UNKNOWN", "paid")

    assert result is None


def test_invalid_invoice_status_is_rejected(db):
    invoice = create_test_invoice()

    with pytest.raises(ValueError):
        update_invoice_status(invoice.invoice_id, "unknown")

    assert get_invoice(invoice.invoice_id).status == "pending"

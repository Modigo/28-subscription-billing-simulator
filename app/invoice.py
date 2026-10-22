from dataclasses import dataclass
import sqlite3
import uuid

from datetime import date, datetime, timezone

from app.database import get_connection


@dataclass
class Invoice:
    invoice_id: str
    subscription_id: str
    amount_kobo: int
    billing_period_start: str
    billing_period_end: str
    issue_date: str
    due_date: str
    status: str
    created_at: str


def calculate_invoice_amount(plan_price_kobo: int) -> int:
    """Return the validated invoice amount in kobo."""

    if isinstance(plan_price_kobo, bool) or not isinstance(
        plan_price_kobo, int
    ):
        raise TypeError("Plan price must be an integer in kobo.")

    if plan_price_kobo < 0:
        raise ValueError("Plan price cannot be negative.")

    return plan_price_kobo


def invoice_exists(
        subscription_id: str,
        billing_period_start: str,
        billing_period_end: str,
) -> bool:
    """Check whether an invoice exists for this billing period."""

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT 1 FROM invoices
            WHERE subscription_id = ?
            AND billing_period_start = ?
            AND billing_period_end = ?
            """,
            (
                subscription_id,
                billing_period_start,
                billing_period_end,
            ),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def get_invoice(invoice_id: str) -> Invoice | None:
    """Retrieve an invoice by its ID."""

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (invoice_id,),
        ).fetchone()

        if row is None:
            return None

        return Invoice(**dict(row))

    finally:
        connection.close


def update_invoice_status(
        invoice_id: str,
        status: str,
) -> Invoice | None:
    """Update an invoice's status and return the updated invoice."""

    allowed_statuses = {"pending", "paid", "failed"}

    if not isinstance(status, str) or status not in allowed_statuses:
        raise ValueError(
            f"Invalid status. Choose one of: {', '.join(sorted(allowed_statuses))}."
        )

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE invoices
            SET status = ?
            WHERE invoice_id = ?
            """,
            (status, invoice_id),
        )
        connection.commit()

        row = connection.execute(
            "SELECT * FROM invoices WHERE invoice_id = ?",
            (invoice_id,),
        ).fetchone()

        if row is None:
            return None

        return Invoice(**dict(row))

    finally:
        connection.close()


def generate_invoice(
        subscription_id: str,
        plan_price_kobo: int,
        billing_period_start: str,
        billing_period_end: str,
        issue_date: str,
        due_date: str,
) -> Invoice:
    """Generate an invoice or return the existing invoice."""

    if not isinstance(subscription_id, str) or not subscription_id.strip():
        raise ValueError("Subscription ID is required.")

    # Validate the supplied price.
    amount_kobo = calculate_invoice_amount(plan_price_kobo)

    # Validate the dates
    try:
        start = date.fromisoformat(billing_period_start)
        end = date.fromisoformat(billing_period_end)
        issued = date.fromisoformat(issue_date)
        due = date.fromisoformat(due_date)

    except (TypeError, ValueError) as error:
        raise ValueError(
            "Dates must use YYYY-MM-DD format."
        ) from error

    if end <= start:
        raise ValueError("Billing period end must follow its start.")

    if due < issued:
        raise ValueError("Due date cannot precede issue date.")

    # Repeated billing requests must not create duplicate invoices.
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            """
            SELECT * FROM invoices
            WHERE subscription_id = ?
            AND billing_period_start = ?
            AND billing_period_end = ?
            """,
            (subscription_id, billing_period_start, billing_period_end),
        ).fetchone()

        if existing is not None:
            connection.commit()
            return Invoice(**dict(existing))

        invoice = Invoice(
            invoice_id=f"INV-{uuid.uuid4().hex[:12].upper()}",
            subscription_id=subscription_id,
            amount_kobo=amount_kobo,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            issue_date=issue_date,
            due_date=due_date,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        connection.execute(
            """
            INSERT INTO invoices (
                invoice_id,
                subscription_id,
                amount_kobo,
                billing_period_start,
                billing_period_end,
                issue_date,
                due_date,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice.invoice_id,
                invoice.subscription_id,
                invoice.amount_kobo,
                invoice.billing_period_start,
                invoice.billing_period_end,
                invoice.issue_date,
                invoice.due_date,
                invoice.status,
                invoice.created_at,
            ),
        )

        connection.commit()
        return invoice

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_invoices(
        subscription_id: str | None = None,
        status: str | None = None,
) -> list[Invoice]:
    """Retrieve invoices optionally filtered by subscription and status."""

    query = "SELECT * FROM invoices"
    conditions = []
    parameters = []

    if subscription_id is not None:
        if not subscription_id.strip():
            raise ValueError("Subscription ID cannot be empty.")

        conditions.append("subscription_id = ?")
        parameters.append(subscription_id)

    if status is not None:
        if not status.strip():
            raise ValueError("Status cannot be empty.")

        conditions.append("status = ?")
        parameters.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC, invoice_id ASC"

    connection = get_connection()

    try:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [
            Invoice(**dict(row))
            for row in rows
        ]

    finally:
        connection.close()

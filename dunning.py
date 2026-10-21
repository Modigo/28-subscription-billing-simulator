from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Invoice, InvoiceStatus, SubStatus


RETRY_SCHEDULE = [3, 7, 14]
MAX_RETRIES = len(RETRY_SCHEDULE)


def schedule_initial_retry(
    db: Session,
    invoice: Invoice,
    now: datetime | None = None,
):
    """Schedule the first retry three days after payment failure."""

    now = now or datetime.now()

    if invoice.status != InvoiceStatus.FAILED:
        raise ValueError("Only failed invoices can be scheduled for retry.")

    if invoice.retry_count != 0:
        raise ValueError(
            "The initial retry can only be scheduled before any retries."
        )

    invoice.next_retry_date = now + timedelta(days=RETRY_SCHEDULE[0])

    try:
        db.commit()
        db.refresh(invoice)
    except Exception:
        db.rollback()
        raise

    return {
        "status": "Success",
        "message": (
            f"First retry scheduled for "
            f"{invoice.next_retry_date.strftime('%Y-%m-%d %H:%M:%S')}."
        ),
    }


def get_active_dunning_records(
    db: Session,
    now: datetime | None = None,
):
    """Return failed invoices whose scheduled retry dates have arrived."""

    now = now or datetime.now()

    return (
        db.query(Invoice)
        .filter(
            Invoice.status.in_([
                InvoiceStatus.FAILED,
                InvoiceStatus.RETRYING,
            ]),
            Invoice.next_retry_date.isnot(None),
            Invoice.next_retry_date <= now,
        )
        .all()
    )


def execute_system_dunning_sweep(
    db: Session,
    now: datetime | None = None,
):
    """Initiate retries for invoices whose retry dates are due."""

    now = now or datetime.now()
    records = get_active_dunning_records(db, now)

    if not records:
        return {
            "status": "Success",
            "message": "No invoices require dunning recovery processing.",
            "processed": 0,
            "actions": [],
        }

    actions_taken = []

    try:
        for invoice in records:
            scheduled_date = invoice.next_retry_date

            # Initiate the next retry.
            invoice.retry_count += 1
            invoice.status = InvoiceStatus.RETRYING

            if invoice.retry_count < MAX_RETRIES:
                next_retry_day = RETRY_SCHEDULE[invoice.retry_count]
                current_retry_day = RETRY_SCHEDULE[invoice.retry_count - 1]
                interval = next_retry_day - current_retry_day

                invoice.next_retry_date = (
                    scheduled_date + timedelta(days=interval)
                )
            else:
                # Wait for the final retry's payment outcome.
                invoice.next_retry_date = None

            actions_taken.append(
                f"Initiated retry #{invoice.retry_count} "
                f"for {invoice.customer_name}."
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "status": "Sweep Completed",
        "processed": len(records),
        "actions": actions_taken,
    }


def record_retry_result(
    db: Session,
    invoice: Invoice,
    succeeded: bool,
):
    """Record a retry outcome and handle final suspension."""

    try:
        if invoice.status != InvoiceStatus.RETRYING:
            raise ValueError(
                "A retry result can only be recorded for an invoice "
                "currently undergoing a retry."
            )

        if not 1 <= invoice.retry_count <= MAX_RETRIES:
            raise ValueError("Invalid retry count.")

        if succeeded:
            invoice.status = InvoiceStatus.PAID
            invoice.next_retry_date = None

            db.commit()

            return {
                "status": "Success",
                "message": f"Payment recovered for {invoice.customer_name}.",
            }

        if invoice.retry_count >= MAX_RETRIES:
            invoice.status = InvoiceStatus.SUSPENDED
            invoice.next_retry_date = None

            if invoice.subscription:
                invoice.subscription.status = SubStatus.SUSPENDED

            db.commit()

            return {
                "status": "Exhausted",
                "message": (
                    f"All retries failed for {invoice.customer_name}. "
                    "Subscription suspended."
                ),
            }

        if invoice.next_retry_date is None:
            raise ValueError(
                "The next retry date is missing even though retries remain."
            )

        db.commit()

        return {
            "status": "Retry Scheduled",
            "message": (
                f"Payment failed for {invoice.customer_name}. "
                f"Next retry: "
                f"{invoice.next_retry_date.strftime('%Y-%m-%d %H:%M:%S')}."
            ),
        }

    except Exception:
        db.rollback()
        raise

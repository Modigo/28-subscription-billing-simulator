from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import (
    Invoice,
    Subscription,
    InvoiceStatus,
    SubStatus,
    DunningLog,
)


RETRY_SCHEDULE = [3, 7, 14]
MAX_RETRIES = len(RETRY_SCHEDULE)


def add_dunning_log(
    db: Session,
    invoice: Invoice,
    attempt_number: int,
    message: str,
    now: datetime,
):
    log = DunningLog(
        invoice=invoice,
        attempt_number=attempt_number,
        execution_date=now,
        log_message=message,
    )

    db.add(log)


def schedule_initial_retry(
    db: Session,
    invoice: Invoice,
    now: datetime | None = None,
):
    now = now or datetime.now()

    if invoice.status != InvoiceStatus.FAILED:
        raise ValueError("Only failed invoices can be scheduled for retry.")

    if invoice.retry_count != 0:
        raise ValueError("The initial retry requires a retry count of zero.")

    if invoice.next_retry_date is not None:
        raise ValueError("A retry is already scheduled.")

    if invoice.payment_failed_at is not None:
        raise ValueError("The payment failure has already been recorded.")

    if (
        invoice.subscription is None
        or invoice.subscription.status != SubStatus.ACTIVE
    ):
        raise ValueError(
            "Retries can only be scheduled for active subscriptions."
        )

    try:
        invoice.payment_failed_at = now

        invoice.next_retry_date = (
            now + timedelta(days=RETRY_SCHEDULE[0])
        )

        add_dunning_log(
            db,
            invoice,
            1,
            "First retry scheduled for day 3.",
            now,
        )

        db.commit()
        db.refresh(invoice)

        return {
            "status": "Success",
            "message": (
                "First retry scheduled for "
                f"{invoice.next_retry_date.strftime('%Y-%m-%d %H:%M:%S')}."
            ),
        }

    except Exception:
        db.rollback()
        raise


def get_active_dunning_records(
    db: Session,
    now: datetime | None = None,
):
    now = now or datetime.now()

    return (
        db.query(Invoice)
        .filter(
            Invoice.status.in_(
                [
                    InvoiceStatus.FAILED,
                    InvoiceStatus.RETRYING,
                ]
            ),
            Invoice.next_retry_date.isnot(None),
            Invoice.next_retry_date <= now,
            Invoice.retry_count < MAX_RETRIES,
            Invoice.payment_failed_at.isnot(None),
            Invoice.subscription.has(
                Subscription.status == SubStatus.ACTIVE
            ),
        )
        .all()
    )


def execute_system_dunning_sweep(
    db: Session,
    now: datetime | None = None,
):
    now = now or datetime.now()

    records = get_active_dunning_records(db, now)

    if not records:
        return {
            "status": "Success",
            "message": "No invoices require dunning recovery processing.",
            "processed": 0,
            "actions": [],
        }

    actions = []
    processed = 0

    try:
        for invoice in records:
            subscription = invoice.subscription

            if (
                subscription is None
                or subscription.status != SubStatus.ACTIVE
            ):
                invoice.next_retry_date = None
                continue

            if invoice.retry_count >= MAX_RETRIES:
                continue

            if invoice.payment_failed_at is None:
                continue

            invoice.retry_count += 1
            attempt = invoice.retry_count

            invoice.status = InvoiceStatus.RETRYING

            if attempt < MAX_RETRIES:
                target_day = RETRY_SCHEDULE[attempt]

                invoice.next_retry_date = (
                    invoice.payment_failed_at
                    + timedelta(days=target_day)
                )
            else:
                invoice.next_retry_date = None

            message = (
                f"Retry #{attempt} initiated for "
                f"{invoice.customer_name}."
            )

            add_dunning_log(
                db,
                invoice,
                attempt,
                message,
                now,
            )

            actions.append(message)
            processed += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "status": "Sweep Completed",
        "processed": processed,
        "actions": actions,
    }


def record_retry_result(
    db: Session,
    invoice: Invoice,
    succeeded: bool,
    now: datetime | None = None,
):
    now = now or datetime.now()

    try:
        if invoice.status != InvoiceStatus.RETRYING:
            raise ValueError(
                "The invoice does not have an active retry attempt."
            )

        if not 1 <= invoice.retry_count <= MAX_RETRIES:
            raise ValueError("Invalid retry count.")

        subscription = invoice.subscription

        if subscription is None:
            raise ValueError("The invoice has no associated subscription.")

        if succeeded:
            invoice.status = InvoiceStatus.PAID
            invoice.next_retry_date = None

            message = (
                f"Payment recovered for {invoice.customer_name} "
                f"on retry #{invoice.retry_count}."
            )

            add_dunning_log(
                db,
                invoice,
                invoice.retry_count,
                message,
                now,
            )

            db.commit()

            return {
                "status": "Success",
                "message": message,
            }

        if invoice.retry_count == MAX_RETRIES:
            invoice.status = InvoiceStatus.SUSPENDED
            invoice.next_retry_date = None

            if subscription.status == SubStatus.ACTIVE:
                subscription.status = SubStatus.SUSPENDED

            message = (
                f"Retry #{invoice.retry_count} failed for "
                f"{invoice.customer_name}. "
                "All retries exhausted."
            )

            add_dunning_log(
                db,
                invoice,
                invoice.retry_count,
                message,
                now,
            )

            db.commit()

            return {
                "status": "Exhausted",
                "message": message,
            }

        if invoice.next_retry_date is None:
            raise ValueError(
                "The next retry date is missing even though retries remain."
            )

        message = (
            f"Retry #{invoice.retry_count} failed for "
            f"{invoice.customer_name}. "
            f"Next retry: "
            f"{invoice.next_retry_date.strftime('%Y-%m-%d %H:%M:%S')}."
        )

        add_dunning_log(
            db,
            invoice,
            invoice.retry_count,
            message,
            now,
        )

        db.commit()

        return {
            "status": "Retry Scheduled",
            "message": message,
        }

    except Exception:
        db.rollback()
        raise

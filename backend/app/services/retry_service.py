"""Retry processing service for failed invoices."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.billing_event import BillingEvent
from app.models.invoice import Invoice
from app.models.payment_attempt import PaymentAttempt
from app.models.subscription import Subscription
from app.services.payment_service import PaymentService
from app.utils.clock import Clock


class RetryService:
    """Process failed invoices according to retry schedule."""

    @staticmethod
    def schedule_next_retry(invoice: Invoice, retry_schedule: list[int]) -> None:
        """Schedule the next retry time for a failed invoice."""
        now = Clock.now()
        attempt = invoice.attempt_count
        if attempt < len(retry_schedule):
            days = retry_schedule[attempt]
            invoice.next_retry_at = now + timedelta(days=days)
        # If attempts exceed schedule, next_retry_at stays None (exhausted)

    @staticmethod
    def process_retries(db: Session) -> dict:
        """
        Process all eligible failed invoices.
        Returns a summary of results.
        """
        settings = get_settings()
        retry_schedule = settings.get_retry_schedule()
        now = Clock.now()

        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "errors": [],
        }

        # Find failed invoices with next_retry_at <= now
        eligible = (
            db.query(Invoice)
            .filter(
                Invoice.status == "failed",
                Invoice.next_retry_at != None,
                Invoice.next_retry_at <= now,
            )
            .all()
        )

        for invoice in eligible:
            try:
                # For retry processing, simulate success if this is the last retry
                # or failure otherwise — deterministic for demo
                attempt = invoice.attempt_count
                if attempt >= len(retry_schedule):
                    # Exhausted — mark subscription as past_due
                    subscription = (
                        db.query(Subscription)
                        .filter(Subscription.id == invoice.subscription_id)
                        .first()
                    )
                    if subscription:
                        subscription.status = "past_due"
                        db.add(BillingEvent(
                            event_type="retries_exhausted",
                            subscription_id=subscription.id,
                            invoice_id=invoice.id,
                            details={"attempt_count": attempt},
                        ))
                    invoice.status = "failed"
                    results["failed"] += 1
                else:
                    # Retry — simulate success for demo
                    PaymentService.simulate_payment(
                        db, invoice, "success"
                    )
                    subscription = (
                        db.query(Subscription)
                        .filter(Subscription.id == invoice.subscription_id)
                        .first()
                    )
                    if subscription and subscription.status == "past_due":
                        subscription.status = "active"
                    db.add(BillingEvent(
                        event_type="retry_success",
                        subscription_id=invoice.subscription_id,
                        invoice_id=invoice.id,
                        details={"attempt_number": invoice.attempt_count},
                    ))
                    results["succeeded"] += 1

                results["processed"] += 1
                db.commit()
            except Exception as e:
                db.rollback()
                results["errors"].append(
                    f"Error processing invoice {invoice.id}: {str(e)}"
                )

        return results

    @staticmethod
    def process_retry_with_outcome(
        db: Session, invoice: Invoice, outcome: str, failure_reason: str | None = None
    ) -> dict:
        """
        Process a single retry with a specified outcome.
        Used for manual retry simulation.
        """
        settings = get_settings()
        retry_schedule = settings.get_retry_schedule()
        now = Clock.now()

        result = {"success": False, "message": ""}

        if invoice.status != "failed":
            result["message"] = "Invoice is not in failed status"
            return result

        attempt = PaymentService.simulate_payment(
            db, invoice, outcome, failure_reason
        )

        subscription = (
            db.query(Subscription)
            .filter(Subscription.id == invoice.subscription_id)
            .first()
        )

        if outcome == "success":
            if subscription and subscription.status in ("past_due", "suspended"):
                subscription.status = "active"
            db.add(BillingEvent(
                event_type="retry_success",
                subscription_id=invoice.subscription_id,
                invoice_id=invoice.id,
                details={"attempt_number": attempt.attempt_number},
            ))
            result["success"] = True
            result["message"] = f"Payment succeeded on attempt {attempt.attempt_number}"
        else:
            # Schedule next retry or exhaust
            RetryService.schedule_next_retry(invoice, retry_schedule)
            if invoice.next_retry_at is None:
                # Exhausted
                if subscription:
                    subscription.status = "past_due"
                db.add(BillingEvent(
                    event_type="retries_exhausted",
                    subscription_id=invoice.subscription_id,
                    invoice_id=invoice.id,
                    details={"attempt_count": invoice.attempt_count},
                ))
                result["message"] = "All retries exhausted. Subscription marked past_due."
            else:
                db.add(BillingEvent(
                    event_type="retry_failed",
                    subscription_id=invoice.subscription_id,
                    invoice_id=invoice.id,
                    details={
                        "attempt_number": attempt.attempt_number,
                        "next_retry_at": str(invoice.next_retry_at),
                    },
                ))
                result["message"] = (
                    f"Retry failed. Next retry at {invoice.next_retry_at}"
                )

        db.commit()
        return result

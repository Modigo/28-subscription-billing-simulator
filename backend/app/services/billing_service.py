"""Billing scheduler service for recurring billing."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.billing_event import BillingEvent
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.plan_change import PlanChangeHistory
from app.models.subscription import Subscription
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.services.retry_service import RetryService
from app.utils.clock import Clock


class BillingService:
    """Recurring billing scheduler."""

    @staticmethod
    def run_billing_cycle(db: Session) -> dict:
        """
        Process all subscriptions whose billing period has ended.
        Generates new invoices and advances billing periods.
        """
        now = Clock.now()

        results = {
            "processed": 0,
            "invoices_created": 0,
            "errors": [],
        }

        # Find subscriptions whose period has ended
        eligible = (
            db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.current_period_end <= now,
            )
            .all()
        )

        for sub in eligible:
            try:
                # Check for pending plan changes
                pending_change = (
                    db.query(PlanChangeHistory)
                    .filter(
                        PlanChangeHistory.subscription_id == sub.id,
                        PlanChangeHistory.change_type == "next_cycle",
                        PlanChangeHistory.effective_at <= now,
                    )
                    .order_by(PlanChangeHistory.created_at.desc())
                    .first()
                )

                if pending_change:
                    sub.plan_id = pending_change.new_plan_id

                plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
                if not plan:
                    results["errors"].append(
                        f"Plan {sub.plan_id} not found for subscription {sub.id}"
                    )
                    continue

                # Calculate new period
                new_period_start = sub.current_period_end
                if plan.billing_interval == "yearly":
                    new_period_end = new_period_start + timedelta(days=365)
                else:
                    new_period_end = new_period_start + timedelta(days=30)

                # Generate invoice
                invoice = InvoiceService.generate_invoice(
                    db, sub, plan, new_period_start, new_period_end
                )

                if invoice:
                    # Simulate payment (success by default for recurring)
                    PaymentService.simulate_payment(db, invoice, "success")

                    db.add(BillingEvent(
                        event_type="billing_cycle",
                        subscription_id=sub.id,
                        invoice_id=invoice.id,
                        details={
                            "plan_name": plan.name,
                            "amount": str(invoice.amount),
                        },
                    ))

                    sub.current_period_start = new_period_start
                    sub.current_period_end = new_period_end
                    results["invoices_created"] += 1
                else:
                    # Invoice already exists — just advance period
                    sub.current_period_start = new_period_start
                    sub.current_period_end = new_period_end

                results["processed"] += 1
                db.commit()
            except Exception as e:
                db.rollback()
                results["errors"].append(
                    f"Error processing subscription {sub.id}: {str(e)}"
                )

        return results

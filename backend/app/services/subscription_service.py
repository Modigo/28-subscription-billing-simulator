"""Subscription management service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.billing_event import BillingEvent
from app.models.customer import Customer
from app.models.plan import Plan
from app.models.plan_change import PlanChangeHistory
from app.models.subscription import Subscription
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.services.retry_service import RetryService
from app.utils.clock import Clock


# Valid state transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "trialing": ["active", "canceled"],
    "active": ["paused", "canceled", "past_due", "suspended"],
    "past_due": ["active", "suspended"],
    "suspended": ["active"],
    "paused": ["active", "canceled"],
    "canceled": [],
}


class SubscriptionService:
    """Business logic for subscription lifecycle."""

    @staticmethod
    def list_subscriptions(
        db: Session,
        customer_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Subscription]:
        """List subscriptions with optional filters."""
        query = db.query(Subscription)
        if customer_id:
            query = query.filter(Subscription.customer_id == customer_id)
        if status:
            query = query.filter(Subscription.status == status)
        return (
            query.order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_subscription(db: Session, subscription_id: int) -> Subscription | None:
        """Get a subscription by ID."""
        return (
            db.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )

    @staticmethod
    def create_subscription(
        db: Session,
        customer_id: int,
        plan_id: int,
        payment_outcome: str = "success",
    ) -> Subscription:
        """
        Create a new subscription.
        If no trial, generate the first invoice and simulate payment.
        """
        now = Clock.now()

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        if plan.status != "active":
            raise ValueError("Cannot subscribe to a retired plan")

        # Determine billing period
        period_start = now
        if plan.billing_interval == "yearly":
            period_end = period_start + timedelta(days=365)
        else:
            period_end = period_start + timedelta(days=30)

        # Determine status and trial
        trial_end = None
        if plan.trial_days > 0:
            status = "trialing"
            trial_end = now + timedelta(days=plan.trial_days)
        else:
            status = "active"

        subscription = Subscription(
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            current_period_start=period_start,
            current_period_end=period_end,
            trial_end=trial_end,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Generate first invoice if no trial
        invoice = None
        if plan.trial_days == 0:
            invoice = InvoiceService.generate_invoice(
                db, subscription, plan, period_start, period_end
            )
            if invoice:
                failure_reason = (
                    "Simulated payment failure" if payment_outcome == "failure" else None
                )
                PaymentService.simulate_payment(
                    db, invoice, payment_outcome, failure_reason
                )
                if payment_outcome == "failure":
                    retry_schedule = [3, 7, 14]
                    RetryService.schedule_next_retry(invoice, retry_schedule)
                    db.commit()

                db.add(BillingEvent(
                    event_type="subscription_created",
                    subscription_id=subscription.id,
                    invoice_id=invoice.id if invoice else None,
                    details={
                        "plan_name": plan.name,
                        "payment_outcome": payment_outcome,
                    },
                ))
                db.commit()

        return subscription

    @staticmethod
    def pause_subscription(db: Session, subscription_id: int) -> Subscription | None:
        """Pause an active subscription."""
        sub = SubscriptionService.get_subscription(db, subscription_id)
        if not sub:
            return None
        if not SubscriptionService._can_transition(sub.status, "paused"):
            raise ValueError(
                f"Cannot transition from {sub.status} to paused"
            )
        sub.status = "paused"
        db.add(BillingEvent(
            event_type="subscription_paused",
            subscription_id=sub.id,
        ))
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def resume_subscription(db: Session, subscription_id: int) -> Subscription | None:
        """Resume a paused subscription."""
        sub = SubscriptionService.get_subscription(db, subscription_id)
        if not sub:
            return None
        if not SubscriptionService._can_transition(sub.status, "active"):
            raise ValueError(
                f"Cannot transition from {sub.status} to active"
            )
        sub.status = "active"
        db.add(BillingEvent(
            event_type="subscription_resumed",
            subscription_id=sub.id,
        ))
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def cancel_subscription(
        db: Session, subscription_id: int, immediate: bool = True
    ) -> Subscription | None:
        """Cancel a subscription."""
        sub = SubscriptionService.get_subscription(db, subscription_id)
        if not sub:
            return None
        if not SubscriptionService._can_transition(sub.status, "canceled"):
            raise ValueError(
                f"Cannot transition from {sub.status} to canceled"
            )
        now = Clock.now()
        sub.status = "canceled"
        sub.canceled_at = now
        db.add(BillingEvent(
            event_type="subscription_canceled",
            subscription_id=sub.id,
            details={"immediate": immediate},
        ))
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def change_plan(
        db: Session,
        subscription_id: int,
        new_plan_id: int,
        change_type: str = "next_cycle",
    ) -> Subscription | None:
        """Change the plan for a subscription."""
        sub = SubscriptionService.get_subscription(db, subscription_id)
        if not sub:
            return None

        new_plan = db.query(Plan).filter(Plan.id == new_plan_id).first()
        if not new_plan:
            raise ValueError(f"Plan {new_plan_id} not found")
        if new_plan.status != "active":
            raise ValueError("Cannot change to a retired plan")

        now = Clock.now()
        change = PlanChangeHistory(
            subscription_id=sub.id,
            old_plan_id=sub.plan_id,
            new_plan_id=new_plan_id,
            effective_at=now if change_type == "immediate" else sub.current_period_end,
            change_type=change_type,
        )

        if change_type == "immediate":
            sub.plan_id = new_plan_id
        # For next_cycle, the billing service will apply the change

        db.add(change)
        db.add(BillingEvent(
            event_type="plan_change",
            subscription_id=sub.id,
            details={
                "old_plan_id": sub.plan_id,
                "new_plan_id": new_plan_id,
                "change_type": change_type,
            },
        ))
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def _can_transition(from_status: str, to_status: str) -> bool:
        """Check if a state transition is valid."""
        allowed = VALID_TRANSITIONS.get(from_status, [])
        return to_status in allowed

    @staticmethod
    def count_active_subscriptions(db: Session) -> int:
        """Count active subscriptions."""
        return (
            db.query(Subscription)
            .filter(Subscription.status == "active")
            .count()
        )

    @staticmethod
    def count_subscriptions_by_status(db: Session, status: str) -> int:
        """Count subscriptions by status."""
        return (
            db.query(Subscription)
            .filter(Subscription.status == status)
            .count()
        )

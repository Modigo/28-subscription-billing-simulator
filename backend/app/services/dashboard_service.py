"""Dashboard and reporting service."""

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.billing_event import BillingEvent
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.schemas import (
    BillingEventResponse,
    DashboardSummary,
    InvoiceResponse,
)


class DashboardService:
    """Aggregate metrics for the dashboard."""

    @staticmethod
    def get_summary(db: Session) -> DashboardSummary:
        """Get dashboard summary metrics."""
        total_customers = db.query(Customer).count()
        total_active = (
            db.query(Subscription).filter(Subscription.status == "active").count()
        )
        total_invoices = db.query(Invoice).count()
        paid_invoices = (
            db.query(Invoice).filter(Invoice.status == "paid").count()
        )
        failed_invoices = (
            db.query(Invoice).filter(Invoice.status == "failed").count()
        )
        past_due = (
            db.query(Subscription)
            .filter(Subscription.status == "past_due")
            .count()
        )
        suspended = (
            db.query(Subscription)
            .filter(Subscription.status == "suspended")
            .count()
        )

        # Revenue by currency (paid invoices only)
        revenue_rows = (
            db.query(Invoice.currency, func.sum(Invoice.amount))
            .filter(Invoice.status == "paid")
            .group_by(Invoice.currency)
            .all()
        )
        total_revenue: dict[str, Decimal] = {}
        for currency, amount in revenue_rows:
            total_revenue[currency] = Decimal(str(amount))

        # Recent invoices
        recent_invoices = (
            db.query(Invoice)
            .order_by(Invoice.created_at.desc())
            .limit(10)
            .all()
        )
        invoice_responses = [
            InvoiceResponse.model_validate(inv) for inv in recent_invoices
        ]

        # Recent events
        recent_events = (
            db.query(BillingEvent)
            .order_by(BillingEvent.created_at.desc())
            .limit(10)
            .all()
        )
        event_responses = [
            BillingEventResponse.model_validate(ev) for ev in recent_events
        ]

        return DashboardSummary(
            total_customers=total_customers,
            total_active_subscriptions=total_active,
            total_invoices=total_invoices,
            paid_invoices=paid_invoices,
            failed_invoices=failed_invoices,
            past_due_subscriptions=past_due,
            suspended_subscriptions=suspended,
            total_revenue=total_revenue,
            recent_invoices=invoice_responses,
            recent_events=event_responses,
        )

    @staticmethod
    def get_billing_events(
        db: Session,
        event_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[BillingEvent]:
        """Get billing events with optional filter."""
        query = db.query(BillingEvent)
        if event_type:
            query = query.filter(BillingEvent.event_type == event_type)
        return (
            query.order_by(BillingEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

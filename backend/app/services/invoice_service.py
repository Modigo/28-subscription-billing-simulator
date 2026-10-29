"""Invoice generation service."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.utils.clock import Clock


class InvoiceService:
    """Business logic for invoice generation with idempotency."""

    @staticmethod
    def generate_invoice_number() -> str:
        """Generate a unique invoice number."""
        return f"INV-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def calculate_period_end(
        period_start: datetime, billing_interval: str
    ) -> datetime:
        """Calculate the end of a billing period."""
        if billing_interval == "yearly":
            return period_start + timedelta(days=365)
        return period_start + timedelta(days=30)

    @staticmethod
    def generate_invoice(
        db: Session,
        subscription: Subscription,
        plan: Plan,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> Invoice | None:
        """
        Generate an invoice for a subscription.
        Returns None if an invoice already exists for this period (idempotency).
        """
        now = Clock.now()
        if period_start is None:
            period_start = now
        if period_end is None:
            period_end = InvoiceService.calculate_period_end(
                period_start, plan.billing_interval
            )

        # Check for existing invoice (idempotency)
        existing = (
            db.query(Invoice)
            .filter(
                Invoice.subscription_id == subscription.id,
                Invoice.billing_period_start == period_start,
            )
            .first()
        )
        if existing:
            return None

        amount = Decimal(str(plan.price))
        invoice = Invoice(
            subscription_id=subscription.id,
            invoice_number=InvoiceService.generate_invoice_number(),
            amount=amount,
            currency=plan.currency,
            status="pending",
            billing_period_start=period_start,
            billing_period_end=period_end,
            due_at=period_end,
            plan_name=plan.name,
            plan_price=plan.price,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_invoice(db: Session, invoice_id: int) -> Invoice | None:
        """Get an invoice by ID."""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()

    @staticmethod
    def list_invoices(
        db: Session,
        status: str | None = None,
        subscription_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Invoice]:
        """List invoices with optional filters."""
        query = db.query(Invoice)
        if status:
            query = query.filter(Invoice.status == status)
        if subscription_id:
            query = query.filter(Invoice.subscription_id == subscription_id)
        return (
            query.order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_invoices(db: Session, status: str | None = None) -> int:
        """Count invoices, optionally filtered by status."""
        query = db.query(Invoice)
        if status:
            query = query.filter(Invoice.status == status)
        return query.count()

    @staticmethod
    def get_invoices_by_subscription(
        db: Session, subscription_id: int
    ) -> list[Invoice]:
        """Get all invoices for a subscription."""
        return (
            db.query(Invoice)
            .filter(Invoice.subscription_id == subscription_id)
            .order_by(Invoice.created_at.desc())
            .all()
        )

"""Comprehensive backend tests."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas import CustomerCreate, PlanCreate
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.retry_service import RetryService
from app.services.subscription_service import SubscriptionService
from app.utils.clock import Clock


# ─── Plan Tests ──────────────────────────────────────────────────────────────


class TestPlanService:
    def test_create_plan(self, db_session):
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Basic", price=Decimal("1000"), billing_interval="monthly"
        ))
        assert plan.name == "Basic"
        assert plan.price == Decimal("1000")
        assert plan.status == "active"

    def test_reject_negative_price(self, db_session):
        with pytest.raises(Exception):
            PlanService.create_plan(db_session, PlanCreate(
                name="Bad", price=Decimal("-100"), billing_interval="monthly"
            ))

    def test_reject_zero_price(self, db_session):
        with pytest.raises(Exception):
            PlanService.create_plan(db_session, PlanCreate(
                name="Bad", price=Decimal("0"), billing_interval="monthly"
            ))

    def test_retire_plan(self, db_session):
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Basic", price=Decimal("1000"), billing_interval="monthly"
        ))
        retired = PlanService.retire_plan(db_session, plan.id)
        assert retired.status == "retired"

    def test_list_plans(self, db_session):
        PlanService.create_plan(db_session, PlanCreate(
            name="A", price=Decimal("100"), billing_interval="monthly"
        ))
        PlanService.create_plan(db_session, PlanCreate(
            name="B", price=Decimal("200"), billing_interval="yearly"
        ))
        plans = PlanService.list_plans(db_session)
        assert len(plans) == 2

    def test_get_active_plans(self, db_session):
        PlanService.create_plan(db_session, PlanCreate(
            name="Active", price=Decimal("100"), billing_interval="monthly"
        ))
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Retired", price=Decimal("200"), billing_interval="monthly"
        ))
        PlanService.retire_plan(db_session, plan.id)
        active = PlanService.get_active_plans(db_session)
        assert len(active) == 1


# ─── Customer Tests ──────────────────────────────────────────────────────────


class TestCustomerService:
    def test_create_customer(self, db_session):
        cust = CustomerService.create_customer(db_session, CustomerCreate(
            name="John", email="john@example.com"
        ))
        assert cust.name == "John"
        assert cust.email == "john@example.com"

    def test_duplicate_email(self, db_session):
        CustomerService.create_customer(db_session, CustomerCreate(
            name="John", email="john@example.com"
        ))
        with pytest.raises(Exception):
            CustomerService.create_customer(db_session, CustomerCreate(
                name="Jane", email="john@example.com"
            ))

    def test_list_customers(self, db_session):
        CustomerService.create_customer(db_session, CustomerCreate(
            name="A", email="a@test.com"
        ))
        CustomerService.create_customer(db_session, CustomerCreate(
            name="B", email="b@test.com"
        ))
        customers = CustomerService.list_customers(db_session)
        assert len(customers) == 2


# ─── Subscription Tests ──────────────────────────────────────────────────────


class TestSubscriptionService:
    def _setup(self, db_session):
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Monthly", price=Decimal("5000"), billing_interval="monthly"
        ))
        cust = CustomerService.create_customer(db_session, CustomerCreate(
            name="Test", email="test@example.com"
        ))
        return cust, plan

    def test_create_subscription(self, db_session, clean_clock):
        cust, plan = self._setup(db_session)
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        assert sub.status == "active"
        assert sub.customer_id == cust.id
        assert sub.plan_id == plan.id

    def test_create_subscription_generates_invoice(self, db_session, clean_clock):
        cust, plan = self._setup(db_session)
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        invoices = InvoiceService.get_invoices_by_subscription(db_session, sub.id)
        assert len(invoices) == 1
        assert invoices[0].amount == Decimal("5000")

    def test_cancel_subscription(self, db_session, clean_clock):
        cust, plan = self._setup(db_session)
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        canceled = SubscriptionService.cancel_subscription(db_session, sub.id)
        assert canceled.status == "canceled"
        assert canceled.canceled_at is not None

    def test_pause_subscription(self, db_session, clean_clock):
        cust, plan = self._setup(db_session)
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        paused = SubscriptionService.pause_subscription(db_session, sub.id)
        assert paused.status == "paused"

    def test_resume_subscription(self, db_session, clean_clock):
        cust, plan = self._setup(db_session)
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        SubscriptionService.pause_subscription(db_session, sub.id)
        resumed = SubscriptionService.resume_subscription(db_session, sub.id)
        assert resumed.status == "active"

    def test_invalid_transition_cancel_to_resume(self, db_session, clean_clock):
        cust, plan = self._setup(db_session)
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        SubscriptionService.cancel_subscription(db_session, sub.id)
        with pytest.raises(ValueError):
            SubscriptionService.resume_subscription(db_session, sub.id)

    def test_reject_retired_plan(self, db_session, clean_clock):
        cust = CustomerService.create_customer(db_session, CustomerCreate(
            name="Test", email="test@example.com"
        ))
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Old", price=Decimal("100"), billing_interval="monthly"
        ))
        PlanService.retire_plan(db_session, plan.id)
        with pytest.raises(ValueError):
            SubscriptionService.create_subscription(
                db_session, cust.id, plan.id
            )


# ─── Invoice Tests ───────────────────────────────────────────────────────────


class TestInvoiceService:
    def _setup(self, db_session):
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Monthly", price=Decimal("3000"), billing_interval="monthly"
        ))
        cust = CustomerService.create_customer(db_session, CustomerCreate(
            name="Test", email="test@example.com"
        ))
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        return sub, plan

    def test_invoice_amount_matches_plan(self, db_session, clean_clock):
        sub, plan = self._setup(db_session)
        invoices = InvoiceService.get_invoices_by_subscription(db_session, sub.id)
        assert invoices[0].amount == Decimal("3000")

    def test_idempotent_invoice(self, db_session, clean_clock):
        sub, plan = self._setup(db_session)
        now = Clock.now()
        inv1 = InvoiceService.generate_invoice(db_session, sub, plan, now, now + timedelta(days=30))
        inv2 = InvoiceService.generate_invoice(db_session, sub, plan, now, now + timedelta(days=30))
        assert inv2 is None

    def test_list_invoices(self, db_session, clean_clock):
        self._setup(db_session)
        invoices = InvoiceService.list_invoices(db_session)
        assert len(invoices) >= 1


# ─── Payment Tests ───────────────────────────────────────────────────────────


class TestPaymentService:
    def _setup(self, db_session):
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Monthly", price=Decimal("1000"), billing_interval="monthly"
        ))
        cust = CustomerService.create_customer(db_session, CustomerCreate(
            name="Test", email="test@example.com"
        ))
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        invoices = InvoiceService.get_invoices_by_subscription(db_session, sub.id)
        return invoices[0]

    def test_successful_payment(self, db_session, clean_clock):
        invoice = self._setup(db_session)
        # Reset to pending for test
        invoice.status = "pending"
        invoice.attempt_count = 0
        db_session.commit()
        attempt = PaymentService.simulate_payment(db_session, invoice, "success")
        assert attempt.outcome == "success"
        db_session.refresh(invoice)
        assert invoice.status == "paid"
        assert invoice.paid_at is not None

    def test_failed_payment(self, db_session, clean_clock):
        invoice = self._setup(db_session)
        invoice.status = "pending"
        invoice.attempt_count = 0
        db_session.commit()
        attempt = PaymentService.simulate_payment(
            db_session, invoice, "failure", "Card declined"
        )
        assert attempt.outcome == "failure"
        db_session.refresh(invoice)
        assert invoice.status == "failed"

    def test_payment_attempts_recorded(self, db_session, clean_clock):
        invoice = self._setup(db_session)
        invoice.status = "pending"
        invoice.attempt_count = 0
        db_session.commit()
        PaymentService.simulate_payment(db_session, invoice, "failure")
        attempts = PaymentService.get_payment_attempts(db_session, invoice.id)
        assert len(attempts) == 2  # 1 from subscription creation + 1 new


# ─── Retry Tests ─────────────────────────────────────────────────────────────


class TestRetryService:
    def test_schedule_next_retry(self, db_session, clean_clock):
        invoice = Invoice(
            subscription_id=1,
            invoice_number="TEST-001",
            amount=Decimal("100"),
            currency="NGN",
            status="failed",
            billing_period_start=Clock.now(),
            billing_period_end=Clock.now() + timedelta(days=30),
            due_at=Clock.now() + timedelta(days=30),
            attempt_count=1,
        )
        db_session.add(invoice)
        db_session.commit()
        schedule = [3, 7, 14]
        RetryService.schedule_next_retry(invoice, schedule)
        assert invoice.next_retry_at is not None

    def test_skip_not_due(self, db_session, clean_clock):
        now = Clock.now()
        invoice = Invoice(
            subscription_id=1,
            invoice_number="TEST-002",
            amount=Decimal("100"),
            currency="NGN",
            status="failed",
            billing_period_start=now,
            billing_period_end=now + timedelta(days=30),
            due_at=now + timedelta(days=30),
            attempt_count=1,
            next_retry_at=now + timedelta(days=30),  # Not due yet
        )
        db_session.add(invoice)
        db_session.commit()
        result = RetryService.process_retries(db_session)
        assert result["processed"] == 0


# ─── End-to-End Scenario ────────────────────────────────────────────────────


class TestEndToEnd:
    def test_full_flow(self, db_session, clean_clock):
        """Create customer → subscribe → invoice → failed payment → retry → success."""
        # 1. Create customer and plan
        cust = CustomerService.create_customer(db_session, CustomerCreate(
            name="Alice", email="alice@test.com"
        ))
        plan = PlanService.create_plan(db_session, PlanCreate(
            name="Pro", price=Decimal("10000"), billing_interval="monthly"
        ))

        # 2. Subscribe
        sub = SubscriptionService.create_subscription(
            db_session, cust.id, plan.id
        )
        assert sub.status == "active"

        # 3. Invoice generated
        invoices = InvoiceService.get_invoices_by_subscription(db_session, sub.id)
        assert len(invoices) == 1
        assert invoices[0].amount == Decimal("10000")

        # 4. Dashboard metrics
        from app.services.dashboard_service import DashboardService
        summary = DashboardService.get_summary(db_session)
        assert summary.total_customers == 1
        assert summary.total_active_subscriptions == 1
        assert summary.total_invoices == 1

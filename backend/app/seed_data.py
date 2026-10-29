"""Seed data script for demonstrations.

Run: cd backend && python -m app.seed_data
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from decimal import Decimal
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.schemas import CustomerCreate, PlanCreate
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.retry_service import RetryService
from app.services.subscription_service import SubscriptionService
from app.utils.clock import Clock


def seed(db: Session):
    """Seed demo data idempotently."""
    now = Clock.now()

    # Check if already seeded
    if CustomerService.count_customers(db) > 0:
        print("Database already has data. Skipping seed.")
        return

    print("Seeding demo data...")

    # Plans
    plans = []
    for name, price, interval, trial in [
        ("Starter", Decimal("5000"), "monthly", 0),
        ("Professional", Decimal("15000"), "monthly", 7),
        ("Enterprise", Decimal("50000"), "yearly", 0),
    ]:
        plan = PlanService.create_plan(db, PlanCreate(
            name=name,
            description=f"{name} plan for demo purposes",
            price=price,
            currency="NGN",
            billing_interval=interval,
            trial_days=trial,
        ))
        plans.append(plan)
        print(f"  Created plan: {plan.name}")

    # Customers
    customers = []
    for name, email in [
        ("Alice Johnson", "alice@demo.com"),
        ("Bob Smith", "bob@demo.com"),
        ("Carol Williams", "carol@demo.com"),
    ]:
        cust = CustomerService.create_customer(db, CustomerCreate(
            name=name, email=email
        ))
        customers.append(cust)
        print(f"  Created customer: {cust.name}")

    # Subscriptions
    # Alice → Starter (no trial, paid)
    sub1 = SubscriptionService.create_subscription(db, customers[0].id, plans[0].id)
    print(f"  Created subscription: Alice → Starter")

    # Bob → Professional (7-day trial)
    sub2 = SubscriptionService.create_subscription(db, customers[1].id, plans[1].id)
    print(f"  Created subscription: Bob → Professional (trialing)")

    # Carol → Starter (simulate failed payment)
    # Create subscription, then manually fail the invoice
    sub3 = SubscriptionService.create_subscription(db, customers[2].id, plans[0].id)
    invoices = InvoiceService.get_invoices_by_subscription(db, sub3.id)
    if invoices:
        inv = invoices[0]
        # Reset and simulate failure
        inv.status = "pending"
        inv.attempt_count = 0
        db.commit()
        PaymentService.simulate_payment(db, inv, "failure", "Simulated card decline")
        retry_schedule = [3, 7, 14]
        RetryService.schedule_next_retry(inv, retry_schedule)
        db.commit()
        print(f"  Created subscription: Carol → Starter (payment failed, retry scheduled)")

    print("Seed complete!")


if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()

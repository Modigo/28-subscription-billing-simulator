from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.models import Customer, Plan, Subscription
from app.subscriptions import create_subscription, cancel_subscription, get_subscriptions
from app.schemas import SubscriptionCreate, SubscriptionOut

from app.database import get_db, init_db
from app.invoice import generate_invoice, get_invoices
from app.payments import process_payment, process_due_retries
from app.schemas import InvoiceOut
from app.models import Customer, Plan
from app.plans import create_plan, get_plans
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    PlanCreate,
    PlanOut,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Subscription Billing Simulator API",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"message": "Subscription Billing Simulator API is running!"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# CUSTOMER ENDPOINTS

@app.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.id).all()


@app.post("/customers", response_model=CustomerOut, status_code=201)
def add_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    existing_customer = (
        db.query(Customer)
        .filter(Customer.email == customer_data.email)
        .first()
    )

    if existing_customer:
        raise HTTPException(
            status_code=409,
            detail="A customer with this email already exists.",
        )

    customer = Customer(
        name=customer_data.name.strip(),
        email=str(customer_data.email),
    )

    if not customer.name:
        raise HTTPException(
            status_code=422,
            detail="Customer name cannot be empty.",
        )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# PLAN ENDPOINTS

@app.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return get_plans(db)


@app.post("/plans", response_model=PlanOut, status_code=201)
def add_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_plan(
            db=db,
            name=plan_data.name,
            price_kobo=plan_data.price_kobo,
            billing_interval=plan_data.billing_interval,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    # SUBSCRIPTION ENDPOINTS

@app.get("/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(db: Session = Depends(get_db)):
    return get_subscriptions(db)


@app.post("/subscriptions", response_model=SubscriptionOut, status_code=201)
def add_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_subscription(
            db=db,
            customer_id=subscription_data.customer_id,
            plan_id=subscription_data.plan_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    

    # PAYMENT ENDPOINTS

@app.post("/invoices/{invoice_id}/payments")
def simulate_payment(
    invoice_id: int,
    succeed: bool,
    message: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        attempt = process_payment(
            db=db,
            invoice_id=invoice_id,
            succeed=succeed,
            message=message,
        )
        return {
            "message": "Payment attempt recorded.",
            "invoice_id": invoice_id,
            "attempt_number": attempt.attempt_number,
            "status": attempt.status,
            "details": attempt.message,
        }
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error



@app.get("/payment-retries/due")
def list_due_payment_retries(db: Session = Depends(get_db)):
    return process_due_retries(db)


@app.post(
    "/subscriptions/{subscription_id}/cancel",
    response_model=SubscriptionOut,
)
def cancel_existing_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    try:
        return cancel_subscription(db, subscription_id)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    
# INVOICE ENDPOINTS

@app.get("/invoices", response_model=list[InvoiceOut])
def list_all_invoices(db: Session = Depends(get_db)):
    return get_invoices(db)


@app.get(
    "/subscriptions/{subscription_id}/invoices",
    response_model=list[InvoiceOut],
)
def list_subscription_invoices(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    subscription = db.get(Subscription, subscription_id)

    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    return get_invoices(db, subscription_id=subscription_id)


@app.post(
    "/subscriptions/{subscription_id}/invoices",
    response_model=InvoiceOut,
    status_code=201,
)
def create_subscription_invoice(
    subscription_id: int,
    db: Session = Depends(get_db),
):
    subscription = db.get(Subscription, subscription_id)

    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    try:
        return generate_invoice(
            db=db,
            subscription_id=subscription.id,
            plan_price_kobo=subscription.plan.price_kobo,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end,
            issue_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=7),
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
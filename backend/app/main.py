"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    billing,
    customers,
    dashboard,
    invoices,
    plans,
    subscriptions,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Subscription Billing Simulator",
    description="MVP for recurring subscription billing without real payments",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(plans.router, prefix="/api/v1", tags=["Plans"])
app.include_router(customers.router, prefix="/api/v1", tags=["Customers"])
app.include_router(subscriptions.router, prefix="/api/v1", tags=["Subscriptions"])
app.include_router(invoices.router, prefix="/api/v1", tags=["Invoices"])
app.include_router(billing.router, prefix="/api/v1", tags=["Billing"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])


@app.get("/health")
def health_check():
    return {"status": "ok", "demo_mode": settings.DEMO_MODE}

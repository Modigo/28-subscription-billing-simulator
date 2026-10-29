"""Billing operations API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import BillingRunResult, RetryRunResult
from app.services.billing_service import BillingService
from app.services.retry_service import RetryService

router = APIRouter()


@router.post("/billing/run", response_model=BillingRunResult)
def run_billing_scheduler(db: Session = Depends(get_db)):
    """Manually trigger the billing scheduler."""
    result = BillingService.run_billing_cycle(db)
    return BillingRunResult(
        processed=result["processed"],
        invoices_created=result["invoices_created"],
        errors=result["errors"],
    )


@router.post("/retries/run", response_model=RetryRunResult)
def run_retry_processor(db: Session = Depends(get_db)):
    """Manually trigger the retry processor."""
    result = RetryService.process_retries(db)
    return RetryRunResult(
        processed=result["processed"],
        succeeded=result["succeeded"],
        failed=result["failed"],
        errors=result["errors"],
    )

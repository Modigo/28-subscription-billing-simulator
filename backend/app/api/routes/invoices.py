"""Invoices API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    InvoiceListResponse,
    InvoiceResponse,
    PaymentAttemptResponse,
    SimulatePaymentRequest,
)
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.services.retry_service import RetryService

router = APIRouter()


@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    status: str | None = Query(None),
    subscription_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    invoices = InvoiceService.list_invoices(
        db, status=status, subscription_id=subscription_id, skip=skip, limit=limit
    )
    total = InvoiceService.count_invoices(db, status=status)
    return InvoiceListResponse(items=invoices, total=total)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post(
    "/invoices/{invoice_id}/simulate-payment", response_model=PaymentAttemptResponse
)
def simulate_payment(
    invoice_id: int,
    data: SimulatePaymentRequest,
    db: Session = Depends(get_db),
):
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "paid":
        raise HTTPException(
            status_code=409, detail="Invoice is already paid"
        )

    failure_reason = (
        "Simulated payment failure" if data.outcome == "failure" else None
    )
    attempt = PaymentService.simulate_payment(
        db, invoice, data.outcome, failure_reason
    )

    # If payment failed, schedule retry
    if data.outcome == "failure":
        retry_schedule = [3, 7, 14]
        RetryService.schedule_next_retry(invoice, retry_schedule)
        db.commit()

    return attempt


@router.get(
    "/invoices/{invoice_id}/attempts", response_model=list[PaymentAttemptResponse]
)
def get_payment_attempts(invoice_id: int, db: Session = Depends(get_db)):
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    attempts = PaymentService.get_payment_attempts(db, invoice_id)
    return attempts

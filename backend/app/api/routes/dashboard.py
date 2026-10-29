"""Dashboard API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import BillingEventResponse, DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard metrics summary."""
    return DashboardService.get_summary(db)


@router.get("/events", response_model=list[BillingEventResponse])
def get_billing_events(
    event_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get billing event history."""
    events = DashboardService.get_billing_events(
        db, event_type=event_type, skip=skip, limit=limit
    )
    return [BillingEventResponse.model_validate(e) for e in events]

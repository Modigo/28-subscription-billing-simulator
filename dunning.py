# =====================================================================
# SUBSCRIPTION BILLING SIMULATOR - DUNNING & RETRY LOGIC MODULE
# Framework: FastAPI + SQLAlchemy
# =====================================================================

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Invoice, Subscription, InvoiceStatus, SubStatus

# Core Configuration: 3 Retries total (Attempt 1 at 3 days, 2 at 7 days, 3 at 14 days)
RETRY_SCHEDULE = [3, 7, 14]  
MAX_RETRIES = len(RETRY_SCHEDULE)

def get_active_dunning_records(db: Session):
    """
    Queries the database via session to find active payment failures.
    """
    return db.query(Invoice).filter(
        Invoice.status.in_([InvoiceStatus.FAILED, InvoiceStatus.RETRYING])
    ).all()

def execute_system_dunning_sweep(db: Session):
    """
    Automated recovery sweep engine. Loops through failed invoices,
    calculates timeline increments, and suspends account profiles
    when the maximum retry threshold is exhausted.
    """
    records = get_active_dunning_records(db)
    
    if not records:
        return {"status": "Success", "message": "No invoices require dunning recovery processing."}
    
    actions_taken = []
    
    for invoice in records:
        invoice.retry_count += 1
        
        if invoice.retry_count >= MAX_RETRIES:
            invoice.status = InvoiceStatus.SUSPENDED
            invoice.next_retry_date = None
            
            if invoice.subscription:
                invoice.subscription.status = SubStatus.SUSPENDED
                
            actions_taken.append(f"Suspended account for {invoice.customer_name} due to exhausted retries.")
        else:
            next_days_delta = RETRY_SCHEDULE[invoice.retry_count]
            invoice.status = InvoiceStatus.RETRYING
            invoice.next_retry_date = datetime.now() + timedelta(days=next_days_delta)
            
            actions_taken.append(
                f"Executed retry #{invoice.retry_count} for {invoice.customer_name}. Next window: {invoice.next_retry_date.strftime('%Y-%m-%d')}"
            )
            
    db.commit()
    return {"status": "Sweep Completed", "actions": actions_taken}

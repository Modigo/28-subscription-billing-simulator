# =====================================================================
# PYTEST SUITE - AUTOMATED DUNNING RETRY ENGINE TESTING
# File: test_dunning.py
# =====================================================================

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
import dunning

@pytest.fixture
def db_session():
    """
    Sets up a clean, isolated in-memory SQLite database.
    This database runs completely inside RAM and vanishes after the test ends.
    """
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_dunning_sweep_empty_queue(db_session):
    """
    Test Case 1: Verifies the engine handles an empty queue gracefully.
    """
    result = dunning.execute_system_dunning_sweep(db_session)
    assert result["status"] == "Success"
    assert "No invoices require" in result["message"]

def test_dunning_cycle_progression(db_session):
    """
    Test Case 2: Verifies that a failed invoice progresses correctly
    through the 3, 7, and 14 day retry schedule blocks.
    """
    # 1. Create mock plan and subscription models to satisfy foreign key constraints
    mock_plan = models.Plan(name="Test Tier", price=10.0)
    db_session.add(mock_plan)
    db_session.commit()

    mock_sub = models.Subscription(
        customer_name="Test User", 
        plan_id=mock_plan.id, 
        next_billing_date=datetime.now()
    )
    db_session.add(mock_sub)
    db_session.commit()

    # 2. Add an initial failed invoice mimicking Member 3's output
    mock_invoice = models.Invoice(
        subscription_id=mock_sub.id,
        customer_name="Test User",
        amount_due=10.0,
        retry_count=0,
        status=models.InvoiceStatus.FAILED
    )
    db_session.add(mock_invoice)
    db_session.commit()

    # --- SWEEP 1 ---
    # Should advance retry_count to 1 and change status to RETRYING
    sweep_1 = dunning.execute_system_dunning_sweep(db_session)
    assert mock_invoice.retry_count == 1
    assert mock_invoice.status == models.InvoiceStatus.RETRYING
    assert mock_invoice.next_retry_date is not None

    # --- SWEEP 2 ---
    # Should advance retry_count to 2
    sweep_2 = dunning.execute_system_dunning_sweep(db_session)
    assert mock_invoice.retry_count == 2
    assert mock_invoice.status == models.InvoiceStatus.RETRYING

    # --- SWEEP 3 (MAX EXHAUSTION) ---
    # Should hit MAX_RETRIES (3) and flip status to SUSPENDED on both Invoice and Subscription
    sweep_3 = dunning.execute_system_dunning_sweep(db_session)
    assert mock_invoice.retry_count == 3
    assert mock_invoice.status == models.InvoiceStatus.SUSPENDED
    assert mock_sub.status == models.SubStatus.SUSPENDED

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import models  # noqa


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    Base.metadata.create_all(engine)

    Session = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = Session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()

def test_paid_invoice_is_excluded_from_due_retries(db):
    # Create a test subscription and invoice.
    subscription, invoice, now = create_invoice_data(db)

    # First, simulate a failed payment.
    process_payment(
        db,
        invoice.id,
        succeed=False,
        now=now,
    )

    # Then, simulate a successful payment.
    process_payment(
        db,
        invoice.id,
        succeed=True,
        now=now + timedelta(hours=1),
    )

    # Check for retries after the original retry becomes due.
    due_time = now + timedelta(days=4)

    results = process_due_retries(
        db,
        now=due_time,
    )

    # The paid invoice must not appear in the retry list.
    assert all(
        retry.invoice_id != invoice.id
        for retry in results
    )

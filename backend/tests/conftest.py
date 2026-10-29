"""Test fixtures for database isolation."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.utils.clock import Clock


@pytest.fixture
def db_session():
    """Provide an in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def clean_clock():
    """Reset clock before and after each test."""
    Clock.reset()
    yield
    Clock.reset()

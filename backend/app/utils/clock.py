"""Injectable clock for testable time simulation."""

from datetime import datetime, timezone


class Clock:
    """Clock abstraction that can be overridden in tests."""

    _override: datetime | None = None

    @classmethod
    def now(cls) -> datetime:
        """Return the current UTC time, or an overridden time for tests."""
        if cls._override is not None:
            return cls._override
        return datetime.now(timezone.utc)

    @classmethod
    def set_time(cls, dt: datetime) -> None:
        """Override the current time for testing."""
        cls._override = dt

    @classmethod
    def reset(cls) -> None:
        """Reset to real time."""
        cls._override = None


# Module-level convenience
now = Clock.now

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    """Shared audit timestamps for knowledge base entities."""

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": utcnow},
    )

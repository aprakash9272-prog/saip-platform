from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.capability import Capability


class DomainBase(SQLModel):
    name: str = Field(max_length=255, index=True, unique=True)
    description: Optional[str] = Field(default=None)


class Domain(DomainBase, TimestampMixin, table=True):
    """A security domain in the capability taxonomy (e.g. Endpoint Security)."""

    __tablename__ = "domain"

    id: Optional[int] = Field(default=None, primary_key=True)

    capabilities: list["Capability"] = Relationship(back_populates="domain")

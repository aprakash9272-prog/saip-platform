from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer


class EnvironmentType(str, Enum):
    PRODUCTION = "Production"
    UAT = "UAT"
    DEVELOPMENT = "Development"
    DR = "DR"
    OT = "OT"


class EnvironmentBase(SQLModel):
    name: str = Field(max_length=255)
    environment_type: str = Field(max_length=50)
    description: Optional[str] = Field(default=None)


class Environment(EnvironmentBase, TimestampMixin, table=True):
    __tablename__ = "environment"
    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_environment_customer_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", nullable=False, index=True)

    customer: "Customer" = Relationship(back_populates="environments")

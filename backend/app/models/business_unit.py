from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer


class BusinessUnitBase(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)


class BusinessUnit(BusinessUnitBase, TimestampMixin, table=True):
    __tablename__ = "business_unit"
    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_business_unit_customer_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", nullable=False, index=True)

    customer: "Customer" = Relationship(back_populates="business_units")

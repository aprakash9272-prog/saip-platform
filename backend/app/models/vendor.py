from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class VendorBase(SQLModel):
    name: str = Field(max_length=255, index=True, unique=True)
    website: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    headquarters: Optional[str] = Field(default=None, max_length=255)


class Vendor(VendorBase, TimestampMixin, table=True):
    __tablename__ = "vendor"

    id: Optional[int] = Field(default=None, primary_key=True)

    products: list["Product"] = Relationship(
        back_populates="vendor",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

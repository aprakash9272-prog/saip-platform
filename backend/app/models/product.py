from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.edition import Edition
    from app.models.vendor import Vendor


class ProductBase(SQLModel):
    name: str = Field(max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None, max_length=500)


class Product(ProductBase, TimestampMixin, table=True):
    __tablename__ = "product"
    __table_args__ = (
        UniqueConstraint("vendor_id", "name", name="uq_product_vendor_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", nullable=False, index=True)

    vendor: "Vendor" = Relationship(back_populates="products")
    editions: list["Edition"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

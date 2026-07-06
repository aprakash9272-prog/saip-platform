from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.module import Module
    from app.models.product import Product


class EditionBase(SQLModel):
    name: str = Field(max_length=255)
    tier: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None)


class Edition(EditionBase, TimestampMixin, table=True):
    __tablename__ = "edition"
    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_edition_product_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", nullable=False, index=True)

    product: "Product" = Relationship(back_populates="editions")
    modules: list["Module"] = Relationship(
        back_populates="edition",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

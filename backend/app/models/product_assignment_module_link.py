from typing import Optional

from sqlmodel import Field, SQLModel


class ProductAssignmentModuleLink(SQLModel, table=True):
    """Association table: which modules are enabled for a product assignment."""

    __tablename__ = "product_assignment_module_link"

    assignment_id: Optional[int] = Field(
        default=None, foreign_key="product_assignment.id", primary_key=True
    )
    module_id: Optional[int] = Field(
        default=None, foreign_key="module.id", primary_key=True
    )

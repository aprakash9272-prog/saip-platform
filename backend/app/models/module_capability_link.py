from typing import Optional

from sqlmodel import Field, SQLModel


class ModuleCapabilityLink(SQLModel, table=True):
    """Association table: which capabilities a module provides."""

    __tablename__ = "module_capability_link"

    module_id: Optional[int] = Field(
        default=None, foreign_key="module.id", primary_key=True
    )
    capability_id: Optional[int] = Field(
        default=None, foreign_key="capability.id", primary_key=True
    )

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin
from app.models.module_capability_link import ModuleCapabilityLink

if TYPE_CHECKING:
    from app.models.capability import Capability
    from app.models.edition import Edition


class ModuleBase(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)


class Module(ModuleBase, TimestampMixin, table=True):
    __tablename__ = "module"
    __table_args__ = (
        UniqueConstraint("edition_id", "name", name="uq_module_edition_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    edition_id: int = Field(foreign_key="edition.id", nullable=False, index=True)

    edition: "Edition" = Relationship(back_populates="modules")
    capabilities: list["Capability"] = Relationship(
        back_populates="modules",
        link_model=ModuleCapabilityLink,
    )

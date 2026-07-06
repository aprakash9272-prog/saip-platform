from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampMixin
from app.models.module_capability_link import ModuleCapabilityLink

if TYPE_CHECKING:
    from app.models.domain import Domain
    from app.models.framework_mapping import FrameworkMapping
    from app.models.module import Module


class CapabilityBase(SQLModel):
    name: str = Field(max_length=255)
    code: str = Field(max_length=100, index=True, unique=True)
    description: Optional[str] = Field(default=None)
    risk_category: Optional[str] = Field(default=None, max_length=100)


class Capability(CapabilityBase, TimestampMixin, table=True):
    __tablename__ = "capability"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain_id: int = Field(foreign_key="domain.id", nullable=False, index=True)

    domain: "Domain" = Relationship(back_populates="capabilities")
    modules: list["Module"] = Relationship(
        back_populates="capabilities",
        link_model=ModuleCapabilityLink,
    )
    framework_mappings: list["FrameworkMapping"] = Relationship(
        back_populates="capability",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

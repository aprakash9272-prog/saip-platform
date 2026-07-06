from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.capability import Capability
    from app.models.framework import Framework


class FrameworkMappingBase(SQLModel):
    control_id: str = Field(max_length=100)
    control_name: str = Field(max_length=500)


class FrameworkMapping(FrameworkMappingBase, TimestampMixin, table=True):
    __tablename__ = "framework_mapping"
    __table_args__ = (
        UniqueConstraint(
            "capability_id",
            "framework_id",
            "control_id",
            name="uq_mapping_capability_framework_control",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    capability_id: int = Field(foreign_key="capability.id", nullable=False, index=True)
    framework_id: int = Field(foreign_key="framework.id", nullable=False, index=True)

    capability: "Capability" = Relationship(back_populates="framework_mappings")
    framework: "Framework" = Relationship(back_populates="mappings")

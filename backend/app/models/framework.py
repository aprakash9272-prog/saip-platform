from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.framework_mapping import FrameworkMapping


class FrameworkBase(SQLModel):
    name: str = Field(max_length=255)
    version: str = Field(max_length=50)


class Framework(FrameworkBase, TimestampMixin, table=True):
    __tablename__ = "framework"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_framework_name_version"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    mappings: list["FrameworkMapping"] = Relationship(
        back_populates="framework",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

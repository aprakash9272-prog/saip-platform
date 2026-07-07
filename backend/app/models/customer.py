from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.assessment_project import AssessmentProject
    from app.models.business_unit import BusinessUnit
    from app.models.environment import Environment


class CustomerBase(SQLModel):
    name: str = Field(max_length=255, index=True, unique=True)
    industry: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None, max_length=500)
    headquarters: Optional[str] = Field(default=None, max_length=255)


class Customer(CustomerBase, TimestampMixin, table=True):
    """A customer organization whose security environment is being assessed."""

    __tablename__ = "customer"

    id: Optional[int] = Field(default=None, primary_key=True)

    business_units: List["BusinessUnit"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    environments: List["Environment"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    assessment_projects: List["AssessmentProject"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product_assignment import ProductAssignment


class AssessmentStatus(str, Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class AssessmentProjectBase(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    status: str = Field(default=AssessmentStatus.DRAFT.value, max_length=50)
    start_date: Optional[date] = Field(default=None)
    target_completion_date: Optional[date] = Field(default=None)


class AssessmentProject(AssessmentProjectBase, TimestampMixin, table=True):
    __tablename__ = "assessment_project"
    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_assessment_project_customer_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", nullable=False, index=True)

    customer: "Customer" = Relationship(back_populates="assessment_projects")
    product_assignments: List["ProductAssignment"] = Relationship(
        back_populates="assessment_project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

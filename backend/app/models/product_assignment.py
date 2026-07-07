from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin
from app.models.product_assignment_module_link import ProductAssignmentModuleLink

if TYPE_CHECKING:
    from app.models.assessment_project import AssessmentProject
    from app.models.edition import Edition
    from app.models.environment import Environment
    from app.models.module import Module
    from app.models.product import Product
    from app.models.vendor import Vendor


class DeploymentStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    DEPLOYED = "Deployed"
    DECOMMISSIONED = "Decommissioned"


class ProductAssignmentBase(SQLModel):
    license_quantity: Optional[int] = Field(default=None)
    deployment_model: str = Field(max_length=50)
    deployment_status: str = Field(default=DeploymentStatus.NOT_STARTED.value, max_length=50)
    notes: Optional[str] = Field(default=None)


class ProductAssignment(ProductAssignmentBase, TimestampMixin, table=True):
    """Assigns an existing knowledge-base product edition to an assessment
    project's environment. References Vendor/Product/Edition/Module rows
    from the Sprint 3-5 knowledge base rather than duplicating them."""

    __tablename__ = "product_assignment"
    __table_args__ = (
        UniqueConstraint(
            "assessment_project_id",
            "edition_id",
            "environment_id",
            name="uq_assignment_project_edition_environment",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_project_id: int = Field(
        foreign_key="assessment_project.id", nullable=False, index=True
    )
    vendor_id: int = Field(foreign_key="vendor.id", nullable=False, index=True)
    product_id: int = Field(foreign_key="product.id", nullable=False, index=True)
    edition_id: int = Field(foreign_key="edition.id", nullable=False, index=True)
    environment_id: int = Field(foreign_key="environment.id", nullable=False, index=True)

    assessment_project: "AssessmentProject" = Relationship(
        back_populates="product_assignments"
    )
    vendor: "Vendor" = Relationship()
    product: "Product" = Relationship()
    edition: "Edition" = Relationship()
    environment: "Environment" = Relationship()
    modules: List["Module"] = Relationship(link_model=ProductAssignmentModuleLink)

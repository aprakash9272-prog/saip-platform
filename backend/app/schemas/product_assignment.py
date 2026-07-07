from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel

from app.models.product_assignment import DeploymentStatus, ProductAssignmentBase
from app.models.product_capability_mapping import DeploymentModel


def _validate_deployment_model(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = {item.value for item in DeploymentModel}
    if value not in allowed:
        raise ValueError(f"deployment_model must be one of {sorted(allowed)}")
    return value


def _validate_deployment_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = {item.value for item in DeploymentStatus}
    if value not in allowed:
        raise ValueError(f"deployment_status must be one of {sorted(allowed)}")
    return value


class ProductAssignmentCreate(ProductAssignmentBase):
    assessment_project_id: int
    vendor_id: int
    product_id: int
    edition_id: int
    environment_id: int
    module_ids: List[int] = Field(default_factory=list)

    _check_deployment_model = field_validator("deployment_model")(
        _validate_deployment_model
    )
    _check_deployment_status = field_validator("deployment_status")(
        _validate_deployment_status
    )


class ProductAssignmentUpdate(SQLModel):
    assessment_project_id: Optional[int] = None
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None
    edition_id: Optional[int] = None
    environment_id: Optional[int] = None
    license_quantity: Optional[int] = None
    deployment_model: Optional[str] = None
    deployment_status: Optional[str] = None
    notes: Optional[str] = None
    module_ids: Optional[List[int]] = None

    _check_deployment_model = field_validator("deployment_model")(
        _validate_deployment_model
    )
    _check_deployment_status = field_validator("deployment_status")(
        _validate_deployment_status
    )


class ProductAssignmentRead(ProductAssignmentBase):
    id: int
    assessment_project_id: int
    vendor_id: int
    product_id: int
    edition_id: int
    environment_id: int
    module_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

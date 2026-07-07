from datetime import datetime
from typing import List, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.models.product_capability_mapping import (
    AvailabilityStatus,
    DeploymentModel,
    Platform,
    ProductCapabilityMappingBase,
)


def _validate_deployment_model(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = {item.value for item in DeploymentModel}
    if value not in allowed:
        raise ValueError(f"deployment_model must be one of {sorted(allowed)}")
    return value


def _validate_availability_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = {item.value for item in AvailabilityStatus}
    if value not in allowed:
        raise ValueError(f"availability_status must be one of {sorted(allowed)}")
    return value


def _validate_platforms(value: Optional[List[str]]) -> Optional[List[str]]:
    if value is None:
        return value
    allowed = {item.value for item in Platform}
    invalid = [v for v in value if v not in allowed]
    if invalid:
        raise ValueError(f"supported_platforms contains invalid values {invalid}; allowed: {sorted(allowed)}")
    return value


class ProductCapabilityMappingCreate(ProductCapabilityMappingBase):
    vendor_id: int
    product_id: int
    edition_id: int
    module_id: int
    capability_id: int

    _check_deployment_model = field_validator("deployment_model")(_validate_deployment_model)
    _check_availability_status = field_validator("availability_status")(
        _validate_availability_status
    )
    _check_platforms = field_validator("supported_platforms")(_validate_platforms)


class ProductCapabilityMappingUpdate(SQLModel):
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None
    edition_id: Optional[int] = None
    module_id: Optional[int] = None
    capability_id: Optional[int] = None
    licensing_tier: Optional[str] = None
    supported_platforms: Optional[List[str]] = None
    deployment_model: Optional[str] = None
    availability_status: Optional[str] = None

    _check_deployment_model = field_validator("deployment_model")(_validate_deployment_model)
    _check_availability_status = field_validator("availability_status")(
        _validate_availability_status
    )
    _check_platforms = field_validator("supported_platforms")(_validate_platforms)


class ProductCapabilityMappingRead(ProductCapabilityMappingBase):
    id: int
    vendor_id: int
    product_id: int
    edition_id: int
    module_id: int
    capability_id: int
    created_at: datetime
    updated_at: datetime


class ProductCapabilityMappingBulkUpdate(SQLModel):
    ids: List[int]
    patch: ProductCapabilityMappingUpdate


class ProductCapabilityMappingBulkDelete(SQLModel):
    ids: List[int]


class BulkOperationResult(SQLModel):
    updated: int = 0
    deleted: int = 0
    failed: List[str] = Field(default_factory=list)

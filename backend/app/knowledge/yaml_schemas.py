import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.product_capability_mapping import AvailabilityStatus, DeploymentModel, Platform

CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class VendorYAML(BaseModel):
    name: str = Field(min_length=1)
    website: Optional[str] = None
    description: Optional[str] = None
    headquarters: Optional[str] = None


class ProductYAML(BaseModel):
    name: str = Field(min_length=1)
    vendor: str = Field(min_length=1, description="Vendor name this product belongs to.")
    category: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class EditionYAML(BaseModel):
    name: str = Field(min_length=1)
    vendor: str = Field(min_length=1)
    product: str = Field(min_length=1)
    tier: Optional[str] = None
    description: Optional[str] = None


class ModuleYAML(BaseModel):
    name: str = Field(min_length=1)
    vendor: str = Field(min_length=1)
    product: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    description: Optional[str] = None
    capabilities: List[str] = Field(
        default_factory=list,
        description="Capability codes this module provides.",
    )


class DomainYAML(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None


class CapabilityYAML(BaseModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    domain: str = Field(min_length=1, description="Domain name this capability belongs to.")
    description: Optional[str] = None
    risk_category: Optional[str] = None
    is_business_critical: bool = False

    @field_validator("code")
    @classmethod
    def code_must_be_slug_like(cls, value: str) -> str:
        if not CODE_PATTERN.match(value):
            raise ValueError(
                "code must start with a letter/digit and contain only "
                "letters, digits, '.', '_' or '-'"
            )
        return value


class FrameworkYAML(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class FrameworkMappingYAML(BaseModel):
    capability_code: str = Field(min_length=1)
    framework: str = Field(min_length=1)
    framework_version: str = Field(min_length=1)
    control_id: str = Field(min_length=1)
    control_name: str = Field(min_length=1)


class ProductCapabilityMappingYAML(BaseModel):
    vendor: str = Field(min_length=1)
    product: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    module: str = Field(min_length=1)
    capability_code: str = Field(min_length=1)
    licensing_tier: Optional[str] = None
    supported_platforms: List[str] = Field(default_factory=list)
    deployment_model: str = Field(min_length=1)
    availability_status: str = AvailabilityStatus.GENERALLY_AVAILABLE.value

    @field_validator("deployment_model")
    @classmethod
    def deployment_model_must_be_known(cls, value: str) -> str:
        allowed = {item.value for item in DeploymentModel}
        if value not in allowed:
            raise ValueError(f"deployment_model must be one of {sorted(allowed)}")
        return value

    @field_validator("availability_status")
    @classmethod
    def availability_status_must_be_known(cls, value: str) -> str:
        allowed = {item.value for item in AvailabilityStatus}
        if value not in allowed:
            raise ValueError(f"availability_status must be one of {sorted(allowed)}")
        return value

    @field_validator("supported_platforms")
    @classmethod
    def platforms_must_be_known(cls, value: List[str]) -> List[str]:
        allowed = {item.value for item in Platform}
        invalid = [v for v in value if v not in allowed]
        if invalid:
            raise ValueError(
                f"supported_platforms contains invalid values {invalid}; "
                f"allowed: {sorted(allowed)}"
            )
        return value

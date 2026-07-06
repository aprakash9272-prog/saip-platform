import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

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


class CapabilityYAML(BaseModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    domain: Optional[str] = None
    description: Optional[str] = None
    risk_category: Optional[str] = None

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

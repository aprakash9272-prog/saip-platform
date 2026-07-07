from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CoverageRequest(BaseModel):
    assessment_project_id: int


class CapabilityCoverageItem(BaseModel):
    id: int
    code: str
    name: str
    domain_id: int
    domain_name: str
    covered: bool
    provider_count: int
    providers: List[str] = Field(default_factory=list)


class DuplicateCapabilityItem(BaseModel):
    id: int
    code: str
    name: str
    domain_id: int
    domain_name: str
    provider_count: int
    providers: List[str] = Field(default_factory=list)


class DomainCoverage(BaseModel):
    domain_id: int
    domain_name: str
    covered_count: int
    total_count: int
    coverage_percentage: float


class CapabilityMatrix(BaseModel):
    covered: List[CapabilityCoverageItem]
    missing: List[CapabilityCoverageItem]
    duplicate: List[DuplicateCapabilityItem]


class CoverageReport(BaseModel):
    """Point-in-time coverage calculation for an assessment project.

    Only Product Assignments with deployment_status == "Deployed" count
    towards coverage — a product that is Not Started, In Progress, or
    Decommissioned is not actually protecting the environment today. This
    is a pure calculation: no recommendations, no gap/overlap scoring.
    """

    assessment_project_id: int
    assessment_project_name: str
    generated_at: datetime
    total_capabilities: int
    covered_capability_count: int
    missing_capability_count: int
    duplicate_capability_count: int
    overall_coverage_percentage: float
    domain_coverage: List[DomainCoverage]
    covered_capabilities: List[CapabilityCoverageItem]
    missing_capabilities: List[CapabilityCoverageItem]
    duplicate_capabilities: List[DuplicateCapabilityItem]

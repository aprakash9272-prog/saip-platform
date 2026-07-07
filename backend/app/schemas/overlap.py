from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OverlapRequest(BaseModel):
    assessment_project_id: int


class DuplicateCapabilityOverlap(BaseModel):
    """A capability covered by more than one deployed product."""

    id: int
    code: str
    name: str
    domain_id: int
    domain_name: str
    provider_count: int
    distinct_vendor_count: int
    providers: List[str] = Field(default_factory=list)
    cross_vendor: bool


class ProductOverlapPair(BaseModel):
    """Two deployed products sharing one or more capabilities."""

    vendor_a: str
    product_a: str
    vendor_b: str
    product_b: str
    shared_capability_count: int
    shared_capability_codes: List[str] = Field(default_factory=list)
    overlap_percentage: float


class ModuleOverlapPair(BaseModel):
    """Two enabled modules (possibly from different products) sharing
    capabilities — a finer-grained view than product overlap."""

    vendor_a: str
    product_a: str
    module_a: str
    vendor_b: str
    product_b: str
    module_b: str
    shared_capability_count: int
    shared_capability_codes: List[str] = Field(default_factory=list)


class FrameworkOverlapItem(BaseModel):
    """A compliance framework control redundantly satisfied by more than
    one deployed product."""

    framework_name: str
    framework_version: str
    control_id: str
    control_name: str
    provider_count: int
    providers: List[str] = Field(default_factory=list)


class RedundantLicenseItem(BaseModel):
    """A deployed assignment whose capabilities are wholly or partially
    also provided by other deployed assignments — a license reduction
    candidate."""

    assignment_id: int
    vendor: str
    product: str
    edition: str
    license_quantity: Optional[int] = None
    redundant_capability_count: int
    total_capability_count: int
    redundancy_percentage: float
    fully_redundant: bool


class UnusedCapabilityItem(BaseModel):
    """A capability available under a deployed edition (via a module that
    could be enabled) but not actually enabled in this assignment —
    answers "which capabilities were purchased but never enabled?"."""

    assignment_id: int
    vendor: str
    product: str
    edition: str
    module: str
    capability_code: str
    capability_name: str
    domain_name: str


class VendorOverlapSummary(BaseModel):
    vendor: str
    deployed_product_count: int
    total_capabilities_provided: int
    unique_capabilities_provided: int
    overlapping_capabilities_provided: int
    total_license_quantity: int
    open_gaps_addressable: int


class DomainOverlapScore(BaseModel):
    domain_id: int
    domain_name: str
    covered_count: int
    duplicate_count: int
    overlap_percentage: float


class OverlapSummary(BaseModel):
    assessment_project_id: int
    assessment_project_name: str
    generated_at: datetime
    total_deployed_products: int
    total_vendors: int
    duplicate_capability_count: int
    cross_vendor_duplicate_count: int
    unused_capability_count: int
    overlap_percentage: float
    optimization_score: float
    vendor_consolidation_score: float
    license_reduction_opportunity: int
    cost_optimization_score: float
    operational_complexity_score: float


class OverlapReport(OverlapSummary):
    """Deterministic overlap/optimization analysis for an assessment
    project, built on top of the Coverage, Gap, and Recommendation
    Engines. No AI/LLM reasoning — every metric here is a rule-based
    aggregation over Deployed product assignments and the existing
    knowledge base.
    """

    domain_overlap_scores: List[DomainOverlapScore]
    duplicate_capabilities: List[DuplicateCapabilityOverlap]
    product_overlaps: List[ProductOverlapPair]
    module_overlaps: List[ModuleOverlapPair]
    framework_overlaps: List[FrameworkOverlapItem]
    redundant_licenses: List[RedundantLicenseItem]
    unused_capabilities: List[UnusedCapabilityItem]
    vendor_summary: List[VendorOverlapSummary]

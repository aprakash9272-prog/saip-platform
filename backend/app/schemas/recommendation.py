from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.gap import FrameworkControlRef

PRIORITY_LEVELS = ["Critical", "High", "Medium", "Low"]


class RecommendationRequest(BaseModel):
    assessment_project_id: int


class ProductCandidate(BaseModel):
    """One catalog product/module capable of closing a gap."""

    vendor: str
    product: str
    edition: str
    module: str
    licensing_tier: Optional[str] = None
    deployment_model: str
    supported_platforms: List[str] = Field(default_factory=list)
    availability_status: str
    already_deployed_vendor: bool
    confidence_score: float
    implementation_complexity: str
    estimated_effort: str


class RecommendationItem(BaseModel):
    """A recommendation to close one gap, using its best-ranked candidate
    product plus every other known candidate for comparison."""

    capability_id: int
    capability_code: str
    capability_name: str
    domain_id: int
    domain_name: str
    severity: str
    business_impact: str
    framework_controls: List[FrameworkControlRef] = Field(default_factory=list)
    candidates: List[ProductCandidate] = Field(default_factory=list)
    priority: str
    domain_coverage_improvement_percentage: float
    estimated_risk_reduction: float


class PriorityBreakdown(BaseModel):
    priority: str
    count: int
    capability_codes: List[str] = Field(default_factory=list)


class ProductComparisonEntry(BaseModel):
    vendor: str
    product: str
    gaps_addressed: int
    average_confidence_score: float
    domains_covered: List[str] = Field(default_factory=list)


class CoverageForecast(BaseModel):
    current_coverage_percentage: float
    projected_coverage_percentage: float
    addressable_gap_count: int
    unaddressable_gap_count: int


class RecommendationSummary(BaseModel):
    assessment_project_id: int
    assessment_project_name: str
    generated_at: datetime
    total_gaps: int
    addressable_gaps: int
    unaddressable_gaps: int
    critical_priority_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    current_risk_score: float
    projected_risk_score: float
    estimated_overall_risk_reduction: float
    coverage_forecast: CoverageForecast


class RecommendationReport(RecommendationSummary):
    """Deterministic, knowledge-base-driven recommendations to close every
    addressable gap identified by the Gap Engine.

    Every recommendation is derived from existing ProductCapabilityMapping
    catalog rows — no AI/LLM reasoning, no generated text. Gaps with zero
    catalog candidates are counted (unaddressable_gaps) but do not appear
    in ``recommendations`` since there is nothing to recommend.
    """

    priority_matrix: List[PriorityBreakdown]
    product_comparison: List[ProductComparisonEntry]
    recommendations: List[RecommendationItem]

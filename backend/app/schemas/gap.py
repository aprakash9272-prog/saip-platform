from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low", "Informational"]


class GapRequest(BaseModel):
    assessment_project_id: int


class FrameworkControlRef(BaseModel):
    framework_name: str
    framework_version: str
    control_id: str
    control_name: str


class GapItem(BaseModel):
    """A single missing capability, classified for risk triage.

    ``status`` is always "Open" in this sprint — the Gap Engine only
    identifies and classifies gaps. Acknowledging, accepting risk on, or
    remediating a gap is a future (Recommendation Engine) concern.
    """

    id: int
    code: str
    name: str
    domain_id: int
    domain_name: str
    risk_category: Optional[str] = None
    severity: str
    business_impact: str
    framework_controls: List[FrameworkControlRef] = Field(default_factory=list)
    mapped_products: List[str] = Field(default_factory=list)
    status: str = "Open"


class DomainGapScore(BaseModel):
    domain_id: int
    domain_name: str
    coverage_percentage: float
    gap_percentage: float
    missing_count: int
    critical_gap_count: int
    domain_risk_score: float


class GapSummary(BaseModel):
    assessment_project_id: int
    assessment_project_name: str
    generated_at: datetime
    total_capabilities: int
    total_gaps: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    informational_count: int
    overall_gap_percentage: float
    overall_risk_score: float


class GapReport(GapSummary):
    """Point-in-time gap calculation for an assessment project.

    Built directly from the Coverage Engine's missing-capability list (see
    app/engine/coverage_engine.py) — every gap here is a capability with
    zero Deployed product assignments providing it. Severity and business
    impact are deterministic classifications, not AI-generated judgments;
    no remediation recommendations are produced.
    """

    domain_gap_scores: List[DomainGapScore]
    gaps: List[GapItem]

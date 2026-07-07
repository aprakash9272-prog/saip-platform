"""Schemas for the Scenario Simulation Engine (Sprint 11).

The Simulation Engine never invents new scoring logic: every field here
either mirrors an existing engine's report (``CoverageReport``,
``GapReport``, ``RecommendationReport``, ``OverlapReport``) or is a
deterministic before/after diff of numbers those reports already
compute. There is no AI/LLM reasoning anywhere in this module.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.coverage import CoverageReport
from app.schemas.gap import GapReport
from app.schemas.overlap import OverlapReport
from app.schemas.recommendation import RecommendationReport


class ScenarioType(str, Enum):
    ADD_PRODUCT = "add_product"
    REMOVE_PRODUCT = "remove_product"
    REPLACE_PRODUCT = "replace_product"
    UPGRADE_EDITION = "upgrade_edition"
    DOWNGRADE_EDITION = "downgrade_edition"
    ENABLE_MODULE = "enable_module"
    DISABLE_MODULE = "disable_module"
    CHANGE_LICENSING_TIER = "change_licensing_tier"
    CHANGE_DEPLOYMENT_MODEL = "change_deployment_model"
    CHANGE_AVAILABILITY_STATUS = "change_availability_status"
    CONSOLIDATE_VENDORS = "consolidate_vendors"
    REMOVE_DUPLICATE_PRODUCTS = "remove_duplicate_products"


class ComparisonClassification(str, Enum):
    IMPROVEMENT = "Improvement"
    REGRESSION = "Regression"
    NEUTRAL = "Neutral"


class SimulationRequest(BaseModel):
    """Describes one hypothetical architecture change to simulate against
    an assessment project's current Deployed product assignments.

    Only the fields relevant to ``scenario_type`` need to be supplied —
    the engine validates the required subset for each scenario and raises
    ``InvalidReferenceError`` (-> HTTP 422) if something required is
    missing or does not resolve. A single flat, mostly-optional schema
    covers all 12 scenarios rather than a discriminated union per type,
    since several scenarios share the same mechanical shape (e.g.
    upgrade/downgrade edition/change licensing tier are all an
    edition swap on an existing assignment).
    """

    assessment_project_id: int
    scenario_type: ScenarioType
    name: Optional[str] = Field(
        default=None, description="Optional label for this simulation run."
    )

    # add_product / replace_product ("add" half): a brand new assignment.
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None
    edition_id: Optional[int] = None
    environment_id: Optional[int] = None
    module_ids: Optional[List[int]] = None
    license_quantity: Optional[int] = None
    deployment_model: Optional[str] = None
    deployment_status: Optional[str] = None
    notes: Optional[str] = None

    # remove_product / replace_product ("remove" half) / upgrade_edition /
    # downgrade_edition / change_licensing_tier / enable_module /
    # disable_module / change_deployment_model / change_availability_status:
    # the existing assignment being mutated.
    assignment_id: Optional[int] = None

    # upgrade_edition / downgrade_edition / change_licensing_tier: swap the
    # assignment onto a different edition (the caller decides which target
    # edition represents an "upgrade" vs. "downgrade" vs. a plain tier
    # change — the engine just applies the swap deterministically).
    target_edition_id: Optional[int] = None
    target_module_ids: Optional[List[int]] = None

    # enable_module / disable_module: one module toggled on the assignment.
    module_id: Optional[int] = None

    # consolidate_vendors / remove_duplicate_products: bulk-remove a set of
    # assignments (typically sourced from the Overlap Engine's own
    # redundant_licenses / vendor_summary output by the caller/UI).
    assignment_ids: Optional[List[int]] = None


class MetricComparison(BaseModel):
    """One current-vs-proposed metric, classified Improvement / Regression
    / Neutral. Some metrics improve when higher (e.g. coverage %),
    others improve when lower (e.g. gap %, risk score, overlap %, cost
    and complexity scores, vendor/license counts) — the classification
    already accounts for that, so consumers can treat every comparison
    uniformly."""

    metric: str
    current_value: float
    proposed_value: float
    delta: float
    percentage_change: float
    classification: ComparisonClassification


class CapabilityComparisonItem(BaseModel):
    """A capability whose coverage status changed (or stayed put) between
    the current and proposed states."""

    id: int
    code: str
    name: str
    domain_name: str
    current_covered: bool
    proposed_covered: bool
    current_provider_count: int
    proposed_provider_count: int
    classification: ComparisonClassification


class VendorComparisonItem(BaseModel):
    vendor: str
    current_deployed: bool
    proposed_deployed: bool
    current_capability_count: int
    proposed_capability_count: int
    current_license_quantity: int
    proposed_license_quantity: int
    classification: ComparisonClassification


class FrameworkComparisonItem(BaseModel):
    framework_name: str
    framework_version: str
    total_controls: int
    current_satisfied_controls: int
    proposed_satisfied_controls: int
    classification: ComparisonClassification


class SimulationSummary(BaseModel):
    id: int
    assessment_project_id: int
    assessment_project_name: str
    scenario_type: ScenarioType
    name: Optional[str] = None
    generated_at: datetime
    coverage_delta: MetricComparison
    gap_delta: MetricComparison
    overlap_delta: MetricComparison
    recommendation_delta: MetricComparison
    risk_delta: MetricComparison
    cost_delta: MetricComparison
    complexity_delta: MetricComparison
    vendor_count_delta: MetricComparison
    license_count_delta: MetricComparison
    framework_coverage_delta: MetricComparison
    executive_summary: List[str] = Field(default_factory=list)


class SimulationReport(SimulationSummary):
    """Deterministic before/after comparison of an assessment project's
    Coverage, Gap, Recommendation, and Overlap reports: once against its
    real current Deployed product assignments, and once again with one
    hypothetical scenario applied in memory (flushed but never committed
    to the database — see ``app/engine/simulation_engine.py``). Every
    number here comes from re-running the four existing engines
    unmodified; no calculation is duplicated and no AI/LLM reasoning is
    involved anywhere.
    """

    current_coverage: CoverageReport
    proposed_coverage: CoverageReport
    current_gap: GapReport
    proposed_gap: GapReport
    current_recommendation: RecommendationReport
    proposed_recommendation: RecommendationReport
    current_overlap: OverlapReport
    proposed_overlap: OverlapReport
    capability_comparison: List[CapabilityComparisonItem] = Field(default_factory=list)
    vendor_comparison: List[VendorComparisonItem] = Field(default_factory=list)
    framework_comparison: List[FrameworkComparisonItem] = Field(default_factory=list)

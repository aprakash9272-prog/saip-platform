"""Gap analysis engine.

Identifies and classifies every missing security capability for an
assessment project, built directly on top of the Coverage Engine's
missing-capability list. This is pure identification/classification — no
remediation recommendations, no simulation, no AI reasoning. Those are
separate future engines (see app/engine/recommendation_engine.py and
friends).
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlmodel import Session

from app.engine.coverage_engine import CoverageEngine
from app.repositories.capability import CapabilityRepository
from app.repositories.product_capability_mapping import (
    ProductCapabilityMappingRepository,
)
from app.schemas.gap import (
    SEVERITY_LEVELS,
    DomainGapScore,
    FrameworkControlRef,
    GapItem,
    GapReport,
)

# Numeric weight per severity tier, used to compute an aggregate 0-100 risk
# score (see domain_risk_score / overall risk score below).
_SEVERITY_WEIGHT: Dict[str, int] = {
    "Critical": 100,
    "High": 75,
    "Medium": 50,
    "Low": 25,
    "Informational": 0,
}

# Baseline severity points contributed by a capability's risk category.
# Calibrated so risk category alone lands on a sensible tier (Critical -> High,
# High -> High, Medium -> Medium, Low -> Low), and corroborating signals
# (framework mapping count, business-critical flag) are what push a gap up
# into the top Critical tier.
_RISK_CATEGORY_BASE_SCORE: Dict[str, int] = {
    "Critical": 5,
    "High": 4,
    "Medium": 2,
    "Low": 1,
}


def _classify_severity(
    risk_category: Optional[str], framework_mapping_count: int, is_business_critical: bool
) -> str:
    """Deterministic severity classification.

    score = risk_category base (0-5)
          + framework mapping bonus (+1 for 1-2 mappings, +2 for 3+)
          + business-critical bonus (+1)
    Higher scores escalate the tier; a capability with no risk category, no
    framework mappings, and not business-critical is merely Informational.
    """
    score = _RISK_CATEGORY_BASE_SCORE.get(risk_category or "", 0)
    if framework_mapping_count >= 3:
        score += 2
    elif framework_mapping_count >= 1:
        score += 1
    if is_business_critical:
        score += 1

    if score >= 6:
        return "Critical"
    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    if score >= 1:
        return "Low"
    return "Informational"


def _classify_business_impact(risk_category: Optional[str], is_business_critical: bool) -> str:
    """Deterministic business-impact classification (operational lens,
    distinct from — but related to — technical severity)."""
    if is_business_critical and risk_category in ("Critical", "High"):
        return "Severe"
    if is_business_critical or risk_category == "Critical":
        return "High"
    if risk_category in ("High", "Medium"):
        return "Moderate"
    return "Low"


class GapEngine:
    """Computes a :class:`GapReport` for a single assessment project.

    Reuses :class:`CoverageEngine` to determine which capabilities are
    missing, then classifies each missing capability by severity and
    business impact using its risk category, the number of compliance
    framework controls mapped to it, and whether it is flagged
    business-critical. Every gap's ``status`` is fixed at "Open" — this
    engine only identifies and classifies; remediation workflow and
    recommendations are out of scope for this sprint.
    """

    def __init__(self, session: Session):
        self.session = session
        self.coverage_engine = CoverageEngine(session)
        self.capability_repository = CapabilityRepository(session)
        self.product_mapping_repository = ProductCapabilityMappingRepository(session)

    def calculate(self, assessment_project_id: int) -> GapReport:
        coverage = self.coverage_engine.calculate(assessment_project_id)

        capabilities_by_id = {c.id: c for c in self.capability_repository.all()}

        # capability_id -> distinct catalog products (regardless of whether
        # deployed in this assessment) known to provide it — informational
        # only, not a ranked or prioritized recommendation.
        products_by_capability: Dict[int, set] = defaultdict(set)
        for mapping in self.product_mapping_repository.all():
            label = (
                f"{mapping.vendor.name} - {mapping.product.name} ({mapping.edition.name})"
            )
            products_by_capability[mapping.capability_id].add(label)

        gaps: List[GapItem] = []
        domain_gap_counts: Dict[int, int] = defaultdict(int)
        domain_critical_counts: Dict[int, int] = defaultdict(int)
        domain_severity_totals: Dict[int, int] = defaultdict(int)

        for missing in coverage.missing_capabilities:
            capability = capabilities_by_id.get(missing.id)
            framework_controls: List[FrameworkControlRef] = []
            framework_mapping_count = 0
            risk_category: Optional[str] = None
            is_business_critical = False

            if capability is not None:
                risk_category = capability.risk_category
                is_business_critical = capability.is_business_critical
                framework_mapping_count = len(capability.framework_mappings)
                framework_controls = [
                    FrameworkControlRef(
                        framework_name=mapping.framework.name,
                        framework_version=mapping.framework.version,
                        control_id=mapping.control_id,
                        control_name=mapping.control_name,
                    )
                    for mapping in capability.framework_mappings
                ]

            severity = _classify_severity(
                risk_category, framework_mapping_count, is_business_critical
            )
            business_impact = _classify_business_impact(risk_category, is_business_critical)

            gaps.append(
                GapItem(
                    id=missing.id,
                    code=missing.code,
                    name=missing.name,
                    domain_id=missing.domain_id,
                    domain_name=missing.domain_name,
                    risk_category=risk_category,
                    severity=severity,
                    business_impact=business_impact,
                    framework_controls=sorted(
                        framework_controls,
                        key=lambda f: (f.framework_name, f.control_id),
                    ),
                    mapped_products=sorted(products_by_capability.get(missing.id, set())),
                    status="Open",
                )
            )

            domain_gap_counts[missing.domain_id] += 1
            domain_severity_totals[missing.domain_id] += _SEVERITY_WEIGHT[severity]
            if severity == "Critical":
                domain_critical_counts[missing.domain_id] += 1

        domain_gap_scores = []
        for domain_coverage in coverage.domain_coverage:
            total = domain_coverage.total_count
            missing_count = domain_gap_counts.get(domain_coverage.domain_id, 0)
            gap_percentage = round((missing_count / total * 100), 2) if total else 0.0
            avg_severity = (
                domain_severity_totals.get(domain_coverage.domain_id, 0) / missing_count
                if missing_count
                else 0.0
            )
            domain_risk_score = round((gap_percentage + avg_severity) / 2, 2)
            domain_gap_scores.append(
                DomainGapScore(
                    domain_id=domain_coverage.domain_id,
                    domain_name=domain_coverage.domain_name,
                    coverage_percentage=domain_coverage.coverage_percentage,
                    gap_percentage=gap_percentage,
                    missing_count=missing_count,
                    critical_gap_count=domain_critical_counts.get(
                        domain_coverage.domain_id, 0
                    ),
                    domain_risk_score=domain_risk_score,
                )
            )

        severity_counts = {level: 0 for level in SEVERITY_LEVELS}
        for gap in gaps:
            severity_counts[gap.severity] += 1

        total_gaps = len(gaps)
        overall_gap_percentage = (
            round((total_gaps / coverage.total_capabilities * 100), 2)
            if coverage.total_capabilities
            else 0.0
        )
        overall_avg_severity = (
            sum(_SEVERITY_WEIGHT[gap.severity] for gap in gaps) / total_gaps
            if total_gaps
            else 0.0
        )
        overall_risk_score = round((overall_gap_percentage + overall_avg_severity) / 2, 2)

        return GapReport(
            assessment_project_id=coverage.assessment_project_id,
            assessment_project_name=coverage.assessment_project_name,
            generated_at=datetime.now(timezone.utc),
            total_capabilities=coverage.total_capabilities,
            total_gaps=total_gaps,
            critical_count=severity_counts["Critical"],
            high_count=severity_counts["High"],
            medium_count=severity_counts["Medium"],
            low_count=severity_counts["Low"],
            informational_count=severity_counts["Informational"],
            overall_gap_percentage=overall_gap_percentage,
            overall_risk_score=overall_risk_score,
            domain_gap_scores=domain_gap_scores,
            gaps=gaps,
        )

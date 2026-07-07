"""Security recommendation engine.

Recommends products, modules, and configurations from the existing
knowledge base that would close the gaps identified by the Gap Engine.
Every recommendation is derived deterministically from
ProductCapabilityMapping catalog rows — there is no AI/LLM reasoning, no
generated text, and no simulation. Gaps with zero catalog candidates are
counted but produce no recommendation, since there is nothing in the
catalog to recommend.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from sqlmodel import Session

from app.engine.gap_engine import GapEngine
from app.models.product_assignment import DeploymentStatus
from app.models.product_capability_mapping import ProductCapabilityMapping
from app.repositories.product_assignment import ProductAssignmentRepository
from app.repositories.product_capability_mapping import (
    ProductCapabilityMappingRepository,
)
from app.schemas.recommendation import (
    PRIORITY_LEVELS,
    CoverageForecast,
    PriorityBreakdown,
    ProductCandidate,
    ProductComparisonEntry,
    RecommendationItem,
    RecommendationReport,
)

# Confidence score (0-100) by availability status — a Generally Available
# product is a safer bet than a Beta/Preview one, and a Deprecated or
# Discontinued one is barely worth recommending at all.
_AVAILABILITY_CONFIDENCE: Dict[str, float] = {
    "Generally Available": 80.0,
    "Beta": 55.0,
    "Preview": 40.0,
    "Deprecated": 15.0,
    "Discontinued": 5.0,
}
_ALREADY_DEPLOYED_CONFIDENCE_BONUS = 15.0

# Base implementation complexity by deployment model.
_DEPLOYMENT_COMPLEXITY: Dict[str, str] = {
    "SaaS": "Low",
    "Agent": "Medium",
    "Network": "Medium",
    "Hybrid": "High",
}
_COMPLEXITY_DOWNGRADE = {"High": "Medium", "Medium": "Low", "Low": "Low"}
_EFFORT_BY_COMPLEXITY = {
    "Low": "1-2 weeks",
    "Medium": "2-6 weeks",
    "High": "6-12 weeks",
}
_COMPLEXITY_RANK = {"Low": 0, "Medium": 1, "High": 2}

_SEVERITY_SCORE: Dict[str, int] = {
    "Critical": 6,
    "High": 4,
    "Medium": 2,
    "Low": 1,
    "Informational": 0,
}
_BUSINESS_IMPACT_SCORE: Dict[str, int] = {
    "Severe": 2,
    "High": 1,
    "Moderate": 0,
    "Low": 0,
}
# Mirrors GapEngine's own severity weights, used to compute marginal risk
# reduction if a single gap is closed.
_SEVERITY_WEIGHT: Dict[str, int] = {
    "Critical": 100,
    "High": 75,
    "Medium": 50,
    "Low": 25,
    "Informational": 0,
}


def _confidence_score(availability_status: str, already_deployed_vendor: bool) -> float:
    score = _AVAILABILITY_CONFIDENCE.get(availability_status, 30.0)
    if already_deployed_vendor:
        score += _ALREADY_DEPLOYED_CONFIDENCE_BONUS
    return round(min(score, 100.0), 2)


def _implementation_complexity(deployment_model: str, already_deployed_vendor: bool) -> str:
    complexity = _DEPLOYMENT_COMPLEXITY.get(deployment_model, "Medium")
    if already_deployed_vendor:
        complexity = _COMPLEXITY_DOWNGRADE[complexity]
    return complexity


def _classify_priority(
    severity: str,
    business_impact: str,
    framework_mapping_count: int,
    best_complexity: str,
    domain_coverage_improvement_percentage: float,
) -> str:
    """Deterministic 4-tier priority ranking (Critical/High/Medium/Low).

    score = severity (0-6) + business criticality (0-2)
          + framework impact bonus (+1 for 1-2 controls, +2 for 3+)
          + easy-win bonus (+1 if Low complexity, -1 if High complexity)
          + concentrated-domain bonus (+1 if closing this gap moves the
            domain's coverage by 10 points or more — a domain small enough
            that each capability counts disproportionately; the real
            catalog's domains average ~18 capabilities each (~5.5 points
            per capability), so this only fires for unusually small/custom
            domains, not the typical case)
    """
    score = _SEVERITY_SCORE.get(severity, 0) + _BUSINESS_IMPACT_SCORE.get(business_impact, 0)
    if framework_mapping_count >= 3:
        score += 2
    elif framework_mapping_count >= 1:
        score += 1
    if best_complexity == "Low":
        score += 1
    elif best_complexity == "High":
        score -= 1
    if domain_coverage_improvement_percentage >= 10.0:
        score += 1

    if score >= 9:
        return "Critical"
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


class RecommendationEngine:
    """Computes a :class:`RecommendationReport` for a single assessment
    project, using the Gap Engine's report as its sole source of gaps."""

    def __init__(self, session: Session):
        self.session = session
        self.gap_engine = GapEngine(session)
        self.assignment_repository = ProductAssignmentRepository(session)
        self.product_mapping_repository = ProductCapabilityMappingRepository(session)

    def calculate(self, assessment_project_id: int) -> RecommendationReport:
        gap_report = self.gap_engine.calculate(assessment_project_id)

        deployed_vendor_ids = {
            a.vendor_id
            for a in self.assignment_repository.list_by_assessment_project(
                assessment_project_id
            )
            if a.deployment_status == DeploymentStatus.DEPLOYED.value
        }

        mappings_by_capability: Dict[int, List[ProductCapabilityMapping]] = defaultdict(list)
        for mapping in self.product_mapping_repository.all():
            mappings_by_capability[mapping.capability_id].append(mapping)

        # Capability count per domain, used for the "concentrated domain"
        # priority bonus. DomainGapScore doesn't carry total_count directly,
        # but it's recoverable from missing_count / gap_percentage — this is
        # only ever looked up for domains that actually have a gap below, so
        # gap_percentage is guaranteed non-zero at lookup time.
        domain_capability_totals: Dict[int, int] = {
            domain_score.domain_id: round(
                domain_score.missing_count / (domain_score.gap_percentage / 100)
            )
            for domain_score in gap_report.domain_gap_scores
            if domain_score.gap_percentage
        }

        total_gaps = len(gap_report.gaps)
        total_severity_weight = sum(_SEVERITY_WEIGHT[g.severity] for g in gap_report.gaps)

        recommendations: List[RecommendationItem] = []
        priority_counts: Dict[str, int] = {p: 0 for p in PRIORITY_LEVELS}
        priority_codes: Dict[str, List[str]] = defaultdict(list)
        product_gap_ids: Dict[Tuple[str, str], set] = defaultdict(set)
        product_confidences: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        product_domains: Dict[Tuple[str, str], set] = defaultdict(set)

        addressable = 0
        for gap in gap_report.gaps:
            catalog_mappings = mappings_by_capability.get(gap.id, [])
            if not catalog_mappings:
                continue

            addressable += 1
            candidates: List[ProductCandidate] = []
            for mapping in catalog_mappings:
                already_deployed = mapping.vendor_id in deployed_vendor_ids
                confidence = _confidence_score(mapping.availability_status, already_deployed)
                complexity = _implementation_complexity(
                    mapping.deployment_model, already_deployed
                )
                candidates.append(
                    ProductCandidate(
                        vendor=mapping.vendor.name,
                        product=mapping.product.name,
                        edition=mapping.edition.name,
                        module=mapping.module.name,
                        licensing_tier=mapping.licensing_tier,
                        deployment_model=mapping.deployment_model,
                        supported_platforms=list(mapping.supported_platforms),
                        availability_status=mapping.availability_status,
                        already_deployed_vendor=already_deployed,
                        confidence_score=confidence,
                        implementation_complexity=complexity,
                        estimated_effort=_EFFORT_BY_COMPLEXITY[complexity],
                    )
                )
                key = (mapping.vendor.name, mapping.product.name)
                product_gap_ids[key].add(gap.id)
                product_confidences[key].append(confidence)
                product_domains[key].add(gap.domain_name)

            candidates.sort(
                key=lambda c: (
                    -c.confidence_score,
                    _COMPLEXITY_RANK[c.implementation_complexity],
                    c.vendor,
                    c.product,
                )
            )
            best = candidates[0]

            domain_total = domain_capability_totals.get(gap.domain_id, 0)
            domain_improvement = round(100 / domain_total, 2) if domain_total else 0.0

            priority = _classify_priority(
                gap.severity,
                gap.business_impact,
                len(gap.framework_controls),
                best.implementation_complexity,
                domain_improvement,
            )
            priority_counts[priority] += 1
            priority_codes[priority].append(gap.code)

            new_total = total_gaps - 1
            gap_weight = _SEVERITY_WEIGHT[gap.severity]
            new_gap_pct = (
                round(new_total / gap_report.total_capabilities * 100, 2)
                if gap_report.total_capabilities
                else 0.0
            )
            new_avg_severity = (
                (total_severity_weight - gap_weight) / new_total if new_total else 0.0
            )
            new_risk_score = round((new_gap_pct + new_avg_severity) / 2, 2)
            estimated_risk_reduction = round(gap_report.overall_risk_score - new_risk_score, 2)

            recommendations.append(
                RecommendationItem(
                    capability_id=gap.id,
                    capability_code=gap.code,
                    capability_name=gap.name,
                    domain_id=gap.domain_id,
                    domain_name=gap.domain_name,
                    severity=gap.severity,
                    business_impact=gap.business_impact,
                    framework_controls=gap.framework_controls,
                    candidates=candidates,
                    priority=priority,
                    domain_coverage_improvement_percentage=domain_improvement,
                    estimated_risk_reduction=estimated_risk_reduction,
                )
            )

        # PRIORITY_LEVELS is ["Critical", "High", "Medium", "Low"], so sorting
        # ascending by index already puts Critical first.
        recommendations.sort(
            key=lambda r: (
                PRIORITY_LEVELS.index(r.priority),
                -r.candidates[0].confidence_score,
            )
        )

        unaddressable = total_gaps - addressable

        priority_matrix = [
            PriorityBreakdown(
                priority=p, count=priority_counts[p], capability_codes=sorted(priority_codes[p])
            )
            for p in PRIORITY_LEVELS
        ]

        product_comparison = sorted(
            (
                ProductComparisonEntry(
                    vendor=vendor,
                    product=product,
                    gaps_addressed=len(gap_ids),
                    average_confidence_score=round(
                        sum(product_confidences[(vendor, product)])
                        / len(product_confidences[(vendor, product)]),
                        2,
                    ),
                    domains_covered=sorted(product_domains[(vendor, product)]),
                )
                for (vendor, product), gap_ids in product_gap_ids.items()
            ),
            key=lambda entry: (-entry.gaps_addressed, entry.vendor, entry.product),
        )

        current_coverage_percentage = round(100 - gap_report.overall_gap_percentage, 2)
        projected_covered = gap_report.total_capabilities - unaddressable
        projected_coverage_percentage = (
            round(projected_covered / gap_report.total_capabilities * 100, 2)
            if gap_report.total_capabilities
            else 0.0
        )
        projected_avg_severity = (
            sum(
                _SEVERITY_WEIGHT[g.severity]
                for g in gap_report.gaps
                if not mappings_by_capability.get(g.id)
            )
            / unaddressable
            if unaddressable
            else 0.0
        )
        projected_gap_percentage = round(100 - projected_coverage_percentage, 2)
        projected_risk_score = round((projected_gap_percentage + projected_avg_severity) / 2, 2)
        estimated_overall_risk_reduction = round(
            gap_report.overall_risk_score - projected_risk_score, 2
        )

        coverage_forecast = CoverageForecast(
            current_coverage_percentage=current_coverage_percentage,
            projected_coverage_percentage=projected_coverage_percentage,
            addressable_gap_count=addressable,
            unaddressable_gap_count=unaddressable,
        )

        return RecommendationReport(
            assessment_project_id=gap_report.assessment_project_id,
            assessment_project_name=gap_report.assessment_project_name,
            generated_at=datetime.now(timezone.utc),
            total_gaps=total_gaps,
            addressable_gaps=addressable,
            unaddressable_gaps=unaddressable,
            critical_priority_count=priority_counts["Critical"],
            high_priority_count=priority_counts["High"],
            medium_priority_count=priority_counts["Medium"],
            low_priority_count=priority_counts["Low"],
            current_risk_score=gap_report.overall_risk_score,
            projected_risk_score=projected_risk_score,
            estimated_overall_risk_reduction=estimated_overall_risk_reduction,
            coverage_forecast=coverage_forecast,
            priority_matrix=priority_matrix,
            product_comparison=product_comparison,
            recommendations=recommendations,
        )

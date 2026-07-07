"""Coverage analysis engine.

Calculates how much of the vendor-neutral capability catalog an assessment
project's deployed products actually cover. This is a pure calculation —
no gap remediation, no overlap scoring, no recommendations. Those are
separate future engines (see app/engine/gap_engine.py and friends).
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

from sqlmodel import Session

from app.models.product_assignment import DeploymentStatus
from app.repositories.assessment_project import AssessmentProjectRepository
from app.repositories.capability import CapabilityRepository
from app.repositories.domain import DomainRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.schemas.coverage import (
    CapabilityCoverageItem,
    CoverageReport,
    DomainCoverage,
    DuplicateCapabilityItem,
)
from app.services.assessment_project import AssessmentProjectService


class CoverageEngine:
    """Computes a :class:`CoverageReport` for a single assessment project.

    Only Product Assignments whose ``deployment_status`` is ``Deployed``
    contribute to coverage — a product that is Not Started, In Progress, or
    Decommissioned is not actually protecting the environment today, so it
    should not count as "covering" a capability.
    """

    def __init__(self, session: Session):
        self.session = session
        self.assessment_project_service = AssessmentProjectService(session)
        self.assessment_project_repository = AssessmentProjectRepository(session)
        self.assignment_repository = ProductAssignmentRepository(session)
        self.domain_repository = DomainRepository(session)
        self.capability_repository = CapabilityRepository(session)

    def calculate(self, assessment_project_id: int) -> CoverageReport:
        project = self.assessment_project_service.get(assessment_project_id)

        assignments = self.assignment_repository.list_by_assessment_project(
            assessment_project_id
        )
        deployed_assignments = [
            a for a in assignments if a.deployment_status == DeploymentStatus.DEPLOYED.value
        ]

        all_capabilities = self.capability_repository.all()
        all_domains = self.domain_repository.all()
        domain_by_id = {d.id: d for d in all_domains}

        # capability_id -> distinct {assignment_id: provider_label}. Keying by
        # assignment_id (not module_id) means two modules on the *same*
        # deployed product providing the same capability is not a duplicate —
        # duplicates only count when two different deployed products overlap.
        providers: Dict[int, Dict[int, str]] = defaultdict(dict)
        for assignment in deployed_assignments:
            label = (
                f"{assignment.vendor.name} - {assignment.product.name} "
                f"({assignment.edition.name})"
            )
            for module in assignment.modules:
                for capability in module.capabilities:
                    providers[capability.id][assignment.id] = label

        domain_totals: Dict[int, int] = defaultdict(int)
        domain_covered: Dict[int, int] = defaultdict(int)

        covered_items: List[CapabilityCoverageItem] = []
        missing_items: List[CapabilityCoverageItem] = []
        duplicate_items: List[DuplicateCapabilityItem] = []

        for capability in sorted(all_capabilities, key=lambda c: c.code):
            domain = domain_by_id.get(capability.domain_id)
            domain_name = domain.name if domain else "Unknown"
            domain_totals[capability.domain_id] += 1

            capability_providers = providers.get(capability.id, {})
            provider_count = len(capability_providers)
            provider_labels = sorted(set(capability_providers.values()))

            item = CapabilityCoverageItem(
                id=capability.id,
                code=capability.code,
                name=capability.name,
                domain_id=capability.domain_id,
                domain_name=domain_name,
                covered=provider_count > 0,
                provider_count=provider_count,
                providers=provider_labels,
            )

            if provider_count > 0:
                covered_items.append(item)
                domain_covered[capability.domain_id] += 1
                if provider_count > 1:
                    duplicate_items.append(
                        DuplicateCapabilityItem(
                            id=capability.id,
                            code=capability.code,
                            name=capability.name,
                            domain_id=capability.domain_id,
                            domain_name=domain_name,
                            provider_count=provider_count,
                            providers=provider_labels,
                        )
                    )
            else:
                missing_items.append(item)

        domain_coverage = []
        for domain in sorted(all_domains, key=lambda d: d.name):
            total = domain_totals.get(domain.id, 0)
            covered = domain_covered.get(domain.id, 0)
            percentage = round((covered / total * 100), 2) if total else 0.0
            domain_coverage.append(
                DomainCoverage(
                    domain_id=domain.id,
                    domain_name=domain.name,
                    covered_count=covered,
                    total_count=total,
                    coverage_percentage=percentage,
                )
            )

        total_capabilities = len(all_capabilities)
        covered_count = len(covered_items)
        overall_percentage = (
            round((covered_count / total_capabilities * 100), 2)
            if total_capabilities
            else 0.0
        )

        return CoverageReport(
            assessment_project_id=project.id,
            assessment_project_name=project.name,
            generated_at=datetime.now(timezone.utc),
            total_capabilities=total_capabilities,
            covered_capability_count=covered_count,
            missing_capability_count=len(missing_items),
            duplicate_capability_count=len(duplicate_items),
            overall_coverage_percentage=overall_percentage,
            domain_coverage=domain_coverage,
            covered_capabilities=covered_items,
            missing_capabilities=missing_items,
            duplicate_capabilities=duplicate_items,
        )

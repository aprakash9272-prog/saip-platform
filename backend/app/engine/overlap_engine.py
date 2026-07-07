"""Security overlap & optimization engine.

Identifies overlapping security capabilities across an assessment
project's deployed products and surfaces consolidation opportunities:
duplicate capabilities, product/module/framework overlap, redundant
licenses, unused (purchased-but-not-enabled) capabilities, and vendors
solving identical problems. Every metric here is a deterministic,
rule-based aggregation over Deployed product assignments and the
existing knowledge base — there is no AI/LLM reasoning and no simulation.
"""

from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from typing import Dict, List, Set, Tuple

from sqlmodel import Session

from app.engine.coverage_engine import CoverageEngine
from app.engine.gap_engine import GapEngine
from app.engine.recommendation_engine import RecommendationEngine
from app.models.product_assignment import DeploymentStatus
from app.repositories.capability import CapabilityRepository
from app.repositories.module import ModuleRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.schemas.overlap import (
    DomainOverlapScore,
    DuplicateCapabilityOverlap,
    FrameworkOverlapItem,
    ModuleOverlapPair,
    OverlapReport,
    ProductOverlapPair,
    RedundantLicenseItem,
    UnusedCapabilityItem,
    VendorOverlapSummary,
)


def _assignment_label(assignment) -> str:
    return f"{assignment.vendor.name} - {assignment.product.name} ({assignment.edition.name})"


class OverlapEngine:
    """Computes an :class:`OverlapReport` for a single assessment project.

    Reuses :class:`CoverageEngine` (via :class:`GapEngine`) for the
    covered/duplicate capability baseline, :class:`GapEngine` for the
    overall gap percentage that feeds the optimization score, and
    :class:`RecommendationEngine`'s product comparison to note which
    overlapping vendors also help close open gaps (a genuine reason to
    keep a vendor despite redundancy, rather than a pure duplicate).
    """

    def __init__(self, session: Session):
        self.session = session
        self.coverage_engine = CoverageEngine(session)
        self.gap_engine = GapEngine(session)
        self.recommendation_engine = RecommendationEngine(session)
        self.assignment_repository = ProductAssignmentRepository(session)
        self.module_repository = ModuleRepository(session)
        self.capability_repository = CapabilityRepository(session)

    def calculate(self, assessment_project_id: int) -> OverlapReport:
        coverage = self.coverage_engine.calculate(assessment_project_id)
        gap_report = self.gap_engine.calculate(assessment_project_id)
        recommendation_report = self.recommendation_engine.calculate(assessment_project_id)

        assignments = self.assignment_repository.list_by_assessment_project(
            assessment_project_id
        )
        deployed = [
            a for a in assignments if a.deployment_status == DeploymentStatus.DEPLOYED.value
        ]

        capability_by_id = {c.id: c for c in self.capability_repository.all()}

        # assignment_id -> set of capability ids it actually provides
        # (through its enabled modules).
        assignment_capabilities: Dict[int, Set[int]] = {}
        for assignment in deployed:
            caps: Set[int] = set()
            for module in assignment.modules:
                for capability in module.capabilities:
                    caps.add(capability.id)
            assignment_capabilities[assignment.id] = caps

        # capability_id -> {assignment_id: (vendor_name, label)}
        capability_providers: Dict[int, Dict[int, Tuple[str, str]]] = defaultdict(dict)
        for assignment in deployed:
            label = _assignment_label(assignment)
            for capability_id in assignment_capabilities[assignment.id]:
                capability_providers[capability_id][assignment.id] = (
                    assignment.vendor.name,
                    label,
                )

        # -- 1. Duplicate capabilities (+ cross-vendor flag) --------------------
        duplicate_capabilities: List[DuplicateCapabilityOverlap] = []
        domain_duplicate_counts: Dict[int, int] = defaultdict(int)
        cross_vendor_duplicate_count = 0
        for capability_id, providers in capability_providers.items():
            if len(providers) <= 1:
                continue
            capability = capability_by_id.get(capability_id)
            if capability is None:
                continue
            vendor_names = {vendor for vendor, _ in providers.values()}
            labels = sorted({label for _, label in providers.values()})
            cross_vendor = len(vendor_names) >= 2
            if cross_vendor:
                cross_vendor_duplicate_count += 1
            domain_duplicate_counts[capability.domain_id] += 1
            duplicate_capabilities.append(
                DuplicateCapabilityOverlap(
                    id=capability.id,
                    code=capability.code,
                    name=capability.name,
                    domain_id=capability.domain_id,
                    domain_name=capability.domain.name,
                    provider_count=len(providers),
                    distinct_vendor_count=len(vendor_names),
                    providers=labels,
                    cross_vendor=cross_vendor,
                )
            )
        duplicate_capabilities.sort(key=lambda d: (-d.provider_count, d.code))

        # -- 2. Product overlap pairs ------------------------------------------
        product_overlaps: List[ProductOverlapPair] = []
        for a, b in combinations(deployed, 2):
            shared = assignment_capabilities[a.id] & assignment_capabilities[b.id]
            if not shared:
                continue
            smaller = min(len(assignment_capabilities[a.id]), len(assignment_capabilities[b.id]))
            pct = round(len(shared) / smaller * 100, 2) if smaller else 0.0
            product_overlaps.append(
                ProductOverlapPair(
                    vendor_a=a.vendor.name,
                    product_a=a.product.name,
                    vendor_b=b.vendor.name,
                    product_b=b.product.name,
                    shared_capability_count=len(shared),
                    shared_capability_codes=sorted(
                        capability_by_id[c].code for c in shared if c in capability_by_id
                    ),
                    overlap_percentage=pct,
                )
            )
        product_overlaps.sort(key=lambda p: -p.shared_capability_count)

        # -- 3. Module overlap pairs --------------------------------------------
        module_entries = [
            (assignment, module) for assignment in deployed for module in assignment.modules
        ]
        module_overlaps: List[ModuleOverlapPair] = []
        for (assignment_a, module_a), (assignment_b, module_b) in combinations(
            module_entries, 2
        ):
            if module_a.id == module_b.id:
                continue
            caps_a = {c.id for c in module_a.capabilities}
            caps_b = {c.id for c in module_b.capabilities}
            shared = caps_a & caps_b
            if not shared:
                continue
            module_overlaps.append(
                ModuleOverlapPair(
                    vendor_a=assignment_a.vendor.name,
                    product_a=assignment_a.product.name,
                    module_a=module_a.name,
                    vendor_b=assignment_b.vendor.name,
                    product_b=assignment_b.product.name,
                    module_b=module_b.name,
                    shared_capability_count=len(shared),
                    shared_capability_codes=sorted(
                        capability_by_id[c].code for c in shared if c in capability_by_id
                    ),
                )
            )
        module_overlaps.sort(key=lambda m: -m.shared_capability_count)

        # -- 4. Framework overlap (controls redundantly satisfied) -------------
        framework_overlaps: List[FrameworkOverlapItem] = []
        for dup in duplicate_capabilities:
            capability = capability_by_id.get(dup.id)
            if capability is None:
                continue
            for mapping in capability.framework_mappings:
                framework_overlaps.append(
                    FrameworkOverlapItem(
                        framework_name=mapping.framework.name,
                        framework_version=mapping.framework.version,
                        control_id=mapping.control_id,
                        control_name=mapping.control_name,
                        provider_count=dup.provider_count,
                        providers=dup.providers,
                    )
                )
        framework_overlaps.sort(
            key=lambda f: (-f.provider_count, f.framework_name, f.control_id)
        )

        # -- 5. Redundant licenses -----------------------------------------------
        redundant_licenses: List[RedundantLicenseItem] = []
        for assignment in deployed:
            caps = assignment_capabilities[assignment.id]
            if not caps:
                continue
            redundant_count = sum(
                1 for c in caps if len(capability_providers.get(c, {})) > 1
            )
            if redundant_count == 0:
                continue
            total = len(caps)
            pct = round(redundant_count / total * 100, 2) if total else 0.0
            redundant_licenses.append(
                RedundantLicenseItem(
                    assignment_id=assignment.id,
                    vendor=assignment.vendor.name,
                    product=assignment.product.name,
                    edition=assignment.edition.name,
                    license_quantity=assignment.license_quantity,
                    redundant_capability_count=redundant_count,
                    total_capability_count=total,
                    redundancy_percentage=pct,
                    fully_redundant=(redundant_count == total),
                )
            )
        redundant_licenses.sort(key=lambda r: -r.redundancy_percentage)

        # -- 6. Unused capabilities (purchased edition, module never enabled) --
        unused_capabilities: List[UnusedCapabilityItem] = []
        for assignment in deployed:
            enabled_module_ids = {m.id for m in assignment.modules}
            edition_modules, _ = self.module_repository.list(
                skip=0, limit=1_000_000, filters={"edition_id": assignment.edition_id}
            )
            for module in edition_modules:
                if module.id in enabled_module_ids:
                    continue
                for capability in module.capabilities:
                    unused_capabilities.append(
                        UnusedCapabilityItem(
                            assignment_id=assignment.id,
                            vendor=assignment.vendor.name,
                            product=assignment.product.name,
                            edition=assignment.edition.name,
                            module=module.name,
                            capability_code=capability.code,
                            capability_name=capability.name,
                            domain_name=capability.domain.name,
                        )
                    )
        unused_capabilities.sort(key=lambda u: (u.vendor, u.product, u.capability_code))

        # -- 7. Vendor summary (+ Recommendation Engine cross-reference) -------
        vendor_capabilities: Dict[str, Set[int]] = defaultdict(set)
        vendor_assignment_ids: Dict[str, Set[int]] = defaultdict(set)
        vendor_license_quantity: Dict[str, int] = defaultdict(int)
        for assignment in deployed:
            vendor_capabilities[assignment.vendor.name] |= assignment_capabilities[assignment.id]
            vendor_assignment_ids[assignment.vendor.name].add(assignment.id)
            vendor_license_quantity[assignment.vendor.name] += assignment.license_quantity or 0

        capability_vendor_map: Dict[int, Set[str]] = defaultdict(set)
        for capability_id, providers in capability_providers.items():
            for vendor_name, _ in providers.values():
                capability_vendor_map[capability_id].add(vendor_name)

        vendor_gaps_addressable: Dict[str, int] = defaultdict(int)
        for entry in recommendation_report.product_comparison:
            vendor_gaps_addressable[entry.vendor] += entry.gaps_addressed

        vendor_summary: List[VendorOverlapSummary] = []
        for vendor_name, caps in vendor_capabilities.items():
            unique = sum(1 for c in caps if len(capability_vendor_map.get(c, ())) == 1)
            vendor_summary.append(
                VendorOverlapSummary(
                    vendor=vendor_name,
                    deployed_product_count=len(vendor_assignment_ids[vendor_name]),
                    total_capabilities_provided=len(caps),
                    unique_capabilities_provided=unique,
                    overlapping_capabilities_provided=len(caps) - unique,
                    total_license_quantity=vendor_license_quantity[vendor_name],
                    open_gaps_addressable=vendor_gaps_addressable.get(vendor_name, 0),
                )
            )
        vendor_summary.sort(key=lambda v: -v.total_capabilities_provided)

        # -- 8. Domain overlap scores (capability heatmap) ----------------------
        domain_overlap_scores: List[DomainOverlapScore] = []
        for domain_coverage in coverage.domain_coverage:
            duplicate_count = domain_duplicate_counts.get(domain_coverage.domain_id, 0)
            covered_count = domain_coverage.covered_count
            pct = round(duplicate_count / covered_count * 100, 2) if covered_count else 0.0
            domain_overlap_scores.append(
                DomainOverlapScore(
                    domain_id=domain_coverage.domain_id,
                    domain_name=domain_coverage.domain_name,
                    covered_count=covered_count,
                    duplicate_count=duplicate_count,
                    overlap_percentage=pct,
                )
            )
        domain_overlap_scores.sort(key=lambda d: d.domain_name)

        # -- Top-level metrics ----------------------------------------------------
        total_deployed_products = len(deployed)
        total_vendors = len(vendor_capabilities)
        duplicate_capability_count = len(duplicate_capabilities)
        covered_count = coverage.covered_capability_count
        overlap_percentage = (
            round(duplicate_capability_count / covered_count * 100, 2) if covered_count else 0.0
        )

        # Optimization score: 100 minus a blend of redundancy (overlap %) and
        # incompleteness (gap %) — a well-optimized deployment has neither.
        optimization_score = round(
            max(0.0, 100 - (overlap_percentage * 0.5 + gap_report.overall_gap_percentage * 0.5)),
            2,
        )

        vendors_in_cross_vendor_dupes: Set[str] = set()
        for dup in duplicate_capabilities:
            if dup.cross_vendor:
                for vendor_name, _ in capability_providers[dup.id].values():
                    vendors_in_cross_vendor_dupes.add(vendor_name)
        vendor_consolidation_score = (
            round(len(vendors_in_cross_vendor_dupes) / total_vendors * 100, 2)
            if total_vendors
            else 0.0
        )

        license_reduction_opportunity = sum(
            r.license_quantity or 0 for r in redundant_licenses if r.fully_redundant
        )
        total_license_quantity = sum(a.license_quantity or 0 for a in deployed)
        cost_optimization_score = (
            round(license_reduction_opportunity / total_license_quantity * 100, 2)
            if total_license_quantity
            else 0.0
        )

        distinct_deployment_models = {a.deployment_model for a in deployed}
        operational_complexity_score = round(
            min(
                total_vendors * 10
                + total_deployed_products * 2
                + len(distinct_deployment_models) * 5,
                100.0,
            ),
            2,
        )

        return OverlapReport(
            assessment_project_id=gap_report.assessment_project_id,
            assessment_project_name=gap_report.assessment_project_name,
            generated_at=datetime.now(timezone.utc),
            total_deployed_products=total_deployed_products,
            total_vendors=total_vendors,
            duplicate_capability_count=duplicate_capability_count,
            cross_vendor_duplicate_count=cross_vendor_duplicate_count,
            unused_capability_count=len(unused_capabilities),
            overlap_percentage=overlap_percentage,
            optimization_score=optimization_score,
            vendor_consolidation_score=vendor_consolidation_score,
            license_reduction_opportunity=license_reduction_opportunity,
            cost_optimization_score=cost_optimization_score,
            operational_complexity_score=operational_complexity_score,
            domain_overlap_scores=domain_overlap_scores,
            duplicate_capabilities=duplicate_capabilities,
            product_overlaps=product_overlaps,
            module_overlaps=module_overlaps,
            framework_overlaps=framework_overlaps,
            redundant_licenses=redundant_licenses,
            unused_capabilities=unused_capabilities,
            vendor_summary=vendor_summary,
        )

"""Scenario Simulation Engine (Sprint 11).

Lets an architect ask "what if?" about an assessment project's deployed
architecture — add/remove/replace a product, swap an edition, toggle a
module, change a licensing tier or deployment model or availability
status, or consolidate vendors/duplicate products — and see the exact
before/after impact on Coverage, Gap, Recommendation, and Overlap,
without ever touching the real assessment data.

This engine reuses :class:`CoverageEngine`, :class:`GapEngine`,
:class:`RecommendationEngine`, and :class:`OverlapEngine` completely
unmodified for both the "current" and "proposed" calculation passes —
no scoring logic is duplicated here. The only new logic in this module
is (a) applying one hypothetical mutation to in-memory ORM objects and
(b) diffing the two already-computed sets of reports into deltas.

Safety model: a hypothetical mutation is written with ``session.add()``
and ``session.flush()`` — never ``session.commit()`` — so the four
engines (which query through the same session) see it, but nothing is
durably persisted. A ``finally`` block unconditionally calls
``session.rollback()`` before this function returns, discarding the
flushed-but-uncommitted change whether or not an error occurred. This
was verified empirically against both SQLite and PostgreSQL: a plain
``session.commit()`` (e.g. the one ``BaseRepository.create/update/delete``
call) durably persists even inside a SAVEPOINT, whereas ``flush()`` +
``rollback()`` never does. That is why this engine reuses only the
side-effect-free validation helpers from ``ProductAssignmentService``
(``validate_references``, ``validate_duplicate``, ``_resolve_modules``)
and performs every mutation itself via plain ``session.add`` /
``session.delete`` / ``session.flush``, instead of calling that
service's committing ``create`` / ``update`` / ``delete`` methods.

Only the *computed report* of a simulation run is ever durably
persisted (as a ``SimulationRun`` row, purely so ``GET
/analysis/simulation/{id}`` can retrieve a past run) — that record
contains no assessment mutation, only the final read-only output.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from sqlmodel import Session

from app.core.exceptions import EntityNotFoundError, InvalidReferenceError
from app.engine.coverage_engine import CoverageEngine
from app.engine.gap_engine import GapEngine
from app.engine.overlap_engine import OverlapEngine
from app.engine.recommendation_engine import RecommendationEngine
from app.models.product_assignment import DeploymentStatus, ProductAssignment
from app.models.simulation_run import SimulationRun
from app.repositories.capability import CapabilityRepository
from app.repositories.module import ModuleRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.repositories.simulation_run import SimulationRunRepository
from app.schemas.coverage import CoverageReport
from app.schemas.overlap import OverlapReport
from app.schemas.product_assignment import (
    _validate_deployment_model,
    _validate_deployment_status,
)
from app.schemas.simulation import (
    CapabilityComparisonItem,
    ComparisonClassification,
    FrameworkComparisonItem,
    MetricComparison,
    ScenarioType,
    SimulationReport,
    SimulationRequest,
    VendorComparisonItem,
)
from app.services.assessment_project import AssessmentProjectService
from app.services.product_assignment import ProductAssignmentService

_EDITION_SWAP_SCENARIOS = {
    ScenarioType.UPGRADE_EDITION,
    ScenarioType.DOWNGRADE_EDITION,
    ScenarioType.CHANGE_LICENSING_TIER,
}
_BULK_REMOVE_SCENARIOS = {
    ScenarioType.CONSOLIDATE_VENDORS,
    ScenarioType.REMOVE_DUPLICATE_PRODUCTS,
}


def _require(value, field_name: str, scenario: ScenarioType):
    if value is None:
        raise InvalidReferenceError(
            f"scenario_type={scenario.value!r} requires '{field_name}'."
        )
    return value


def _validate_choice(value: str, validator_fn) -> str:
    """Reuses a Pydantic field-validator function outside of Pydantic's own
    validation context, translating its ``ValueError`` into the same
    ``InvalidReferenceError`` the rest of the service layer raises."""
    try:
        return validator_fn(value)
    except ValueError as exc:
        raise InvalidReferenceError(str(exc)) from exc


def _classify(
    current: float, proposed: float, higher_is_better: bool, epsilon: float = 1e-9
) -> ComparisonClassification:
    delta = proposed - current
    if abs(delta) < epsilon:
        return ComparisonClassification.NEUTRAL
    favorable = delta > 0 if higher_is_better else delta < 0
    return (
        ComparisonClassification.IMPROVEMENT
        if favorable
        else ComparisonClassification.REGRESSION
    )


def _metric_comparison(
    metric: str, current: float, proposed: float, higher_is_better: bool
) -> MetricComparison:
    current = round(float(current), 4)
    proposed = round(float(proposed), 4)
    delta = round(proposed - current, 4)
    percentage_change = round((delta / current * 100), 2) if current else (
        100.0 if proposed else 0.0
    )
    return MetricComparison(
        metric=metric,
        current_value=current,
        proposed_value=proposed,
        delta=delta,
        percentage_change=percentage_change,
        classification=_classify(current, proposed, higher_is_better),
    )


def _build_executive_summary(
    deltas: List[MetricComparison], scenario_type: ScenarioType, name: Optional[str]
) -> List[str]:
    """Deterministic, templated summary sentences built only from already
    -computed numbers — no generated text, no AI/LLM reasoning."""
    label = name or scenario_type.value.replace("_", " ").title()
    improvements = [d for d in deltas if d.classification == ComparisonClassification.IMPROVEMENT]
    regressions = [d for d in deltas if d.classification == ComparisonClassification.REGRESSION]
    neutral = [d for d in deltas if d.classification == ComparisonClassification.NEUTRAL]

    lines = [
        f"Scenario \"{label}\": {len(improvements)} of {len(deltas)} tracked metrics improved, "
        f"{len(regressions)} regressed, {len(neutral)} unchanged."
    ]
    for d in improvements:
        lines.append(
            f"Improved -- {d.metric}: {d.current_value} to {d.proposed_value} "
            f"({d.percentage_change:+.2f}%)."
        )
    for d in regressions:
        lines.append(
            f"Regressed -- {d.metric}: {d.current_value} to {d.proposed_value} "
            f"({d.percentage_change:+.2f}%)."
        )
    if not regressions:
        lines.append("No regressions detected across any tracked metric.")
    return lines


class SimulationEngine:
    """Computes a :class:`SimulationReport` for one hypothetical scenario
    applied to an assessment project, then persists it as a
    :class:`SimulationRun` so it can be retrieved later by id."""

    def __init__(self, session: Session):
        self.session = session
        self.assessment_project_service = AssessmentProjectService(session)
        self.assignment_service = ProductAssignmentService(session)
        self.assignment_repository = ProductAssignmentRepository(session)
        self.module_repository = ModuleRepository(session)
        self.capability_repository = CapabilityRepository(session)
        self.simulation_run_repository = SimulationRunRepository(session)
        self.coverage_engine = CoverageEngine(session)
        self.gap_engine = GapEngine(session)
        self.recommendation_engine = RecommendationEngine(session)
        self.overlap_engine = OverlapEngine(session)

    # ------------------------------------------------------------- mutation --

    def _get_assignment(self, assignment_id: int, assessment_project_id: int) -> ProductAssignment:
        assignment = self.assignment_repository.get(assignment_id)
        if assignment is None:
            raise EntityNotFoundError("ProductAssignment", assignment_id)
        if assignment.assessment_project_id != assessment_project_id:
            raise InvalidReferenceError(
                f"ProductAssignment {assignment_id} does not belong to assessment "
                f"project {assessment_project_id}."
            )
        return assignment

    def _add_assignment(self, request: SimulationRequest) -> ProductAssignment:
        scenario = request.scenario_type
        data = {
            "assessment_project_id": request.assessment_project_id,
            "vendor_id": _require(request.vendor_id, "vendor_id", scenario),
            "product_id": _require(request.product_id, "product_id", scenario),
            "edition_id": _require(request.edition_id, "edition_id", scenario),
            "environment_id": _require(request.environment_id, "environment_id", scenario),
            "license_quantity": request.license_quantity,
            "deployment_model": _validate_choice(
                _require(request.deployment_model, "deployment_model", scenario),
                _validate_deployment_model,
            ),
            # Only "Deployed" assignments count towards Coverage/Gap/Overlap
            # (see CoverageEngine) -- default new assignments to Deployed so
            # "add a product" actually shows up in the proposed state, unless
            # the caller explicitly wants to model a different status.
            "deployment_status": _validate_choice(
                request.deployment_status or DeploymentStatus.DEPLOYED.value,
                _validate_deployment_status,
            ),
            "notes": request.notes,
        }
        self.assignment_service.validate_references(data)
        self.assignment_service.validate_duplicate(data)
        modules = self.assignment_service._resolve_modules(
            request.module_ids or [], data["edition_id"]
        )
        obj = ProductAssignment(**data)
        obj.modules = modules
        self.session.add(obj)
        self.session.flush()
        return obj

    def _remove_assignment(self, request: SimulationRequest) -> None:
        assignment = self._get_assignment(
            _require(request.assignment_id, "assignment_id", request.scenario_type),
            request.assessment_project_id,
        )
        self.session.delete(assignment)
        self.session.flush()

    def _swap_edition(self, request: SimulationRequest) -> ProductAssignment:
        scenario = request.scenario_type
        assignment = self._get_assignment(
            _require(request.assignment_id, "assignment_id", scenario),
            request.assessment_project_id,
        )
        target_edition_id = _require(request.target_edition_id, "target_edition_id", scenario)
        if request.target_module_ids is None:
            raise InvalidReferenceError(
                f"scenario_type={scenario.value!r} requires 'target_module_ids' "
                "(pass an empty list to leave no modules enabled on the new edition)."
            )
        self.assignment_service.validate_references(
            {"product_id": assignment.product_id, "edition_id": target_edition_id}
        )
        self.assignment_service.validate_duplicate(
            {
                "assessment_project_id": assignment.assessment_project_id,
                "edition_id": target_edition_id,
                "environment_id": assignment.environment_id,
            },
            exclude_id=assignment.id,
        )
        assignment.edition_id = target_edition_id
        assignment.modules = self.assignment_service._resolve_modules(
            request.target_module_ids, target_edition_id
        )
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def _toggle_module(self, request: SimulationRequest, enable: bool) -> ProductAssignment:
        scenario = request.scenario_type
        assignment = self._get_assignment(
            _require(request.assignment_id, "assignment_id", scenario),
            request.assessment_project_id,
        )
        module_id = _require(request.module_id, "module_id", scenario)
        module = self.module_repository.get(module_id)
        if module is None:
            raise InvalidReferenceError(f"Module with id={module_id} does not exist.")
        if module.edition_id != assignment.edition_id:
            raise InvalidReferenceError(
                f"Module {module_id} does not belong to edition {assignment.edition_id}."
            )
        current_ids = {m.id for m in assignment.modules}
        if enable:
            if module_id not in current_ids:
                assignment.modules = [*assignment.modules, module]
        else:
            assignment.modules = [m for m in assignment.modules if m.id != module_id]
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def _change_deployment_model(self, request: SimulationRequest) -> ProductAssignment:
        scenario = request.scenario_type
        assignment = self._get_assignment(
            _require(request.assignment_id, "assignment_id", scenario),
            request.assessment_project_id,
        )
        assignment.deployment_model = _validate_choice(
            _require(request.deployment_model, "deployment_model", scenario),
            _validate_deployment_model,
        )
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def _change_availability_status(self, request: SimulationRequest) -> ProductAssignment:
        """"Change Availability Status" maps onto
        ``ProductAssignment.deployment_status`` (Not Started / In Progress /
        Deployed / Decommissioned) -- the only availability-style field that
        actually exists on an assessment's product assignment.
        ``availability_status`` (Generally Available / Beta / EOL / ...) is a
        vendor-catalog attribute of ``ProductCapabilityMapping`` and is not
        something an assessment can toggle."""
        scenario = request.scenario_type
        assignment = self._get_assignment(
            _require(request.assignment_id, "assignment_id", scenario),
            request.assessment_project_id,
        )
        assignment.deployment_status = _validate_choice(
            _require(request.deployment_status, "deployment_status", scenario),
            _validate_deployment_status,
        )
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def _bulk_remove(self, request: SimulationRequest) -> None:
        scenario = request.scenario_type
        assignment_ids = request.assignment_ids
        if not assignment_ids:
            raise InvalidReferenceError(
                f"scenario_type={scenario.value!r} requires a non-empty 'assignment_ids' list."
            )
        for assignment_id in assignment_ids:
            assignment = self._get_assignment(assignment_id, request.assessment_project_id)
            self.session.delete(assignment)
        self.session.flush()

    def _apply_scenario(self, request: SimulationRequest) -> None:
        scenario = request.scenario_type
        if scenario == ScenarioType.ADD_PRODUCT:
            self._add_assignment(request)
        elif scenario == ScenarioType.REMOVE_PRODUCT:
            self._remove_assignment(request)
        elif scenario == ScenarioType.REPLACE_PRODUCT:
            self._remove_assignment(request)
            self._add_assignment(request)
        elif scenario in _EDITION_SWAP_SCENARIOS:
            self._swap_edition(request)
        elif scenario == ScenarioType.ENABLE_MODULE:
            self._toggle_module(request, enable=True)
        elif scenario == ScenarioType.DISABLE_MODULE:
            self._toggle_module(request, enable=False)
        elif scenario == ScenarioType.CHANGE_DEPLOYMENT_MODEL:
            self._change_deployment_model(request)
        elif scenario == ScenarioType.CHANGE_AVAILABILITY_STATUS:
            self._change_availability_status(request)
        elif scenario in _BULK_REMOVE_SCENARIOS:
            self._bulk_remove(request)
        else:  # pragma: no cover - unreachable given the ScenarioType enum
            raise InvalidReferenceError(f"Unsupported scenario_type: {scenario}")

    # ---------------------------------------------------------- comparison --

    def _build_framework_index(self) -> Dict[int, List[Tuple[str, str]]]:
        index: Dict[int, List[Tuple[str, str]]] = {}
        for capability in self.capability_repository.all():
            index[capability.id] = [
                (m.framework.name, m.framework.version) for m in capability.framework_mappings
            ]
        return index

    def _framework_coverage_percentage(
        self, framework_index: Dict[int, List[Tuple[str, str]]], covered_ids: Set[int]
    ) -> float:
        total = 0
        satisfied = 0
        for capability_id, frameworks in framework_index.items():
            for _ in frameworks:
                total += 1
                if capability_id in covered_ids:
                    satisfied += 1
        return round(satisfied / total * 100, 2) if total else 0.0

    def _framework_comparison(
        self,
        framework_index: Dict[int, List[Tuple[str, str]]],
        current_ids: Set[int],
        proposed_ids: Set[int],
    ) -> List[FrameworkComparisonItem]:
        totals: Dict[Tuple[str, str], int] = {}
        current_sat: Dict[Tuple[str, str], int] = {}
        proposed_sat: Dict[Tuple[str, str], int] = {}
        for capability_id, frameworks in framework_index.items():
            for key in frameworks:
                totals[key] = totals.get(key, 0) + 1
                if capability_id in current_ids:
                    current_sat[key] = current_sat.get(key, 0) + 1
                if capability_id in proposed_ids:
                    proposed_sat[key] = proposed_sat.get(key, 0) + 1

        items = []
        for key, total in totals.items():
            name, version = key
            current_count = current_sat.get(key, 0)
            proposed_count = proposed_sat.get(key, 0)
            items.append(
                FrameworkComparisonItem(
                    framework_name=name,
                    framework_version=version,
                    total_controls=total,
                    current_satisfied_controls=current_count,
                    proposed_satisfied_controls=proposed_count,
                    classification=_classify(current_count, proposed_count, higher_is_better=True),
                )
            )
        items.sort(key=lambda f: (f.framework_name, f.framework_version))
        return items

    def _capability_comparison(
        self, current_coverage: CoverageReport, proposed_coverage: CoverageReport
    ) -> List[CapabilityComparisonItem]:
        current_by_id = {
            c.id: c for c in current_coverage.covered_capabilities + current_coverage.missing_capabilities
        }
        proposed_by_id = {
            c.id: c
            for c in proposed_coverage.covered_capabilities + proposed_coverage.missing_capabilities
        }
        items: List[CapabilityComparisonItem] = []
        for capability_id, current_item in current_by_id.items():
            proposed_item = proposed_by_id.get(capability_id)
            if proposed_item is None:
                continue
            classification = _classify(
                float(current_item.covered), float(proposed_item.covered), higher_is_better=True
            )
            unchanged = (
                classification == ComparisonClassification.NEUTRAL
                and current_item.provider_count == proposed_item.provider_count
            )
            if unchanged:
                continue
            items.append(
                CapabilityComparisonItem(
                    id=current_item.id,
                    code=current_item.code,
                    name=current_item.name,
                    domain_name=current_item.domain_name,
                    current_covered=current_item.covered,
                    proposed_covered=proposed_item.covered,
                    current_provider_count=current_item.provider_count,
                    proposed_provider_count=proposed_item.provider_count,
                    classification=classification,
                )
            )
        items.sort(
            key=lambda c: (c.classification != ComparisonClassification.IMPROVEMENT, c.code)
        )
        return items

    def _vendor_comparison(
        self, current_overlap: OverlapReport, proposed_overlap: OverlapReport
    ) -> List[VendorComparisonItem]:
        current_by_vendor = {v.vendor: v for v in current_overlap.vendor_summary}
        proposed_by_vendor = {v.vendor: v for v in proposed_overlap.vendor_summary}
        items: List[VendorComparisonItem] = []
        for vendor in sorted(set(current_by_vendor) | set(proposed_by_vendor)):
            current = current_by_vendor.get(vendor)
            proposed = proposed_by_vendor.get(vendor)
            current_caps = current.total_capabilities_provided if current else 0
            proposed_caps = proposed.total_capabilities_provided if proposed else 0
            current_lic = current.total_license_quantity if current else 0
            proposed_lic = proposed.total_license_quantity if proposed else 0
            if (
                (current is not None) == (proposed is not None)
                and current_caps == proposed_caps
                and current_lic == proposed_lic
            ):
                continue
            items.append(
                VendorComparisonItem(
                    vendor=vendor,
                    current_deployed=current is not None,
                    proposed_deployed=proposed is not None,
                    current_capability_count=current_caps,
                    proposed_capability_count=proposed_caps,
                    current_license_quantity=current_lic,
                    proposed_license_quantity=proposed_lic,
                    classification=_classify(current_caps, proposed_caps, higher_is_better=True),
                )
            )
        return items

    # -------------------------------------------------------------- public --

    def simulate(self, request: SimulationRequest) -> SimulationReport:
        project = self.assessment_project_service.get(request.assessment_project_id)
        project_id = project.id
        project_name = project.name

        current_coverage = self.coverage_engine.calculate(request.assessment_project_id)
        current_gap = self.gap_engine.calculate(request.assessment_project_id)
        current_recommendation = self.recommendation_engine.calculate(request.assessment_project_id)
        current_overlap = self.overlap_engine.calculate(request.assessment_project_id)

        try:
            self._apply_scenario(request)
            proposed_coverage = self.coverage_engine.calculate(request.assessment_project_id)
            proposed_gap = self.gap_engine.calculate(request.assessment_project_id)
            proposed_recommendation = self.recommendation_engine.calculate(
                request.assessment_project_id
            )
            proposed_overlap = self.overlap_engine.calculate(request.assessment_project_id)
        finally:
            # Whether the block above succeeded or raised, the hypothetical
            # mutation is only ever flushed, never committed -- rolling back
            # here guarantees the real assessment is untouched either way.
            self.session.rollback()

        framework_index = self._build_framework_index()
        current_covered_ids = {c.id for c in current_coverage.covered_capabilities}
        proposed_covered_ids = {c.id for c in proposed_coverage.covered_capabilities}
        current_fw_pct = self._framework_coverage_percentage(framework_index, current_covered_ids)
        proposed_fw_pct = self._framework_coverage_percentage(framework_index, proposed_covered_ids)

        current_license_total = sum(v.total_license_quantity for v in current_overlap.vendor_summary)
        proposed_license_total = sum(
            v.total_license_quantity for v in proposed_overlap.vendor_summary
        )

        coverage_delta = _metric_comparison(
            "Overall Coverage %",
            current_coverage.overall_coverage_percentage,
            proposed_coverage.overall_coverage_percentage,
            higher_is_better=True,
        )
        gap_delta = _metric_comparison(
            "Overall Gap %",
            current_gap.overall_gap_percentage,
            proposed_gap.overall_gap_percentage,
            higher_is_better=False,
        )
        overlap_delta = _metric_comparison(
            "Overlap %",
            current_overlap.overlap_percentage,
            proposed_overlap.overlap_percentage,
            higher_is_better=False,
        )
        recommendation_delta = _metric_comparison(
            "Estimated Remaining Risk Reduction Potential",
            current_recommendation.estimated_overall_risk_reduction,
            proposed_recommendation.estimated_overall_risk_reduction,
            higher_is_better=False,
        )
        risk_delta = _metric_comparison(
            "Overall Risk Score",
            current_gap.overall_risk_score,
            proposed_gap.overall_risk_score,
            higher_is_better=False,
        )
        cost_delta = _metric_comparison(
            "Cost Optimization Score",
            current_overlap.cost_optimization_score,
            proposed_overlap.cost_optimization_score,
            higher_is_better=False,
        )
        complexity_delta = _metric_comparison(
            "Operational Complexity Score",
            current_overlap.operational_complexity_score,
            proposed_overlap.operational_complexity_score,
            higher_is_better=False,
        )
        vendor_count_delta = _metric_comparison(
            "Total Vendors",
            current_overlap.total_vendors,
            proposed_overlap.total_vendors,
            higher_is_better=False,
        )
        license_count_delta = _metric_comparison(
            "Total License Quantity",
            current_license_total,
            proposed_license_total,
            higher_is_better=False,
        )
        framework_coverage_delta = _metric_comparison(
            "Framework Coverage %", current_fw_pct, proposed_fw_pct, higher_is_better=True
        )

        deltas = [
            coverage_delta,
            gap_delta,
            overlap_delta,
            recommendation_delta,
            risk_delta,
            cost_delta,
            complexity_delta,
            vendor_count_delta,
            license_count_delta,
            framework_coverage_delta,
        ]
        executive_summary = _build_executive_summary(deltas, request.scenario_type, request.name)
        capability_comparison = self._capability_comparison(current_coverage, proposed_coverage)
        vendor_comparison = self._vendor_comparison(current_overlap, proposed_overlap)
        framework_comparison = self._framework_comparison(
            framework_index, current_covered_ids, proposed_covered_ids
        )

        run = SimulationRun(
            assessment_project_id=project_id,
            scenario_type=request.scenario_type.value,
            name=request.name,
            request_json=request.model_dump_json(),
            report_json="",
        )
        self.session.add(run)
        self.session.flush()

        report = SimulationReport(
            id=run.id,
            assessment_project_id=project_id,
            assessment_project_name=project_name,
            scenario_type=request.scenario_type,
            name=request.name,
            generated_at=datetime.now(timezone.utc),
            coverage_delta=coverage_delta,
            gap_delta=gap_delta,
            overlap_delta=overlap_delta,
            recommendation_delta=recommendation_delta,
            risk_delta=risk_delta,
            cost_delta=cost_delta,
            complexity_delta=complexity_delta,
            vendor_count_delta=vendor_count_delta,
            license_count_delta=license_count_delta,
            framework_coverage_delta=framework_coverage_delta,
            executive_summary=executive_summary,
            current_coverage=current_coverage,
            proposed_coverage=proposed_coverage,
            current_gap=current_gap,
            proposed_gap=proposed_gap,
            current_recommendation=current_recommendation,
            proposed_recommendation=proposed_recommendation,
            current_overlap=current_overlap,
            proposed_overlap=proposed_overlap,
            capability_comparison=capability_comparison,
            vendor_comparison=vendor_comparison,
            framework_comparison=framework_comparison,
        )
        run.report_json = report.model_dump_json()
        self.session.add(run)
        self.session.commit()

        return report

    def get(self, simulation_id: int) -> SimulationReport:
        run = self.simulation_run_repository.get(simulation_id)
        if run is None:
            raise EntityNotFoundError("SimulationRun", simulation_id)
        return SimulationReport.model_validate_json(run.report_json)

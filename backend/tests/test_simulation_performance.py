import time

from app.engine.simulation_engine import SimulationEngine
from app.repositories.edition import EditionRepository
from app.repositories.environment import EnvironmentRepository
from app.repositories.product import ProductRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.repositories.vendor import VendorRepository
from app.schemas.simulation import ScenarioType, SimulationRequest
from tests.test_gap_performance import _seed_bulk_catalog


def test_simulation_engine_completes_quickly_at_scale(session):
    project_id = _seed_bulk_catalog(session)

    # Remove one deployed vendor's assignments -- a consolidate_vendors-style
    # bulk removal -- and re-run all four engines over the resulting state.
    assignments = ProductAssignmentRepository(session).list_by_assessment_project(project_id)
    assert assignments
    target_vendor_id = assignments[0].vendor_id
    assignment_ids = [a.id for a in assignments if a.vendor_id == target_vendor_id]

    request = SimulationRequest(
        assessment_project_id=project_id,
        scenario_type=ScenarioType.CONSOLIDATE_VENDORS,
        assignment_ids=assignment_ids,
    )

    start = time.perf_counter()
    report = SimulationEngine(session).simulate(request)
    elapsed = time.perf_counter() - start

    assert report.id is not None
    assert report.current_overlap.total_vendors >= report.proposed_overlap.total_vendors
    for delta in (
        report.coverage_delta,
        report.gap_delta,
        report.overlap_delta,
        report.risk_delta,
    ):
        assert delta.metric

    # Real data must be unaffected by the simulation.
    real_assignments = ProductAssignmentRepository(session).list_by_assessment_project(project_id)
    assert len(real_assignments) == len(assignments)

    # Generous threshold — this simulation runs all four engines twice, so
    # it is a regression guard against accidental N+1 queries, not a strict
    # benchmark.
    assert elapsed < 10.0, f"SimulationEngine.simulate took too long: {elapsed:.2f}s"


def test_add_product_simulation_completes_quickly_at_scale(session):
    project_id = _seed_bulk_catalog(session)

    vendor = VendorRepository(session).list(skip=0, limit=1)[0][0]
    product = ProductRepository(session).list(
        skip=0, limit=1, filters={"vendor_id": vendor.id}
    )[0][0]
    edition = EditionRepository(session).list(
        skip=0, limit=1, filters={"product_id": product.id}
    )[0][0]
    environment = EnvironmentRepository(session).list(skip=0, limit=1)[0][0]

    request = SimulationRequest(
        assessment_project_id=project_id,
        scenario_type=ScenarioType.ADD_PRODUCT,
        vendor_id=vendor.id,
        product_id=product.id,
        edition_id=edition.id,
        environment_id=environment.id,
        deployment_model="Agent",
    )

    start = time.perf_counter()
    report = SimulationEngine(session).simulate(request)
    elapsed = time.perf_counter() - start

    assert report.id is not None
    assert elapsed < 10.0, f"SimulationEngine.simulate took too long: {elapsed:.2f}s"

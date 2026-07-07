import pytest

from app.core.exceptions import EntityNotFoundError, InvalidReferenceError
from app.engine.coverage_engine import CoverageEngine
from app.engine.simulation_engine import SimulationEngine
from app.repositories.product_assignment import ProductAssignmentRepository
from app.schemas.simulation import ComparisonClassification, ScenarioType, SimulationRequest


def _make_domain(client, domain_name):
    return client.post("/domains", json={"name": domain_name}).json()


def _make_capability(client, domain, code):
    return client.post(
        "/capabilities", json={"name": f"Cap {code}", "code": code, "domain_id": domain["id"]}
    ).json()


def _make_hierarchy(client, suffix="1"):
    vendor = client.post("/vendors", json={"name": f"Vendor{suffix}"}).json()
    product = client.post(
        "/products", json={"name": f"Product{suffix}", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": f"Edition{suffix}", "product_id": product["id"]}
    ).json()
    return vendor, product, edition


def _make_module(client, edition, capability_ids, suffix="1"):
    return client.post(
        "/modules",
        json={
            "name": f"Module{suffix}",
            "edition_id": edition["id"],
            "capability_ids": capability_ids,
        },
    ).json()


def _make_customer_project(client, suffix="1"):
    customer = client.post("/customers", json={"name": f"Customer{suffix}"}).json()
    environment = client.post(
        "/environments",
        json={
            "name": f"Production{suffix}",
            "environment_type": "Production",
            "customer_id": customer["id"],
        },
    ).json()
    project = client.post(
        "/assessment-projects",
        json={"name": f"Assessment{suffix}", "customer_id": customer["id"]},
    ).json()
    return customer, environment, project


def _deploy(client, project, environment, vendor, product, edition, module, **overrides):
    payload = {
        "assessment_project_id": project["id"],
        "vendor_id": vendor["id"],
        "product_id": product["id"],
        "edition_id": edition["id"],
        "environment_id": environment["id"],
        "module_ids": [module["id"]] if module else [],
        "deployment_model": "Agent",
        "deployment_status": "Deployed",
    }
    payload.update(overrides)
    return client.post("/product-assignments", json=payload).json()


def test_add_product_scenario_improves_coverage_without_persisting(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "SIM-001")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _, environment, project = _make_customer_project(client)

    before_count = len(
        ProductAssignmentRepository(session).list_by_assessment_project(project["id"])
    )
    current = CoverageEngine(session).calculate(project["id"])
    assert current.overall_coverage_percentage == 0.0

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.ADD_PRODUCT,
        vendor_id=vendor["id"],
        product_id=product["id"],
        edition_id=edition["id"],
        environment_id=environment["id"],
        module_ids=[module["id"]],
        deployment_model="Agent",
    )
    report = SimulationEngine(session).simulate(request)

    assert report.proposed_coverage.overall_coverage_percentage == 100.0
    assert report.coverage_delta.classification == ComparisonClassification.IMPROVEMENT
    assert report.coverage_delta.delta > 0

    # The real assessment must be untouched: same assignment count, same
    # (unaffected) coverage, whether queried via a fresh engine call or the
    # repository directly.
    after_count = len(
        ProductAssignmentRepository(session).list_by_assessment_project(project["id"])
    )
    assert after_count == before_count
    real_coverage = CoverageEngine(session).calculate(project["id"])
    assert real_coverage.overall_coverage_percentage == 0.0


def test_remove_product_scenario_regresses_coverage(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "SIM-002")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _, environment, project = _make_customer_project(client)
    assignment = _deploy(client, project, environment, vendor, product, edition, module)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.REMOVE_PRODUCT,
        assignment_id=assignment["id"],
    )
    report = SimulationEngine(session).simulate(request)

    assert report.current_coverage.overall_coverage_percentage == 100.0
    assert report.proposed_coverage.overall_coverage_percentage == 0.0
    assert report.coverage_delta.classification == ComparisonClassification.REGRESSION

    # Real assignment still exists.
    real_assignments = ProductAssignmentRepository(session).list_by_assessment_project(
        project["id"]
    )
    assert len(real_assignments) == 1


def test_enable_module_scenario_improves_coverage(client, session):
    domain = _make_domain(client, "Endpoint Security")
    enabled_capability = _make_capability(client, domain, "SIM-003")
    extra_capability = _make_capability(client, domain, "SIM-004")
    vendor, product, edition = _make_hierarchy(client, "A")
    enabled_module = _make_module(client, edition, [enabled_capability["id"]], "Enabled")
    extra_module = _make_module(client, edition, [extra_capability["id"]], "Extra")
    _, environment, project = _make_customer_project(client)
    assignment = _deploy(client, project, environment, vendor, product, edition, enabled_module)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.ENABLE_MODULE,
        assignment_id=assignment["id"],
        module_id=extra_module["id"],
    )
    report = SimulationEngine(session).simulate(request)

    assert report.current_coverage.covered_capability_count == 1
    assert report.proposed_coverage.covered_capability_count == 2
    assert report.coverage_delta.classification == ComparisonClassification.IMPROVEMENT


def test_disable_module_scenario_regresses_coverage(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability_a = _make_capability(client, domain, "SIM-005")
    capability_b = _make_capability(client, domain, "SIM-006")
    vendor, product, edition = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition, [capability_a["id"]], "A")
    module_b = _make_module(client, edition, [capability_b["id"]], "B")
    _, environment, project = _make_customer_project(client)
    assignment = client.post(
        "/product-assignments",
        json={
            "assessment_project_id": project["id"],
            "vendor_id": vendor["id"],
            "product_id": product["id"],
            "edition_id": edition["id"],
            "environment_id": environment["id"],
            "module_ids": [module_a["id"], module_b["id"]],
            "deployment_model": "Agent",
            "deployment_status": "Deployed",
        },
    ).json()

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.DISABLE_MODULE,
        assignment_id=assignment["id"],
        module_id=module_b["id"],
    )
    report = SimulationEngine(session).simulate(request)

    assert report.current_coverage.covered_capability_count == 2
    assert report.proposed_coverage.covered_capability_count == 1
    assert report.coverage_delta.classification == ComparisonClassification.REGRESSION


def test_upgrade_edition_requires_target_module_ids(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "SIM-007")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    other_edition = client.post(
        "/editions", json={"name": "Premium", "product_id": product["id"]}
    ).json()
    _, environment, project = _make_customer_project(client)
    assignment = _deploy(client, project, environment, vendor, product, edition, module)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.UPGRADE_EDITION,
        assignment_id=assignment["id"],
        target_edition_id=other_edition["id"],
    )
    with pytest.raises(InvalidReferenceError):
        SimulationEngine(session).simulate(request)


def test_upgrade_edition_scenario_swaps_modules(client, session):
    domain = _make_domain(client, "Endpoint Security")
    old_capability = _make_capability(client, domain, "SIM-008")
    new_capability = _make_capability(client, domain, "SIM-009")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [old_capability["id"]], "A")
    premium_edition = client.post(
        "/editions", json={"name": "Premium", "product_id": product["id"]}
    ).json()
    premium_module = _make_module(client, premium_edition, [new_capability["id"]], "Premium")
    _, environment, project = _make_customer_project(client)
    assignment = _deploy(client, project, environment, vendor, product, edition, module)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.UPGRADE_EDITION,
        assignment_id=assignment["id"],
        target_edition_id=premium_edition["id"],
        target_module_ids=[premium_module["id"]],
    )
    report = SimulationEngine(session).simulate(request)

    proposed_codes = {c.code for c in report.proposed_coverage.covered_capabilities}
    assert proposed_codes == {"SIM-009"}


def test_change_availability_status_to_decommissioned_regresses_coverage(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "SIM-010")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _, environment, project = _make_customer_project(client)
    assignment = _deploy(client, project, environment, vendor, product, edition, module)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.CHANGE_AVAILABILITY_STATUS,
        assignment_id=assignment["id"],
        deployment_status="Decommissioned",
    )
    report = SimulationEngine(session).simulate(request)

    assert report.proposed_coverage.overall_coverage_percentage == 0.0
    assert report.coverage_delta.classification == ComparisonClassification.REGRESSION


def test_consolidate_vendors_bulk_remove(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "SIM-011")
    vendor_a, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    vendor_b, product_b, edition_b = _make_hierarchy(client, "B")
    module_b = _make_module(client, edition_b, [capability["id"]], "B")
    _, environment, project = _make_customer_project(client)
    assignment_a = _deploy(client, project, environment, vendor_a, product_a, edition_a, module_a)
    assignment_b = _deploy(client, project, environment, vendor_b, product_b, edition_b, module_b)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.CONSOLIDATE_VENDORS,
        assignment_ids=[assignment_b["id"]],
    )
    report = SimulationEngine(session).simulate(request)

    assert report.current_overlap.total_vendors == 2
    assert report.proposed_overlap.total_vendors == 1
    assert report.vendor_count_delta.classification == ComparisonClassification.IMPROVEMENT

    real_assignments = ProductAssignmentRepository(session).list_by_assessment_project(
        project["id"]
    )
    assert {a["id"] for a in [assignment_a, assignment_b]} == {a.id for a in real_assignments}


def test_simulation_report_persisted_and_retrievable_by_id(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "SIM-012")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _, environment, project = _make_customer_project(client)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.ADD_PRODUCT,
        name="Add EDR",
        vendor_id=vendor["id"],
        product_id=product["id"],
        edition_id=edition["id"],
        environment_id=environment["id"],
        module_ids=[module["id"]],
        deployment_model="Agent",
    )
    report = SimulationEngine(session).simulate(request)

    fetched = SimulationEngine(session).get(report.id)
    assert fetched.id == report.id
    assert fetched.name == "Add EDR"
    assert fetched.coverage_delta.proposed_value == report.coverage_delta.proposed_value


def test_simulation_engine_raises_for_unknown_simulation_id(session):
    with pytest.raises(EntityNotFoundError):
        SimulationEngine(session).get(999999)


def test_simulation_engine_raises_for_unknown_assessment_project(session):
    request = SimulationRequest(
        assessment_project_id=999999,
        scenario_type=ScenarioType.ADD_PRODUCT,
    )
    with pytest.raises(EntityNotFoundError):
        SimulationEngine(session).simulate(request)


def test_add_product_missing_required_field_rolls_back_cleanly(client, session):
    _, environment, project = _make_customer_project(client)

    request = SimulationRequest(
        assessment_project_id=project["id"],
        scenario_type=ScenarioType.ADD_PRODUCT,
        environment_id=environment["id"],
        # vendor_id/product_id/edition_id intentionally omitted
    )
    with pytest.raises(InvalidReferenceError):
        SimulationEngine(session).simulate(request)

    # Failing mid-scenario must not leave any partial assignment behind.
    real_assignments = ProductAssignmentRepository(session).list_by_assessment_project(
        project["id"]
    )
    assert real_assignments == []

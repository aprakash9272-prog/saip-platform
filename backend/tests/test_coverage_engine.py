import pytest

from app.core.exceptions import EntityNotFoundError
from app.engine.coverage_engine import CoverageEngine


def _build_catalog(client):
    """Two domains, three capabilities: D1 has C1 (EDR-001) + C2 (EDR-002),
    D2 has C3 (TI-001). One module (in one edition) provides only C1."""
    d1 = client.post("/domains", json={"name": "Endpoint Security"}).json()
    d2 = client.post("/domains", json={"name": "Threat Intelligence"}).json()
    c1 = client.post(
        "/capabilities", json={"name": "EDR", "code": "EDR-001", "domain_id": d1["id"]}
    ).json()
    c2 = client.post(
        "/capabilities", json={"name": "EDR2", "code": "EDR-002", "domain_id": d1["id"]}
    ).json()
    c3 = client.post(
        "/capabilities", json={"name": "TI", "code": "TI-001", "domain_id": d2["id"]}
    ).json()

    vendor = client.post("/vendors", json={"name": "Acme"}).json()
    product = client.post(
        "/products", json={"name": "Shield", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": "Pro", "product_id": product["id"]}
    ).json()
    module = client.post(
        "/modules",
        json={"name": "Detector", "edition_id": edition["id"], "capability_ids": [c1["id"]]},
    ).json()
    return {
        "domains": (d1, d2),
        "capabilities": (c1, c2, c3),
        "vendor": vendor,
        "product": product,
        "edition": edition,
        "module": module,
    }


def _build_customer_project(client, suffix="1"):
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


def _assign(client, project, catalog, environment, deployment_status="Deployed", vendor=None, product=None, edition=None, module=None):
    vendor = vendor or catalog["vendor"]
    product = product or catalog["product"]
    edition = edition or catalog["edition"]
    module = module or catalog["module"]
    return client.post(
        "/product-assignments",
        json={
            "assessment_project_id": project["id"],
            "vendor_id": vendor["id"],
            "product_id": product["id"],
            "edition_id": edition["id"],
            "environment_id": environment["id"],
            "module_ids": [module["id"]],
            "deployment_model": "Agent",
            "deployment_status": deployment_status,
        },
    ).json()


def test_coverage_calculates_covered_and_missing_capabilities(client, session):
    catalog = _build_catalog(client)
    _, environment, project = _build_customer_project(client)
    _assign(client, project, catalog, environment, deployment_status="Deployed")

    report = CoverageEngine(session).calculate(project["id"])

    assert report.total_capabilities == 3
    assert report.covered_capability_count == 1
    assert report.missing_capability_count == 2
    assert report.duplicate_capability_count == 0
    assert report.overall_coverage_percentage == round(1 / 3 * 100, 2)

    covered_codes = {c.code for c in report.covered_capabilities}
    missing_codes = {c.code for c in report.missing_capabilities}
    assert covered_codes == {"EDR-001"}
    assert missing_codes == {"EDR-002", "TI-001"}

    domain_by_name = {d.domain_name: d for d in report.domain_coverage}
    assert domain_by_name["Endpoint Security"].covered_count == 1
    assert domain_by_name["Endpoint Security"].total_count == 2
    assert domain_by_name["Endpoint Security"].coverage_percentage == 50.0
    assert domain_by_name["Threat Intelligence"].covered_count == 0
    assert domain_by_name["Threat Intelligence"].total_count == 1
    assert domain_by_name["Threat Intelligence"].coverage_percentage == 0.0


def test_coverage_ignores_non_deployed_assignments(client, session):
    catalog = _build_catalog(client)
    _, environment, project = _build_customer_project(client)
    _assign(client, project, catalog, environment, deployment_status="Not Started")

    report = CoverageEngine(session).calculate(project["id"])

    assert report.covered_capability_count == 0
    assert report.missing_capability_count == 3
    assert report.overall_coverage_percentage == 0.0


def test_coverage_detects_duplicate_capabilities_across_assignments(client, session):
    catalog = _build_catalog(client)
    _, environment, project = _build_customer_project(client)

    # Second vendor/product/edition/module also providing EDR-001.
    vendor_b = client.post("/vendors", json={"name": "Globex"}).json()
    product_b = client.post(
        "/products", json={"name": "Guard", "vendor_id": vendor_b["id"]}
    ).json()
    edition_b = client.post(
        "/editions", json={"name": "Standard", "product_id": product_b["id"]}
    ).json()
    module_b = client.post(
        "/modules",
        json={
            "name": "Detector B",
            "edition_id": edition_b["id"],
            "capability_ids": [catalog["capabilities"][0]["id"]],
        },
    ).json()

    _assign(client, project, catalog, environment, deployment_status="Deployed")
    _assign(
        client,
        project,
        catalog,
        environment,
        deployment_status="Deployed",
        vendor=vendor_b,
        product=product_b,
        edition=edition_b,
        module=module_b,
    )

    report = CoverageEngine(session).calculate(project["id"])

    assert report.duplicate_capability_count == 1
    duplicate = report.duplicate_capabilities[0]
    assert duplicate.code == "EDR-001"
    assert duplicate.provider_count == 2
    assert len(duplicate.providers) == 2


def test_coverage_same_assignment_multiple_modules_is_not_a_duplicate(client, session):
    catalog = _build_catalog(client)
    _, environment, project = _build_customer_project(client)

    # A second module on the SAME edition also covers EDR-001.
    second_module = client.post(
        "/modules",
        json={
            "name": "Detector Two",
            "edition_id": catalog["edition"]["id"],
            "capability_ids": [catalog["capabilities"][0]["id"]],
        },
    ).json()

    client.post(
        "/product-assignments",
        json={
            "assessment_project_id": project["id"],
            "vendor_id": catalog["vendor"]["id"],
            "product_id": catalog["product"]["id"],
            "edition_id": catalog["edition"]["id"],
            "environment_id": environment["id"],
            "module_ids": [catalog["module"]["id"], second_module["id"]],
            "deployment_model": "Agent",
            "deployment_status": "Deployed",
        },
    )

    report = CoverageEngine(session).calculate(project["id"])

    assert report.duplicate_capability_count == 0
    covered = next(c for c in report.covered_capabilities if c.code == "EDR-001")
    assert covered.provider_count == 1


def test_coverage_raises_for_unknown_assessment_project(session):
    with pytest.raises(EntityNotFoundError):
        CoverageEngine(session).calculate(999999)

import pytest

from app.core.exceptions import EntityNotFoundError
from app.engine.overlap_engine import OverlapEngine


def _make_domain(client, domain_name):
    return client.post("/domains", json={"name": domain_name}).json()


def _make_capability(client, domain, code, risk_category=None):
    payload = {"name": f"Cap {code}", "code": code, "domain_id": domain["id"]}
    if risk_category is not None:
        payload["risk_category"] = risk_category
    return client.post("/capabilities", json=payload).json()


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
        json={"name": f"Module{suffix}", "edition_id": edition["id"], "capability_ids": capability_ids},
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
        "module_ids": [module["id"]],
        "deployment_model": "Agent",
        "deployment_status": "Deployed",
    }
    payload.update(overrides)
    return client.post("/product-assignments", json=payload).json()


def _map_product_to_capability(client, vendor, product, edition, module, capability, **overrides):
    payload = {
        "vendor_id": vendor["id"],
        "product_id": product["id"],
        "edition_id": edition["id"],
        "module_id": module["id"],
        "capability_id": capability["id"],
        "deployment_model": "SaaS",
        "availability_status": "Generally Available",
    }
    payload.update(overrides)
    return client.post("/product-mappings", json=payload).json()


def _make_framework(client, name, version="1.0"):
    return client.post("/frameworks", json={"name": name, "version": version}).json()


def _map_control(client, capability, framework, control_id):
    client.post(
        "/mappings",
        json={
            "capability_id": capability["id"],
            "framework_id": framework["id"],
            "control_id": control_id,
            "control_name": f"Control {control_id}",
        },
    )


def test_no_overlap_with_single_deployed_product(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-001")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product, edition, module)

    report = OverlapEngine(session).calculate(project["id"])

    assert report.duplicate_capability_count == 0
    assert report.cross_vendor_duplicate_count == 0
    assert report.overlap_percentage == 0.0
    assert report.product_overlaps == []
    assert len(report.vendor_summary) == 1
    vendor_entry = report.vendor_summary[0]
    assert vendor_entry.total_capabilities_provided == vendor_entry.unique_capabilities_provided
    assert vendor_entry.overlapping_capabilities_provided == 0


def test_cross_vendor_duplicate_capability_detected(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-002")

    vendor_a, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    vendor_b, product_b, edition_b = _make_hierarchy(client, "B")
    module_b = _make_module(client, edition_b, [capability["id"]], "B")

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor_a, product_a, edition_a, module_a)
    _deploy(client, project, environment, vendor_b, product_b, edition_b, module_b)

    report = OverlapEngine(session).calculate(project["id"])

    assert report.duplicate_capability_count == 1
    assert report.cross_vendor_duplicate_count == 1
    dup = report.duplicate_capabilities[0]
    assert dup.code == "EDR-002"
    assert dup.distinct_vendor_count == 2
    assert dup.cross_vendor is True

    assert len(report.product_overlaps) == 1
    pair = report.product_overlaps[0]
    assert pair.shared_capability_count == 1
    assert {pair.vendor_a, pair.vendor_b} == {"VendorA", "VendorB"}


def test_same_vendor_duplicate_is_not_cross_vendor(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-003")

    vendor, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    # Second product from the SAME vendor.
    product_b = client.post(
        "/products", json={"name": "ProductB", "vendor_id": vendor["id"]}
    ).json()
    edition_b = client.post(
        "/editions", json={"name": "EditionB", "product_id": product_b["id"]}
    ).json()
    module_b = _make_module(client, edition_b, [capability["id"]], "B")

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product_a, edition_a, module_a)
    _deploy(client, project, environment, vendor, product_b, edition_b, module_b)

    report = OverlapEngine(session).calculate(project["id"])

    assert report.duplicate_capability_count == 1
    assert report.cross_vendor_duplicate_count == 0
    assert report.duplicate_capabilities[0].cross_vendor is False


def test_module_overlap_detected(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-004")

    vendor_a, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    vendor_b, product_b, edition_b = _make_hierarchy(client, "B")
    module_b = _make_module(client, edition_b, [capability["id"]], "B")

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor_a, product_a, edition_a, module_a)
    _deploy(client, project, environment, vendor_b, product_b, edition_b, module_b)

    report = OverlapEngine(session).calculate(project["id"])

    assert len(report.module_overlaps) == 1
    pair = report.module_overlaps[0]
    assert pair.shared_capability_count == 1
    assert "EDR-004" in pair.shared_capability_codes


def test_framework_overlap_from_duplicate_capability(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-005")
    framework = _make_framework(client, "NIST CSF")
    _map_control(client, capability, framework, "PR.DS-1")

    vendor_a, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    vendor_b, product_b, edition_b = _make_hierarchy(client, "B")
    module_b = _make_module(client, edition_b, [capability["id"]], "B")

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor_a, product_a, edition_a, module_a)
    _deploy(client, project, environment, vendor_b, product_b, edition_b, module_b)

    report = OverlapEngine(session).calculate(project["id"])

    assert len(report.framework_overlaps) == 1
    fw = report.framework_overlaps[0]
    assert fw.control_id == "PR.DS-1"
    assert fw.provider_count == 2


def test_redundant_license_fully_redundant(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-006")

    vendor_a, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    vendor_b, product_b, edition_b = _make_hierarchy(client, "B")
    module_b = _make_module(client, edition_b, [capability["id"]], "B")

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor_a, product_a, edition_a, module_a, license_quantity=100)
    _deploy(client, project, environment, vendor_b, product_b, edition_b, module_b, license_quantity=50)

    report = OverlapEngine(session).calculate(project["id"])

    assert len(report.redundant_licenses) == 2
    assert all(r.fully_redundant for r in report.redundant_licenses)
    assert report.license_reduction_opportunity == 150


def test_unused_capabilities_detected(client, session):
    domain = _make_domain(client, "Endpoint Security")
    enabled_capability = _make_capability(client, domain, "EDR-007")
    unused_capability = _make_capability(client, domain, "EDR-008")

    vendor, product, edition = _make_hierarchy(client, "A")
    enabled_module = _make_module(client, edition, [enabled_capability["id"]], "Enabled")
    # A second module on the SAME edition — comes with the license, but is
    # never enabled in the assignment below.
    unused_module = client.post(
        "/modules",
        json={
            "name": "Unused",
            "edition_id": edition["id"],
            "capability_ids": [unused_capability["id"]],
        },
    ).json()
    _ = unused_module

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product, edition, enabled_module)

    report = OverlapEngine(session).calculate(project["id"])

    assert report.unused_capability_count == 1
    unused = report.unused_capabilities[0]
    assert unused.capability_code == "EDR-008"
    assert unused.module == "Unused"


def test_vendor_summary_cross_references_recommendation_report(client, session):
    domain = _make_domain(client, "Endpoint Security")
    deployed_capability = _make_capability(client, domain, "EDR-009")
    open_gap_capability = _make_capability(client, domain, "EDR-010")

    vendor, product, edition = _make_hierarchy(client, "A")
    deployed_module = _make_module(client, edition, [deployed_capability["id"]], "Deployed")
    # Same vendor also offers a module for a capability that's NOT deployed
    # anywhere in this assessment -- an open gap this vendor could close.
    catalog_module = _make_module(client, edition, [open_gap_capability["id"]], "Catalog")
    _map_product_to_capability(
        client, vendor, product, edition, catalog_module, open_gap_capability
    )

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product, edition, deployed_module)

    report = OverlapEngine(session).calculate(project["id"])

    vendor_entry = next(v for v in report.vendor_summary if v.vendor == "VendorA")
    assert vendor_entry.open_gaps_addressable == 1


def test_optimization_scores_are_bounded(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-011")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product, edition, module)

    report = OverlapEngine(session).calculate(project["id"])

    for score in (
        report.optimization_score,
        report.vendor_consolidation_score,
        report.cost_optimization_score,
        report.operational_complexity_score,
        report.overlap_percentage,
    ):
        assert 0.0 <= score <= 100.0


def test_overlap_engine_raises_for_unknown_assessment_project(session):
    with pytest.raises(EntityNotFoundError):
        OverlapEngine(session).calculate(999999)

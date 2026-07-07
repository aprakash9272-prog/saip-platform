import pytest

from app.core.exceptions import EntityNotFoundError
from app.engine.gap_engine import GapEngine


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


def _deploy(client, project, environment, vendor, product, edition, module):
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
            "deployment_status": "Deployed",
        },
    ).json()


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


def test_gap_with_no_signals_is_informational_and_open(client, session):
    domain = _make_domain(client, "Endpoint Security")
    _make_capability(client, domain, "EDR-001")
    _, _, project = _make_customer_project(client)

    report = GapEngine(session).calculate(project["id"])

    assert report.total_gaps == 1
    gap = report.gaps[0]
    assert gap.code == "EDR-001"
    assert gap.severity == "Informational"
    assert gap.business_impact == "Low"
    assert gap.status == "Open"
    assert gap.framework_controls == []
    assert gap.mapped_products == []


def test_gap_severity_from_risk_category_alone(client, session):
    domain = _make_domain(client, "Endpoint Security")
    _make_capability(client, domain, "EDR-002", risk_category="Critical")
    _make_capability(client, domain, "EDR-003", risk_category="High")
    _make_capability(client, domain, "EDR-004", risk_category="Medium")
    _make_capability(client, domain, "EDR-005", risk_category="Low")
    _, _, project = _make_customer_project(client)

    report = GapEngine(session).calculate(project["id"])

    severities = {g.code: g.severity for g in report.gaps}
    assert severities["EDR-002"] == "High"
    assert severities["EDR-003"] == "High"
    assert severities["EDR-004"] == "Medium"
    assert severities["EDR-005"] == "Low"


def test_gap_escalates_to_critical_with_framework_mappings(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-006", risk_category="High")
    nist = _make_framework(client, "NIST CSF")
    iso = _make_framework(client, "ISO 27001")
    _map_control(client, capability, nist, "PR.DS-1")
    _map_control(client, capability, nist, "PR.DS-2")
    _map_control(client, capability, iso, "A.8.1")
    _, _, project = _make_customer_project(client)

    report = GapEngine(session).calculate(project["id"])

    gap = report.gaps[0]
    assert gap.severity == "Critical"
    assert len(gap.framework_controls) == 3
    control_ids = {c.control_id for c in gap.framework_controls}
    assert control_ids == {"PR.DS-1", "PR.DS-2", "A.8.1"}


def test_gap_escalates_with_business_critical_flag(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-007", risk_category="Low")
    client.put(f"/capabilities/{capability['id']}", json={"is_business_critical": True})
    _, _, project = _make_customer_project(client)

    report = GapEngine(session).calculate(project["id"])

    gap = report.gaps[0]
    assert gap.severity == "Medium"
    # Business impact is driven primarily by business-criticality, so even a
    # Low risk_category capability reads as a High business impact once
    # flagged business-critical.
    assert gap.business_impact == "High"


def test_gap_lists_mapped_products_from_catalog(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-008")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    client.post(
        "/product-mappings",
        json={
            "vendor_id": vendor["id"],
            "product_id": product["id"],
            "edition_id": edition["id"],
            "module_id": module["id"],
            "capability_id": capability["id"],
            "deployment_model": "Agent",
        },
    )
    # Nothing is actually deployed in this assessment, so EDR-008 stays a gap
    # even though the catalog knows a product that could provide it.
    _, _, project = _make_customer_project(client)

    report = GapEngine(session).calculate(project["id"])

    gap = report.gaps[0]
    assert gap.mapped_products == ["VendorA - ProductA (EditionA)"]


def test_domain_gap_score_reflects_missing_and_critical_counts(client, session):
    domain = _make_domain(client, "Endpoint Security")
    cap_missing = _make_capability(client, domain, "EDR-009", risk_category="Critical")
    nist = _make_framework(client, "NIST CSF")
    iso = _make_framework(client, "ISO 27001")
    _map_control(client, cap_missing, nist, "PR.DS-1")
    _map_control(client, cap_missing, nist, "PR.DS-2")
    _map_control(client, cap_missing, iso, "A.8.1")

    cap_covered = client.post(
        "/capabilities", json={"name": "Covered", "code": "EDR-010", "domain_id": domain["id"]}
    ).json()

    vendor, product, edition = _make_hierarchy(client, "B")
    module = _make_module(client, edition, [cap_covered["id"]], "B")
    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product, edition, module)

    report = GapEngine(session).calculate(project["id"])

    domain_score = next(d for d in report.domain_gap_scores if d.domain_name == "Endpoint Security")
    assert domain_score.missing_count == 1
    assert domain_score.critical_gap_count == 1
    assert domain_score.gap_percentage == 50.0
    assert domain_score.coverage_percentage == 50.0
    assert domain_score.domain_risk_score == round((50.0 + 100) / 2, 2)


def test_gap_report_totals_and_severity_counts(client, session):
    domain = _make_domain(client, "Endpoint Security")
    _make_capability(client, domain, "EDR-011", risk_category="Critical")
    _make_capability(client, domain, "EDR-012", risk_category="Low")
    _, _, project = _make_customer_project(client)

    report = GapEngine(session).calculate(project["id"])

    assert report.total_gaps == 2
    assert report.total_capabilities == 2
    assert report.overall_gap_percentage == 100.0
    assert report.critical_count + report.high_count + report.medium_count + \
        report.low_count + report.informational_count == report.total_gaps


def test_gap_engine_raises_for_unknown_assessment_project(session):
    with pytest.raises(EntityNotFoundError):
        GapEngine(session).calculate(999999)

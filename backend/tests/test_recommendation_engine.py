import pytest

from app.core.exceptions import EntityNotFoundError
from app.engine.recommendation_engine import RecommendationEngine


def _make_domain(client, domain_name):
    return client.post("/domains", json={"name": domain_name}).json()


def _make_capability(client, domain, code, risk_category=None, is_business_critical=False):
    payload = {
        "name": f"Cap {code}",
        "code": code,
        "domain_id": domain["id"],
        "is_business_critical": is_business_critical,
    }
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


def test_no_recommendation_when_no_catalog_candidate(client, session):
    domain = _make_domain(client, "Endpoint Security")
    _make_capability(client, domain, "EDR-001")
    _, _, project = _make_customer_project(client)

    report = RecommendationEngine(session).calculate(project["id"])

    assert report.total_gaps == 1
    assert report.addressable_gaps == 0
    assert report.unaddressable_gaps == 1
    assert report.recommendations == []


def test_recommendation_created_when_catalog_candidate_exists(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-002")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _map_product_to_capability(client, vendor, product, edition, module, capability)
    _, _, project = _make_customer_project(client)

    report = RecommendationEngine(session).calculate(project["id"])

    assert report.addressable_gaps == 1
    assert len(report.recommendations) == 1
    rec = report.recommendations[0]
    assert rec.capability_code == "EDR-002"
    best = rec.candidates[0]
    assert best.vendor == "VendorA"
    assert best.confidence_score == 80.0  # Generally Available, not already deployed
    assert best.implementation_complexity == "Low"  # SaaS
    assert best.estimated_effort == "1-2 weeks"
    assert best.already_deployed_vendor is False


def test_confidence_and_complexity_improve_for_already_deployed_vendor(client, session):
    domain = _make_domain(client, "Endpoint Security")
    covered_capability = _make_capability(client, domain, "EDR-003")
    gap_capability = _make_capability(client, domain, "EDR-004")

    vendor, product, edition = _make_hierarchy(client, "A")
    covering_module = _make_module(client, edition, [covered_capability["id"]], "A1")
    gap_module = _make_module(client, edition, [gap_capability["id"]], "A2")
    _map_product_to_capability(
        client, vendor, product, edition, gap_module, gap_capability, deployment_model="Agent"
    )

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, vendor, product, edition, covering_module)

    report = RecommendationEngine(session).calculate(project["id"])

    rec = next(r for r in report.recommendations if r.capability_code == "EDR-004")
    best = rec.candidates[0]
    assert best.already_deployed_vendor is True
    assert best.confidence_score == 95.0  # 80 + 15 bonus
    assert best.implementation_complexity == "Low"  # Agent downgraded to Low


def test_multiple_candidates_sorted_by_confidence(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-005")

    vendor_a, product_a, edition_a = _make_hierarchy(client, "A")
    module_a = _make_module(client, edition_a, [capability["id"]], "A")
    _map_product_to_capability(
        client, vendor_a, product_a, edition_a, module_a, capability,
        availability_status="Beta",
    )

    vendor_b, product_b, edition_b = _make_hierarchy(client, "B")
    module_b = _make_module(client, edition_b, [capability["id"]], "B")
    _map_product_to_capability(
        client, vendor_b, product_b, edition_b, module_b, capability,
        availability_status="Generally Available",
    )

    _, _, project = _make_customer_project(client)

    report = RecommendationEngine(session).calculate(project["id"])

    rec = report.recommendations[0]
    assert len(rec.candidates) == 2
    assert rec.candidates[0].vendor == "VendorB"  # GA beats Beta
    assert rec.candidates[0].confidence_score > rec.candidates[1].confidence_score


def test_product_comparison_aggregates_across_gaps(client, session):
    domain = _make_domain(client, "Endpoint Security")
    cap1 = _make_capability(client, domain, "EDR-006")
    cap2 = _make_capability(client, domain, "EDR-007")

    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [cap1["id"], cap2["id"]], "A")
    _map_product_to_capability(client, vendor, product, edition, module, cap1)
    _map_product_to_capability(client, vendor, product, edition, module, cap2)

    _, _, project = _make_customer_project(client)

    report = RecommendationEngine(session).calculate(project["id"])

    entry = next(
        e for e in report.product_comparison if e.vendor == "VendorA" and e.product == "ProductA"
    )
    assert entry.gaps_addressed == 2


def test_priority_matrix_counts_match_recommendations(client, session):
    domain = _make_domain(client, "Endpoint Security")
    critical_cap = _make_capability(
        client, domain, "EDR-008", risk_category="Critical", is_business_critical=True
    )
    low_cap = _make_capability(client, domain, "EDR-009", risk_category="Low")
    # Filler capabilities, all covered by a deployed assignment below, so the
    # domain is large enough (~17 capabilities) that the "concentrated
    # domain" priority bonus doesn't fire for either gap — this isolates
    # what's under test (severity-driven priority) from that bonus.
    filler_caps = [
        _make_capability(client, domain, f"EDR-FILL-{i}") for i in range(15)
    ]

    nist = _make_framework(client, "NIST CSF")
    _map_control(client, critical_cap, nist, "PR.DS-1")
    _map_control(client, critical_cap, nist, "PR.DS-2")
    _map_control(client, critical_cap, nist, "PR.DS-3")

    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [critical_cap["id"], low_cap["id"]], "A")
    _map_product_to_capability(client, vendor, product, edition, module, critical_cap)
    _map_product_to_capability(client, vendor, product, edition, module, low_cap)

    filler_vendor, filler_product, filler_edition = _make_hierarchy(client, "Filler")
    filler_module = _make_module(
        client, filler_edition, [c["id"] for c in filler_caps], "Filler"
    )

    _, environment, project = _make_customer_project(client)
    _deploy(client, project, environment, filler_vendor, filler_product, filler_edition, filler_module)

    report = RecommendationEngine(session).calculate(project["id"])

    total_from_matrix = sum(entry.count for entry in report.priority_matrix)
    assert total_from_matrix == len(report.recommendations)

    critical_rec = next(r for r in report.recommendations if r.capability_code == "EDR-008")
    low_rec = next(r for r in report.recommendations if r.capability_code == "EDR-009")
    assert critical_rec.priority == "Critical"
    assert low_rec.priority == "Low"


def test_coverage_forecast_reflects_addressable_gaps(client, session):
    domain = _make_domain(client, "Endpoint Security")
    addressable_cap = _make_capability(client, domain, "EDR-010")
    unaddressable_cap = _make_capability(client, domain, "EDR-011")

    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [addressable_cap["id"]], "A")
    _map_product_to_capability(client, vendor, product, edition, module, addressable_cap)
    _ = unaddressable_cap

    _, _, project = _make_customer_project(client)

    report = RecommendationEngine(session).calculate(project["id"])

    forecast = report.coverage_forecast
    assert forecast.addressable_gap_count == 1
    assert forecast.unaddressable_gap_count == 1
    assert forecast.projected_coverage_percentage > forecast.current_coverage_percentage


def test_estimated_risk_reduction_is_non_negative(client, session):
    domain = _make_domain(client, "Endpoint Security")
    capability = _make_capability(client, domain, "EDR-012", risk_category="Critical")
    vendor, product, edition = _make_hierarchy(client, "A")
    module = _make_module(client, edition, [capability["id"]], "A")
    _map_product_to_capability(client, vendor, product, edition, module, capability)
    _, _, project = _make_customer_project(client)

    report = RecommendationEngine(session).calculate(project["id"])

    assert report.estimated_overall_risk_reduction >= 0
    rec = report.recommendations[0]
    assert rec.estimated_risk_reduction >= 0


def test_recommendation_engine_raises_for_unknown_assessment_project(session):
    with pytest.raises(EntityNotFoundError):
        RecommendationEngine(session).calculate(999999)

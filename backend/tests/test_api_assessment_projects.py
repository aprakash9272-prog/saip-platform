def _customer(client, name="Acme Corp"):
    return client.post("/customers", json={"name": name}).json()


def _full_hierarchy(client, suffix="1"):
    """Vendor -> Product -> Edition -> Module -> Capability -> Domain/Framework."""
    vendor = client.post("/vendors", json={"name": f"Vendor{suffix}"}).json()
    product = client.post(
        "/products", json={"name": f"Product{suffix}", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": f"Edition{suffix}", "product_id": product["id"]}
    ).json()
    domain = client.post("/domains", json={"name": f"Domain{suffix}"}).json()
    capability = client.post(
        "/capabilities",
        json={"name": f"Capability{suffix}", "code": f"CAP-{suffix}", "domain_id": domain["id"]},
    ).json()
    module = client.post(
        "/modules",
        json={
            "name": f"Module{suffix}",
            "edition_id": edition["id"],
            "capability_ids": [capability["id"]],
        },
    ).json()
    framework = client.post(
        "/frameworks", json={"name": f"Framework{suffix}", "version": "1.0"}
    ).json()
    client.post(
        "/mappings",
        json={
            "capability_id": capability["id"],
            "framework_id": framework["id"],
            "control_id": f"TC-{suffix}",
            "control_name": "Test control",
        },
    )
    return vendor, product, edition, module, capability, domain, framework


def test_assessment_project_crud_lifecycle(client):
    customer = _customer(client)

    create_resp = client.post(
        "/assessment-projects",
        json={"name": "2026 Security Review", "customer_id": customer["id"], "status": "In Progress"},
    )
    assert create_resp.status_code == 201
    project = create_resp.json()
    assert project["status"] == "In Progress"

    get_resp = client.get(f"/assessment-projects/{project['id']}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/assessment-projects/{project['id']}", json={"status": "Completed"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "Completed"

    delete_resp = client.delete(f"/assessment-projects/{project['id']}")
    assert delete_resp.status_code == 204
    assert client.get(f"/assessment-projects/{project['id']}").status_code == 404


def test_assessment_project_rejects_invalid_status(client):
    customer = _customer(client)
    resp = client.post(
        "/assessment-projects",
        json={"name": "Bad Status", "customer_id": customer["id"], "status": "Bogus"},
    )
    assert resp.status_code == 422


def test_assessment_project_rejects_invalid_customer(client):
    resp = client.post(
        "/assessment-projects", json={"name": "Orphan", "customer_id": 999999}
    )
    assert resp.status_code == 422


def test_assessment_project_rejects_duplicate_name_within_customer(client):
    customer = _customer(client)
    client.post(
        "/assessment-projects", json={"name": "2026 Review", "customer_id": customer["id"]}
    )
    dup = client.post(
        "/assessment-projects", json={"name": "2026 Review", "customer_id": customer["id"]}
    )
    assert dup.status_code == 409


def test_assessment_project_filter_by_status(client):
    customer = _customer(client)
    client.post(
        "/assessment-projects",
        json={"name": "Draft One", "customer_id": customer["id"], "status": "Draft"},
    )
    client.post(
        "/assessment-projects",
        json={"name": "Active One", "customer_id": customer["id"], "status": "In Progress"},
    )

    resp = client.get("/assessment-projects", params={"status": "Draft"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Draft One"


def test_assessment_project_dashboard_aggregates_transitively(client):
    customer = _customer(client)
    vendor, product, edition, module, capability, domain, framework = _full_hierarchy(client)
    environment = client.post(
        "/environments",
        json={"name": "Production", "environment_type": "Production", "customer_id": customer["id"]},
    ).json()
    project = client.post(
        "/assessment-projects", json={"name": "2026 Review", "customer_id": customer["id"]}
    ).json()

    client.post(
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
    )

    resp = client.get(f"/assessment-projects/{project['id']}/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_deployed_products"] == 1
    assert body["distinct_product_count"] == 1
    assert body["vendor_count"] == 1
    assert body["vendors"][0]["name"] == vendor["name"]
    assert body["module_count"] == 1
    assert body["capability_count"] == 1
    assert body["capabilities"][0]["code"] == capability["code"]
    assert body["domain_count"] == 1
    assert body["domains"][0]["name"] == domain["name"]
    assert body["framework_count"] == 1
    assert body["frameworks"][0]["name"] == framework["name"]


def test_assessment_project_export_import_round_trip_is_idempotent(client):
    customer = _customer(client)
    vendor, product, edition, module, capability, domain, framework = _full_hierarchy(client)
    environment = client.post(
        "/environments",
        json={"name": "Production", "environment_type": "Production", "customer_id": customer["id"]},
    ).json()
    project = client.post(
        "/assessment-projects", json={"name": "2026 Review", "customer_id": customer["id"]}
    ).json()
    client.post(
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
    )

    export_resp = client.get(f"/assessment-projects/{project['id']}/export")
    assert export_resp.status_code == 200
    export_payload = export_resp.json()
    assert export_payload["customer"] == customer["name"]
    assert export_payload["assignments"][0]["vendor"] == vendor["name"]
    assert export_payload["assignments"][0]["modules"] == [module["name"]]

    first_import = client.post("/assessment-projects/import", json=export_payload)
    assert first_import.status_code == 200
    assert first_import.json() == {
        "project_id": project["id"],
        "project_status": "unchanged",
        "assignments_created": 0,
        "assignments_updated": 0,
        "assignments_unchanged": 1,
    }


def test_assessment_project_import_creates_new_project_and_assignment(client):
    customer = _customer(client)
    vendor, product, edition, module, capability, domain, framework = _full_hierarchy(client)
    environment = client.post(
        "/environments",
        json={"name": "Production", "environment_type": "Production", "customer_id": customer["id"]},
    ).json()

    payload = {
        "customer": customer["name"],
        "name": "Imported Assessment",
        "status": "Draft",
        "assignments": [
            {
                "vendor": vendor["name"],
                "product": product["name"],
                "edition": edition["name"],
                "modules": [module["name"]],
                "environment": environment["name"],
                "deployment_model": "SaaS",
                "deployment_status": "In Progress",
            }
        ],
    }

    resp = client.post("/assessment-projects/import", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_status"] == "created"
    assert body["assignments_created"] == 1

    projects = client.get(
        "/assessment-projects", params={"customer_id": customer["id"]}
    ).json()
    assert any(p["name"] == "Imported Assessment" for p in projects["items"])


def test_assessment_project_import_rejects_unknown_customer(client):
    resp = client.post(
        "/assessment-projects/import",
        json={"customer": "Does Not Exist", "name": "X", "status": "Draft", "assignments": []},
    )
    assert resp.status_code == 422


def test_assessment_project_import_rejects_unknown_vendor_reference(client):
    customer = _customer(client)
    resp = client.post(
        "/assessment-projects/import",
        json={
            "customer": customer["name"],
            "name": "X",
            "status": "Draft",
            "assignments": [
                {
                    "vendor": "Nonexistent Vendor",
                    "product": "Nonexistent Product",
                    "edition": "Nonexistent Edition",
                    "modules": [],
                    "environment": "Nonexistent Env",
                    "deployment_model": "Agent",
                    "deployment_status": "Not Started",
                }
            ],
        },
    )
    assert resp.status_code == 422

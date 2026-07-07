def _catalog_hierarchy(client, suffix="1"):
    vendor = client.post("/vendors", json={"name": f"Vendor{suffix}"}).json()
    product = client.post(
        "/products", json={"name": f"Product{suffix}", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": f"Edition{suffix}", "product_id": product["id"]}
    ).json()
    module = client.post(
        "/modules", json={"name": f"Module{suffix}", "edition_id": edition["id"]}
    ).json()
    return vendor, product, edition, module


def _customer_with_environment(client, suffix="1"):
    customer = client.post("/customers", json={"name": f"Customer{suffix}"}).json()
    environment = client.post(
        "/environments",
        json={
            "name": f"Production{suffix}",
            "environment_type": "Production",
            "customer_id": customer["id"],
        },
    ).json()
    return customer, environment


def _project(client, customer, suffix="1"):
    return client.post(
        "/assessment-projects",
        json={"name": f"Assessment{suffix}", "customer_id": customer["id"]},
    ).json()


def _assignment_payload(project, vendor, product, edition, environment, module=None, **overrides):
    payload = {
        "assessment_project_id": project["id"],
        "vendor_id": vendor["id"],
        "product_id": product["id"],
        "edition_id": edition["id"],
        "environment_id": environment["id"],
        "module_ids": [module["id"]] if module else [],
        "license_quantity": 100,
        "deployment_model": "Agent",
        "deployment_status": "Deployed",
        "notes": "Rolled out.",
    }
    payload.update(overrides)
    return payload


def test_product_assignment_crud_lifecycle(client):
    vendor, product, edition, module = _catalog_hierarchy(client)
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)
    payload = _assignment_payload(project, vendor, product, edition, environment, module)

    create_resp = client.post("/product-assignments", json=payload)
    assert create_resp.status_code == 201
    assignment = create_resp.json()
    assert assignment["module_ids"] == [module["id"]]
    assert assignment["deployment_status"] == "Deployed"

    get_resp = client.get(f"/product-assignments/{assignment['id']}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/product-assignments/{assignment['id']}",
        json={"deployment_status": "Decommissioned"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["deployment_status"] == "Decommissioned"

    delete_resp = client.delete(f"/product-assignments/{assignment['id']}")
    assert delete_resp.status_code == 204
    assert client.get(f"/product-assignments/{assignment['id']}").status_code == 404


def test_product_assignment_rejects_duplicate(client):
    vendor, product, edition, module = _catalog_hierarchy(client)
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)
    payload = _assignment_payload(project, vendor, product, edition, environment, module)

    first = client.post("/product-assignments", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/product-assignments", json=payload)
    assert duplicate.status_code == 409


def test_product_assignment_rejects_product_not_belonging_to_vendor(client):
    vendor_a, product_a, edition_a, module_a = _catalog_hierarchy(client, "A")
    vendor_b, product_b, edition_b, module_b = _catalog_hierarchy(client, "B")
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)

    payload = _assignment_payload(project, vendor_a, product_b, edition_a, environment)
    resp = client.post("/product-assignments", json=payload)
    assert resp.status_code == 422


def test_product_assignment_rejects_edition_not_belonging_to_product(client):
    vendor_a, product_a, edition_a, module_a = _catalog_hierarchy(client, "A")
    vendor_b, product_b, edition_b, module_b = _catalog_hierarchy(client, "B")
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)

    payload = _assignment_payload(project, vendor_a, product_a, edition_b, environment)
    resp = client.post("/product-assignments", json=payload)
    assert resp.status_code == 422


def test_product_assignment_rejects_module_not_belonging_to_edition(client):
    vendor_a, product_a, edition_a, module_a = _catalog_hierarchy(client, "A")
    vendor_b, product_b, edition_b, module_b = _catalog_hierarchy(client, "B")
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)

    payload = _assignment_payload(
        project, vendor_a, product_a, edition_a, environment, module=module_b
    )
    resp = client.post("/product-assignments", json=payload)
    assert resp.status_code == 422


def test_product_assignment_rejects_environment_from_different_customer(client):
    vendor, product, edition, module = _catalog_hierarchy(client)
    customer_a, environment_a = _customer_with_environment(client, "A")
    customer_b, environment_b = _customer_with_environment(client, "B")
    project = _project(client, customer_a)

    payload = _assignment_payload(project, vendor, product, edition, environment_b)
    resp = client.post("/product-assignments", json=payload)
    assert resp.status_code == 422


def test_product_assignment_rejects_invalid_deployment_model(client):
    vendor, product, edition, module = _catalog_hierarchy(client)
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)

    payload = _assignment_payload(
        project, vendor, product, edition, environment, deployment_model="Carrier Pigeon"
    )
    resp = client.post("/product-assignments", json=payload)
    assert resp.status_code == 422


def test_product_assignment_rejects_invalid_deployment_status(client):
    vendor, product, edition, module = _catalog_hierarchy(client)
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)

    payload = _assignment_payload(
        project, vendor, product, edition, environment, deployment_status="On Fire"
    )
    resp = client.post("/product-assignments", json=payload)
    assert resp.status_code == 422


def test_product_assignment_update_module_ids(client):
    vendor, product, edition, module_a = _catalog_hierarchy(client, "A")
    module_b = client.post(
        "/modules", json={"name": "ModuleB2", "edition_id": edition["id"]}
    ).json()
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)

    payload = _assignment_payload(project, vendor, product, edition, environment, module_a)
    assignment = client.post("/product-assignments", json=payload).json()
    assert assignment["module_ids"] == [module_a["id"]]

    update_resp = client.put(
        f"/product-assignments/{assignment['id']}",
        json={"module_ids": [module_b["id"]]},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["module_ids"] == [module_b["id"]]


def test_product_assignment_filters(client):
    vendor, product, edition, module = _catalog_hierarchy(client)
    customer, environment = _customer_with_environment(client)
    project = _project(client, customer)
    client.post(
        "/product-assignments",
        json=_assignment_payload(project, vendor, product, edition, environment, module),
    )

    resp = client.get(
        "/product-assignments", params={"assessment_project_id": project["id"]}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp_vendor = client.get("/product-assignments", params={"vendor_id": vendor["id"]})
    assert resp_vendor.status_code == 200
    assert resp_vendor.json()["total"] == 1

def test_full_hierarchy_via_api(client):
    vendor = client.post("/vendors", json={"name": "Acme"}).json()
    product = client.post(
        "/products", json={"name": "Shield", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": "Pro", "product_id": product["id"]}
    ).json()
    domain = client.post("/domains", json={"name": "Endpoint Security"}).json()
    capability = client.post(
        "/capabilities",
        json={"name": "Detection", "code": "EDR-999", "domain_id": domain["id"]},
    ).json()

    module_resp = client.post(
        "/modules",
        json={
            "name": "Detector",
            "edition_id": edition["id"],
            "capability_ids": [capability["id"]],
        },
    )
    assert module_resp.status_code == 201
    module = module_resp.json()
    assert module["capability_ids"] == [capability["id"]]

    framework = client.post(
        "/frameworks", json={"name": "TestFW", "version": "1.0"}
    ).json()
    mapping_resp = client.post(
        "/mappings",
        json={
            "capability_id": capability["id"],
            "framework_id": framework["id"],
            "control_id": "TC-1",
            "control_name": "Test control",
        },
    )
    assert mapping_resp.status_code == 201
    assert mapping_resp.json()["capability_id"] == capability["id"]


def test_product_rejects_invalid_vendor_reference(client):
    resp = client.post("/products", json={"name": "Orphan", "vendor_id": 999999})
    assert resp.status_code == 422


def test_capability_rejects_invalid_domain_reference(client):
    resp = client.post(
        "/capabilities",
        json={"name": "Detection", "code": "EDR-998", "domain_id": 999999},
    )
    assert resp.status_code == 422


def test_module_rejects_invalid_capability_reference(client):
    vendor = client.post("/vendors", json={"name": "Acme"}).json()
    product = client.post(
        "/products", json={"name": "Shield", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": "Pro", "product_id": product["id"]}
    ).json()

    resp = client.post(
        "/modules",
        json={"name": "Detector", "edition_id": edition["id"], "capability_ids": [999999]},
    )
    assert resp.status_code == 422


def test_module_capability_links_can_be_updated(client):
    vendor = client.post("/vendors", json={"name": "Acme"}).json()
    product = client.post(
        "/products", json={"name": "Shield", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": "Pro", "product_id": product["id"]}
    ).json()
    domain = client.post("/domains", json={"name": "Endpoint Security"}).json()
    cap_a = client.post(
        "/capabilities", json={"name": "A", "code": "A-1", "domain_id": domain["id"]}
    ).json()
    cap_b = client.post(
        "/capabilities", json={"name": "B", "code": "B-1", "domain_id": domain["id"]}
    ).json()

    module = client.post(
        "/modules",
        json={
            "name": "Detector",
            "edition_id": edition["id"],
            "capability_ids": [cap_a["id"]],
        },
    ).json()

    update_resp = client.put(
        f"/modules/{module['id']}", json={"capability_ids": [cap_b["id"]]}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["capability_ids"] == [cap_b["id"]]

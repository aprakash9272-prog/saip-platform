import yaml


def _build_hierarchy(client, suffix="1"):
    vendor = client.post("/vendors", json={"name": f"Acme{suffix}"}).json()
    product = client.post(
        "/products", json={"name": f"Shield{suffix}", "vendor_id": vendor["id"]}
    ).json()
    edition = client.post(
        "/editions", json={"name": f"Pro{suffix}", "product_id": product["id"]}
    ).json()
    module = client.post(
        "/modules", json={"name": f"Detector{suffix}", "edition_id": edition["id"]}
    ).json()
    domain = client.post("/domains", json={"name": f"Domain{suffix}"}).json()
    capability = client.post(
        "/capabilities",
        json={"name": f"Cap{suffix}", "code": f"CAP-{suffix}", "domain_id": domain["id"]},
    ).json()
    return vendor, product, edition, module, capability


def _mapping_payload(vendor, product, edition, module, capability, **overrides):
    payload = {
        "vendor_id": vendor["id"],
        "product_id": product["id"],
        "edition_id": edition["id"],
        "module_id": module["id"],
        "capability_id": capability["id"],
        "licensing_tier": "Enterprise",
        "supported_platforms": ["Windows", "Cloud"],
        "deployment_model": "Agent",
        "availability_status": "Generally Available",
    }
    payload.update(overrides)
    return payload


def test_product_mapping_crud_lifecycle(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    payload = _mapping_payload(vendor, product, edition, module, capability)

    create_resp = client.post("/product-mappings", json=payload)
    assert create_resp.status_code == 201
    mapping = create_resp.json()
    assert mapping["deployment_model"] == "Agent"
    assert mapping["supported_platforms"] == ["Windows", "Cloud"]

    get_resp = client.get(f"/product-mappings/{mapping['id']}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/product-mappings/{mapping['id']}", json={"availability_status": "Beta"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["availability_status"] == "Beta"

    delete_resp = client.delete(f"/product-mappings/{mapping['id']}")
    assert delete_resp.status_code == 204

    after_delete = client.get(f"/product-mappings/{mapping['id']}")
    assert after_delete.status_code == 404


def test_product_mapping_rejects_duplicate(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    payload = _mapping_payload(vendor, product, edition, module, capability)

    first = client.post("/product-mappings", json=payload)
    assert first.status_code == 201

    duplicate = client.post("/product-mappings", json=payload)
    assert duplicate.status_code == 409


def test_product_mapping_allows_same_module_capability_different_tier(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    base = _mapping_payload(vendor, product, edition, module, capability)

    first = client.post("/product-mappings", json=base)
    assert first.status_code == 201

    different_tier = client.post(
        "/product-mappings", json={**base, "licensing_tier": "Standard"}
    )
    assert different_tier.status_code == 201


def test_product_mapping_rejects_inconsistent_hierarchy(client):
    vendor_a, product_a, edition_a, module_a, capability_a = _build_hierarchy(client, "A")
    vendor_b, product_b, edition_b, module_b, capability_b = _build_hierarchy(client, "B")

    # product_b does not belong to vendor_a
    payload = _mapping_payload(vendor_a, product_b, edition_a, module_a, capability_a)
    resp = client.post("/product-mappings", json=payload)
    assert resp.status_code == 422


def test_product_mapping_rejects_invalid_deployment_model(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    payload = _mapping_payload(
        vendor, product, edition, module, capability, deployment_model="Carrier Pigeon"
    )
    resp = client.post("/product-mappings", json=payload)
    assert resp.status_code == 422


def test_product_mapping_rejects_invalid_platform(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    payload = _mapping_payload(
        vendor, product, edition, module, capability, supported_platforms=["Amiga"]
    )
    resp = client.post("/product-mappings", json=payload)
    assert resp.status_code == 422


def test_product_mapping_filters(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    client.post(
        "/product-mappings",
        json=_mapping_payload(
            vendor, product, edition, module, capability, deployment_model="Agent"
        ),
    )
    client.post(
        "/product-mappings",
        json=_mapping_payload(
            vendor,
            product,
            edition,
            module,
            capability,
            licensing_tier="Standard",
            deployment_model="SaaS",
        ),
    )

    by_deployment = client.get("/product-mappings", params={"deployment_model": "SaaS"})
    assert by_deployment.status_code == 200
    assert by_deployment.json()["total"] == 1

    by_vendor = client.get("/product-mappings", params={"vendor_id": vendor["id"]})
    assert by_vendor.status_code == 200
    assert by_vendor.json()["total"] == 2


def test_product_mapping_facets(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    client.post(
        "/product-mappings",
        json=_mapping_payload(vendor, product, edition, module, capability),
    )

    resp = client.get("/product-mappings/facets")
    assert resp.status_code == 200
    body = resp.json()
    assert "Agent" in body["deployment_models"]
    assert "Generally Available" in body["availability_statuses"]
    assert "Enterprise" in body["licensing_tiers"]


def test_product_mapping_export_yaml(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    client.post(
        "/product-mappings",
        json=_mapping_payload(vendor, product, edition, module, capability),
    )

    resp = client.get("/product-mappings/export")
    assert resp.status_code == 200
    records = yaml.safe_load(resp.text)
    assert any(r["capability_code"] == capability["code"] for r in records)


def test_product_mapping_import_creates_and_is_idempotent(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    payload = yaml.safe_dump(
        [
            {
                "vendor": vendor["name"],
                "product": product["name"],
                "edition": edition["name"],
                "module": module["name"],
                "capability_code": capability["code"],
                "licensing_tier": "Enterprise",
                "supported_platforms": ["Cloud"],
                "deployment_model": "SaaS",
                "availability_status": "Generally Available",
            }
        ]
    ).encode()

    first = client.post(
        "/product-mappings/import",
        files={"file": ("mappings.yaml", payload, "application/x-yaml")},
    )
    assert first.status_code == 200
    assert first.json() == {"created": 1, "updated": 0, "unchanged": 0}

    second = client.post(
        "/product-mappings/import",
        files={"file": ("mappings.yaml", payload, "application/x-yaml")},
    )
    assert second.status_code == 200
    assert second.json() == {"created": 0, "updated": 0, "unchanged": 1}


def test_product_mapping_import_rejects_unknown_module(client):
    payload = yaml.safe_dump(
        [
            {
                "vendor": "DoesNotExist",
                "product": "Nope",
                "edition": "Nope",
                "module": "Nope",
                "capability_code": "NOPE-1",
                "deployment_model": "Agent",
            }
        ]
    ).encode()

    resp = client.post(
        "/product-mappings/import",
        files={"file": ("mappings.yaml", payload, "application/x-yaml")},
    )
    assert resp.status_code == 422


def test_product_mapping_bulk_update(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    m1 = client.post(
        "/product-mappings",
        json=_mapping_payload(vendor, product, edition, module, capability),
    ).json()
    m2 = client.post(
        "/product-mappings",
        json=_mapping_payload(
            vendor, product, edition, module, capability, licensing_tier="Standard"
        ),
    ).json()

    resp = client.patch(
        "/product-mappings/bulk",
        json={"ids": [m1["id"], m2["id"]], "patch": {"availability_status": "Deprecated"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated"] == 2
    assert body["failed"] == []

    assert client.get(f"/product-mappings/{m1['id']}").json()["availability_status"] == "Deprecated"
    assert client.get(f"/product-mappings/{m2['id']}").json()["availability_status"] == "Deprecated"


def test_product_mapping_bulk_delete(client):
    vendor, product, edition, module, capability = _build_hierarchy(client)
    m1 = client.post(
        "/product-mappings",
        json=_mapping_payload(vendor, product, edition, module, capability),
    ).json()
    m2 = client.post(
        "/product-mappings",
        json=_mapping_payload(
            vendor, product, edition, module, capability, licensing_tier="Standard"
        ),
    ).json()

    resp = client.request(
        "DELETE", "/product-mappings/bulk", json={"ids": [m1["id"], m2["id"]]}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted"] == 2

    assert client.get(f"/product-mappings/{m1['id']}").status_code == 404
    assert client.get(f"/product-mappings/{m2['id']}").status_code == 404

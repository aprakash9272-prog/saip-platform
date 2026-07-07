def _customer(client, name="Acme Corp"):
    return client.post("/customers", json={"name": name}).json()


def test_business_unit_crud_lifecycle(client):
    customer = _customer(client)

    create_resp = client.post(
        "/business-units",
        json={"name": "Retail Banking", "customer_id": customer["id"]},
    )
    assert create_resp.status_code == 201
    unit = create_resp.json()

    get_resp = client.get(f"/business-units/{unit['id']}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/business-units/{unit['id']}", json={"description": "Consumer banking arm"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Consumer banking arm"

    delete_resp = client.delete(f"/business-units/{unit['id']}")
    assert delete_resp.status_code == 204
    assert client.get(f"/business-units/{unit['id']}").status_code == 404


def test_business_unit_rejects_invalid_customer(client):
    resp = client.post(
        "/business-units", json={"name": "Orphan Unit", "customer_id": 999999}
    )
    assert resp.status_code == 422


def test_business_unit_rejects_duplicate_name_within_customer(client):
    customer = _customer(client)
    client.post(
        "/business-units", json={"name": "Retail Banking", "customer_id": customer["id"]}
    )
    dup = client.post(
        "/business-units", json={"name": "Retail Banking", "customer_id": customer["id"]}
    )
    assert dup.status_code == 409


def test_business_unit_allows_same_name_different_customer(client):
    customer_a = _customer(client, "Acme Corp")
    customer_b = _customer(client, "Globex")

    first = client.post(
        "/business-units", json={"name": "Retail Banking", "customer_id": customer_a["id"]}
    )
    second = client.post(
        "/business-units", json={"name": "Retail Banking", "customer_id": customer_b["id"]}
    )
    assert first.status_code == 201
    assert second.status_code == 201


def test_business_unit_filter_by_customer(client):
    customer_a = _customer(client, "Acme Corp")
    customer_b = _customer(client, "Globex")
    client.post(
        "/business-units", json={"name": "Retail Banking", "customer_id": customer_a["id"]}
    )
    client.post(
        "/business-units", json={"name": "Logistics", "customer_id": customer_b["id"]}
    )

    resp = client.get("/business-units", params={"customer_id": customer_a["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Retail Banking"

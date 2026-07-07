def _customer(client, name="Acme Corp"):
    return client.post("/customers", json={"name": name}).json()


def test_environment_crud_lifecycle(client):
    customer = _customer(client)

    create_resp = client.post(
        "/environments",
        json={
            "name": "Production - US",
            "environment_type": "Production",
            "customer_id": customer["id"],
        },
    )
    assert create_resp.status_code == 201
    environment = create_resp.json()
    assert environment["environment_type"] == "Production"

    get_resp = client.get(f"/environments/{environment['id']}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/environments/{environment['id']}", json={"environment_type": "DR"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["environment_type"] == "DR"

    delete_resp = client.delete(f"/environments/{environment['id']}")
    assert delete_resp.status_code == 204
    assert client.get(f"/environments/{environment['id']}").status_code == 404


def test_environment_rejects_invalid_environment_type(client):
    customer = _customer(client)
    resp = client.post(
        "/environments",
        json={
            "name": "Weird Env",
            "environment_type": "Metaverse",
            "customer_id": customer["id"],
        },
    )
    assert resp.status_code == 422


def test_environment_rejects_invalid_customer(client):
    resp = client.post(
        "/environments",
        json={"name": "Orphan Env", "environment_type": "UAT", "customer_id": 999999},
    )
    assert resp.status_code == 422


def test_environment_rejects_duplicate_name_within_customer(client):
    customer = _customer(client)
    client.post(
        "/environments",
        json={"name": "Production", "environment_type": "Production", "customer_id": customer["id"]},
    )
    dup = client.post(
        "/environments",
        json={"name": "Production", "environment_type": "Production", "customer_id": customer["id"]},
    )
    assert dup.status_code == 409


def test_environment_filter_by_type_and_customer(client):
    customer = _customer(client)
    client.post(
        "/environments",
        json={"name": "Production", "environment_type": "Production", "customer_id": customer["id"]},
    )
    client.post(
        "/environments",
        json={"name": "UAT", "environment_type": "UAT", "customer_id": customer["id"]},
    )

    resp = client.get("/environments", params={"environment_type": "UAT"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "UAT"

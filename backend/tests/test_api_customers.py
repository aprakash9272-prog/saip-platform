def test_customer_crud_lifecycle(client):
    create_resp = client.post(
        "/customers",
        json={"name": "Acme Corp", "industry": "Financial Services"},
    )
    assert create_resp.status_code == 201
    customer = create_resp.json()
    assert customer["name"] == "Acme Corp"

    get_resp = client.get(f"/customers/{customer['id']}")
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/customers/{customer['id']}", json={"industry": "Healthcare"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["industry"] == "Healthcare"

    delete_resp = client.delete(f"/customers/{customer['id']}")
    assert delete_resp.status_code == 204

    after_delete = client.get(f"/customers/{customer['id']}")
    assert after_delete.status_code == 404


def test_customer_rejects_duplicate_name(client):
    client.post("/customers", json={"name": "Acme Corp"})
    dup = client.post("/customers", json={"name": "Acme Corp"})
    assert dup.status_code == 409


def test_customer_search_and_pagination(client):
    client.post("/customers", json={"name": "Acme Corp", "industry": "Financial Services"})
    client.post("/customers", json={"name": "Globex", "industry": "Manufacturing"})

    resp = client.get("/customers", params={"search": "Acme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Acme Corp"

    paged = client.get("/customers", params={"skip": 0, "limit": 1})
    assert paged.status_code == 200
    assert paged.json()["total"] == 2
    assert len(paged.json()["items"]) == 1


def test_customer_sorting(client):
    client.post("/customers", json={"name": "Zeta Inc"})
    client.post("/customers", json={"name": "Alpha Inc"})

    resp = client.get("/customers", params={"sort_by": "name"})
    assert resp.status_code == 200
    names = [item["name"] for item in resp.json()["items"]]
    assert names == ["Alpha Inc", "Zeta Inc"]

    resp_desc = client.get("/customers", params={"sort_by": "name", "sort_desc": True})
    names_desc = [item["name"] for item in resp_desc.json()["items"]]
    assert names_desc == ["Zeta Inc", "Alpha Inc"]

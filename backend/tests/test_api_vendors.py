def test_vendor_crud_lifecycle(client):
    create_resp = client.post(
        "/vendors",
        json={
            "name": "Acme",
            "website": "https://acme.example",
            "description": "A test vendor.",
            "headquarters": "Testville",
        },
    )
    assert create_resp.status_code == 201
    vendor = create_resp.json()
    assert vendor["name"] == "Acme"
    assert "id" in vendor and "created_at" in vendor

    duplicate_resp = client.post("/vendors", json={"name": "Acme"})
    assert duplicate_resp.status_code == 409

    list_resp = client.get("/vendors", params={"search": "Acme"})
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Acme"

    get_resp = client.get(f"/vendors/{vendor['id']}")
    assert get_resp.status_code == 200

    missing_resp = client.get("/vendors/999999")
    assert missing_resp.status_code == 404

    update_resp = client.put(
        f"/vendors/{vendor['id']}", json={"description": "Updated description."}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated description."
    assert update_resp.json()["name"] == "Acme"

    delete_resp = client.delete(f"/vendors/{vendor['id']}")
    assert delete_resp.status_code == 204

    after_delete_resp = client.get(f"/vendors/{vendor['id']}")
    assert after_delete_resp.status_code == 404


def test_vendor_list_is_paginated(client):
    for i in range(5):
        client.post("/vendors", json={"name": f"Vendor {i}"})

    resp = client.get("/vendors", params={"skip": 2, "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["skip"] == 2
    assert body["limit"] == 2

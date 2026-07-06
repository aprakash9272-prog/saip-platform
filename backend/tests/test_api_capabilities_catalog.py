import yaml


def _make_domain(client, name="Endpoint Security"):
    return client.post("/domains", json={"name": name}).json()


def test_capability_filter_by_domain_id(client):
    domain_a = _make_domain(client, "Endpoint Security")
    domain_b = _make_domain(client, "Network Security")
    client.post(
        "/capabilities",
        json={"name": "EDR", "code": "EDR-CAT-1", "domain_id": domain_a["id"]},
    )
    client.post(
        "/capabilities",
        json={"name": "Firewall", "code": "NET-CAT-1", "domain_id": domain_b["id"]},
    )

    resp = client.get("/capabilities", params={"domain_id": domain_a["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["code"] == "EDR-CAT-1"


def test_capability_filter_by_risk_category(client):
    domain = _make_domain(client)
    client.post(
        "/capabilities",
        json={
            "name": "EDR",
            "code": "EDR-CAT-2",
            "domain_id": domain["id"],
            "risk_category": "Critical",
        },
    )
    client.post(
        "/capabilities",
        json={
            "name": "Reporting",
            "code": "EDR-CAT-3",
            "domain_id": domain["id"],
            "risk_category": "Low",
        },
    )

    resp = client.get("/capabilities", params={"risk_category": "Critical"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["code"] == "EDR-CAT-2"


def test_capability_facets_endpoint(client):
    domain = _make_domain(client, "Cloud Security")
    client.post(
        "/capabilities",
        json={
            "name": "CSPM",
            "code": "CLD-CAT-1",
            "domain_id": domain["id"],
            "risk_category": "High",
        },
    )

    resp = client.get("/capabilities/facets")
    assert resp.status_code == 200
    body = resp.json()
    assert any(d["name"] == "Cloud Security" for d in body["domains"])
    assert "High" in body["risk_categories"]


def test_capability_export_round_trips_as_yaml(client):
    domain = _make_domain(client, "Data Security & Privacy")
    client.post(
        "/capabilities",
        json={
            "name": "DLP",
            "code": "DAT-CAT-1",
            "domain_id": domain["id"],
            "description": "Prevents data exfiltration.",
            "risk_category": "High",
        },
    )

    resp = client.get("/capabilities/export")
    assert resp.status_code == 200
    records = yaml.safe_load(resp.text)
    assert any(
        r["code"] == "DAT-CAT-1" and r["domain"] == "Data Security & Privacy"
        for r in records
    )


def test_capability_import_creates_and_is_idempotent(client):
    _make_domain(client, "API Security")
    payload = yaml.safe_dump(
        [
            {
                "name": "API Gateway Security",
                "code": "API-CAT-1",
                "domain": "API Security",
                "description": "Enforces security policy at the API gateway.",
                "risk_category": "High",
            }
        ]
    ).encode()

    first = client.post(
        "/capabilities/import",
        files={"file": ("capabilities.yaml", payload, "application/x-yaml")},
    )
    assert first.status_code == 200
    assert first.json() == {"created": 1, "updated": 0, "unchanged": 0}

    second = client.post(
        "/capabilities/import",
        files={"file": ("capabilities.yaml", payload, "application/x-yaml")},
    )
    assert second.status_code == 200
    assert second.json() == {"created": 0, "updated": 0, "unchanged": 1}


def test_capability_import_rejects_unknown_domain(client):
    payload = yaml.safe_dump(
        [{"name": "Orphan", "code": "ORPH-1", "domain": "DoesNotExist"}]
    ).encode()

    resp = client.post(
        "/capabilities/import",
        files={"file": ("capabilities.yaml", payload, "application/x-yaml")},
    )
    assert resp.status_code == 422


def test_capability_import_rejects_invalid_yaml(client):
    resp = client.post(
        "/capabilities/import",
        files={"file": ("bad.yaml", b": not: valid: yaml: [", "application/x-yaml")},
    )
    assert resp.status_code == 422

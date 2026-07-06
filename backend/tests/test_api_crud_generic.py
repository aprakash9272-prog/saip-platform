import pytest

RESOURCES = [
    "vendors",
    "products",
    "editions",
    "modules",
    "domains",
    "capabilities",
    "frameworks",
    "mappings",
]


@pytest.mark.parametrize("resource", RESOURCES)
def test_list_endpoint_returns_empty_paginated_response(client, resource):
    resp = client.get(f"/{resource}")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0, "skip": 0, "limit": 50}


@pytest.mark.parametrize("resource", RESOURCES)
def test_get_missing_item_returns_404(client, resource):
    resp = client.get(f"/{resource}/999999")
    assert resp.status_code == 404


@pytest.mark.parametrize("resource", RESOURCES)
def test_swagger_and_openapi_are_served(client, resource):
    # Sanity check that every resource is actually documented.
    schema = client.get("/openapi.json").json()
    assert f"/{resource}" in schema["paths"]

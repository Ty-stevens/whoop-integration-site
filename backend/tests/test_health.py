def test_root_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "EnduraSync"
    assert payload["status"] == "ok"
    assert payload["database"] is True


def test_api_health(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


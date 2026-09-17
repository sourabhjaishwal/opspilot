def test_services_endpoint_returns_success(client):
    response = client.get("/services")

    assert response.status_code == 200
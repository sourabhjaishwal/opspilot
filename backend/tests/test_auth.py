def test_register_rejects_duplicate_username(client):
    first = client.post(
        "/auth/register",
        json={"username": "ops-admin", "password": "secret123", "role": "admin"},
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/auth/register",
        json={"username": "ops-admin", "password": "anotherpass", "role": "user"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Username already exists. Please choose a different username."


def test_register_requires_password(client):
    response = client.post(
        "/auth/register",
        json={"username": "new-user", "password": "", "role": "user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Password is required."


def test_login_rejects_invalid_credentials(client):
    client.post(
        "/auth/register",
        json={"username": "service-user", "password": "secret123", "role": "user"},
    )

    response = client.post(
        "/auth/login",
        json={"username": "service-user", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/auth/login",
        json={"username": "missing-user", "password": "secret123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."


def test_non_admin_user_cannot_create_service(client):
    from app.main import app
    from app.models.user import User
    from app.routes.deps import get_current_user

    app.dependency_overrides[get_current_user] = lambda: User(
        id=99,
        username="basic-user",
        hashed_password="",
        role="user",
    )
    try:
        response = client.post(
            "/services",
            json={"name": "restricted-service", "description": "Should fail"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"

# backend/tests/integration/test_auth.py
import pytest
import uuid


@pytest.mark.integration
class TestRegister:
    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "email": f"new_{uuid.uuid4().hex[:8]}@test.com",
            "name": "New User",
            "password": "securepassword"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] is not None

    def test_register_duplicate_email(self, client):
        email = f"dup_{uuid.uuid4().hex[:8]}@test.com"
        payload = {"email": email, "name": "User", "password": "password123"}

        r1 = client.post("/api/auth/register", json=payload)
        assert r1.status_code == 201

        r2 = client.post("/api/auth/register", json=payload)
        assert r2.status_code == 409
        assert "already registered" in r2.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        response = client.post("/api/auth/register", json={
            "email": "not-valid",
            "name": "User",
            "password": "password123"
        })
        assert response.status_code == 422

    def test_register_short_password(self, client):
        response = client.post("/api/auth/register", json={
            "email": "valid@test.com",
            "name": "User",
            "password": "short"
        })
        assert response.status_code == 422

    def test_register_password_not_returned(self, client):
        response = client.post("/api/auth/register", json={
            "email": f"safe_{uuid.uuid4().hex[:8]}@test.com",
            "name": "User",
            "password": "mypassword123"
        })
        data = response.json()
        assert "password" not in str(data)
        assert "password_hash" not in str(data)


@pytest.mark.integration
class TestLogin:
    @pytest.fixture(autouse=True)
    def register_user(self, client):
        self.email = f"login_{uuid.uuid4().hex[:8]}@test.com"
        self.password = "testpassword123"
        client.post("/api/auth/register", json={
            "email": self.email, "name": "Login User", "password": self.password
        })

    def test_login_success(self, client):
        response = client.post("/api/auth/login", json={
            "email": self.email, "password": self.password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 20

    def test_login_wrong_password(self, client):
        response = client.post("/api/auth/login", json={
            "email": self.email, "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", json={
            "email": "nobody@test.com", "password": "anypassword"
        })
        assert response.status_code == 401

    def test_login_returns_user_info(self, client):
        response = client.post("/api/auth/login", json={
            "email": self.email, "password": self.password
        })
        data = response.json()
        assert data["user"]["email"] == self.email
        assert "id" in data["user"]


@pytest.mark.integration
class TestProtectedEndpoints:
    def test_no_token_returns_403(self, client):
        response = client.get("/api/tasks")
        assert response.status_code in (401, 403)

    def test_invalid_token_returns_401(self, client):
        response = client.get("/api/tasks", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert response.status_code == 401

    def test_valid_token_allows_access(self, client, auth_headers):
        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200

    def test_me_endpoint_returns_user(self, client, auth_headers, registered_user):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == registered_user["user"]["email"]
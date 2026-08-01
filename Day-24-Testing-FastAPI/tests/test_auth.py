# ============================================================
# tests/test_auth.py
# Authentication endpoint tests
# ============================================================

import pytest
from fastapi.testclient import TestClient


class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123",
            "full_name": "New User"
        })
        assert response.status_code == 201
        body = response.json()
        assert body["username"] == "newuser"
        assert body["email"] == "new@example.com"
        assert body["role"] == "user"    # always user, never admin
        assert "id" in body
        assert "hashed_password" not in body
        assert "password" not in body

    def test_register_minimum_fields(self, client: TestClient):
        """Only username, email, password are required."""
        response = client.post("/api/v1/auth/register", json={
            "username": "minuser",
            "email": "min@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 201

    def test_register_duplicate_email(self, client: TestClient, regular_user):
        response = client.post("/api/v1/auth/register", json={
            "username": "otherusername",
            "email": regular_user.email,
            "password": "SecurePass123"
        })
        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client: TestClient, regular_user):
        response = client.post("/api/v1/auth/register", json={
            "username": regular_user.username,
            "email": "other@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 409
        assert "username" in response.json()["detail"].lower()

    @pytest.mark.parametrize("password,should_fail", [
        ("SecurePass123", False),      # valid
        ("short1", True),              # too short
        ("alllowercase", True),        # no numbers/special chars
        ("12345678", True),            # all numbers
        ("ALLUPPERCASE1", False),      # valid - has number
        ("abc", True),                 # way too short
    ])
    def test_register_password_validation(
        self, client: TestClient, password: str, should_fail: bool
    ):
        response = client.post("/api/v1/auth/register", json={
            "username": f"user_{password[:5]}",
            "email": f"{password[:5]}@test.com",
            "password": password
        })
        if should_fail:
            assert response.status_code == 422
        else:
            assert response.status_code in (201, 409)

    @pytest.mark.parametrize("username,valid", [
        ("validuser", True),
        ("valid_user", True),
        ("valid123", True),
        ("has space", False),
        ("has@symbol", False),
        ("ab", False),             # too short (< 3)
        ("a" * 51, False),         # too long (> 50)
        ("ValidUser", True),       # will be lowercased
    ])
    def test_register_username_validation(
        self, client: TestClient, username: str, valid: bool
    ):
        response = client.post("/api/v1/auth/register", json={
            "username": username,
            "email": f"test_{username[:8]}@test.com",
            "password": "SecurePass123"
        })
        if valid:
            assert response.status_code in (201, 409)
        else:
            assert response.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login (form) and /login/json"""

    def test_login_form_success(self, client: TestClient, regular_user):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "UserPass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert isinstance(body["expires_in"], int)
        assert body["expires_in"] > 0

    def test_login_json_success(self, client: TestClient, regular_user):
        response = client.post("/api/v1/auth/login/json", json={
            "username": "testuser",
            "password": "UserPass123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client: TestClient, regular_user):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "WrongPass999"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Non-existent user: MUST return 401, not 404."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody", "password": "anypass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401    # not 404!

    def test_login_deactivated_user(self, client: TestClient, inactive_user):
        """Deactivated user cannot login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive", "password": "InactivePass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 400


class TestProtectedEndpoints:
    """Test authentication requirements on protected routes."""

    def test_me_with_valid_token(
        self, client: TestClient, user_headers, regular_user
    ):
        response = client.get("/api/v1/auth/me", headers=user_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["username"] == regular_user.username
        assert body["id"] == regular_user.id
        assert "hashed_password" not in body

    def test_me_without_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.parametrize("bad_token", [
        "not-a-jwt",
        "Bearer notabearer",
        "eyJhbGciOiJIUzI1NiJ9.invalid.signature",
        "",
    ])
    def test_me_with_bad_token(self, client: TestClient, bad_token: str):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {bad_token}"}
        )
        assert response.status_code == 401


class TestRefreshAndLogout:
    """Token refresh and logout flow."""

    def test_refresh_success(self, client: TestClient, regular_user):
        login = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "UserPass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        refresh_token = login.json()["refresh_token"]
        original_access = login.json()["access_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        new_access = response.json()["access_token"]
        assert new_access != original_access    # new token issued

    def test_cannot_use_access_token_as_refresh(
        self, client: TestClient, user_token: str
    ):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": user_token}    # wrong type!
        )
        assert response.status_code == 401

    def test_logout_success(self, client: TestClient, user_headers):
        response = client.post(
            "/api/v1/auth/logout",
            headers=user_headers
        )
        assert response.status_code == 200
        assert "message" in response.json()

    def test_change_password_success(
        self, client: TestClient, user_headers, regular_user
    ):
        response = client.put(
            "/api/v1/auth/change-password",
            json={
                "current_password": "UserPass123",
                "new_password": "NewSecure456!",
                "confirm_new_password": "NewSecure456!"
            },
            headers=user_headers
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(
        self, client: TestClient, user_headers
    ):
        response = client.put(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WRONGPASSWORD",
                "new_password": "NewSecure456!",
                "confirm_new_password": "NewSecure456!"
            },
            headers=user_headers
        )
        assert response.status_code == 400

    def test_change_password_mismatch(
        self, client: TestClient, user_headers
    ):
        response = client.put(
            "/api/v1/auth/change-password",
            json={
                "current_password": "UserPass123",
                "new_password": "NewSecure456!",
                "confirm_new_password": "DifferentPass789!"
            },
            headers=user_headers
        )
        assert response.status_code == 422
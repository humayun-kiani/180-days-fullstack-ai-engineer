# backend/tests/unit/test_security.py
import pytest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, decode_token
)


@pytest.mark.unit
class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("password123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_not_plaintext(self):
        plain = "mysecretpassword"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses random salt — same input, different output."""
        h1 = hash_password("password123")
        h2 = hash_password("password123")
        assert h1 != h2

    def test_verify_correct_password(self):
        plain = "correct_password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    @pytest.mark.parametrize("password", [
        "short",
        "a" * 100,
        "p@$$w0rd!",
        "unicode_ünïcödé",
        "   spaces   ",
    ])
    def test_hash_various_passwords(self, password):
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


@pytest.mark.unit
class TestJWT:
    def test_create_token_returns_string(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        user_id = "user-123"
        token = create_access_token(user_id)
        decoded = decode_token(token)
        assert decoded == user_id

    def test_decode_invalid_token_returns_none(self):
        assert decode_token("not.a.valid.token") is None

    def test_decode_empty_token_returns_none(self):
        assert decode_token("") is None

    def test_decode_tampered_token_returns_none(self):
        token = create_access_token("user-123")
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_token_contains_correct_subject(self):
        """Token payload should contain the user ID as subject."""
        from jose import jwt
        from app.core.config import settings
        token = create_access_token("specific-user-id")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "specific-user-id"

    def test_different_users_get_different_tokens(self):
        t1 = create_access_token("user-1")
        t2 = create_access_token("user-2")
        assert t1 != t2
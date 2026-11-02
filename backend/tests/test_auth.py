import pytest
from fastapi import HTTPException


def test_unknown_email_still_performs_argon2_password_verification(monkeypatch):
    from app.routers import auth

    attempted = []

    monkeypatch.setattr(auth.settings, "app_secret_key", "test-secret-" + "x" * 32)
    monkeypatch.setattr(auth, "_load_user", lambda db, email: None)

    def verify(password, encoded_hash):
        attempted.append((password, encoded_hash))
        return False

    monkeypatch.setattr(auth.password_hash, "verify", verify)

    with pytest.raises(HTTPException) as error:
        auth.login(
            auth.LoginRequest(email="unknown@example.org", password="not-the-password"),
            db=object(),
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Email or password is incorrect."
    assert attempted == [("not-the-password", auth.DUMMY_PASSWORD_HASH)]

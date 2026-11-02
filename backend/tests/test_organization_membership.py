import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from uuid import uuid4


def test_organization_member_addition_is_admin_scoped_and_role_bounded():
    from app.main import app
    from app.routers.organizations import MemberAdd

    paths = app.openapi()["paths"]
    assert "post" in paths["/api/v1/organizations/members"]
    assert MemberAdd(email="  COLLEAGUE@example.org ", role="reviewer").email == "colleague@example.org"
    with pytest.raises(ValidationError):
        MemberAdd(email="colleague@example.org", role="organization_admin")
    with pytest.raises(ValidationError):
        MemberAdd(email="not-an-email", role="reviewer")


def test_user_can_list_organizations_and_switch_only_to_an_active_membership(monkeypatch):
    from app.main import app
    from app.routers import auth

    paths = app.openapi()["paths"]
    assert "get" in paths["/api/v1/auth/organizations"]
    assert "post" in paths["/api/v1/auth/switch-organization"]

    user_id = uuid4()
    organization_id = uuid4()
    captured = {"calls": []}

    class FakeResult:
        def mappings(self):
            return self

        def first(self):
            return {
                "id": user_id,
                "email": "member@example.org",
                "display_name": "Member",
                "is_active": True,
                "organization_id": organization_id,
                "role": "reviewer",
                "organization_name": "Research Group",
            }

    class FakeDatabase:
        def execute(self, statement, parameters):
            captured["calls"].append({
                "statement": str(statement),
                "parameters": parameters,
            })
            return FakeResult()

        def commit(self):
            pass

    monkeypatch.setattr(auth, "_create_access_token", lambda uid, oid, role: "switched-token")
    result = auth.switch_organization(
        auth.SwitchOrganizationRequest(organization_id=organization_id),
        {"id": str(user_id), "organization_id": str(uuid4()), "role": "researcher"},
        FakeDatabase(),
    )

    membership_lookup = captured["calls"][0]
    assert "om.organization_id = :organization_id" in membership_lookup["statement"]
    assert membership_lookup["parameters"] == {"user_id": str(user_id), "organization_id": organization_id}
    assert any("organization_context_switched" in call["statement"] for call in captured["calls"])
    assert result["access_token"] == "switched-token"
    assert result["user"]["organization_id"] == str(organization_id)
    assert result["user"]["role"] == "reviewer"



def test_only_organization_admin_can_add_existing_members():
    from app.routers.organizations import MemberAdd, add_existing_member

    with pytest.raises(HTTPException) as error:
        add_existing_member(
            MemberAdd(email="colleague@example.org", role="reviewer"),
            {"id": str(uuid4()), "organization_id": str(uuid4()), "role": "researcher"},
            db=object(),
        )
    assert error.value.status_code == 403


def test_login_request_and_user_lookup_support_an_explicit_organization():
    from app.routers.auth import LoginRequest, _load_user

    organization_id = uuid4()
    request = LoginRequest(
        email="member@example.org",
        password="a-long-enough-password",
        organization_id=organization_id,
    )
    captured = {}

    class FakeResult:
        def mappings(self):
            return self

        def first(self):
            return None

    class FakeDatabase:
        def execute(self, statement, parameters):
            captured["statement"] = str(statement)
            captured["parameters"] = parameters
            return FakeResult()

    _load_user(FakeDatabase(), request.email, request.organization_id)
    assert "om.organization_id = :organization_id" in captured["statement"]
    assert captured["parameters"]["organization_id"] == organization_id


def test_login_falls_back_when_saved_organization_membership_is_no_longer_active(monkeypatch):
    from app.routers import auth

    preferred_organization = uuid4()
    active_organization = uuid4()
    user_id = uuid4()
    lookup_organizations = []

    active_user = {
        "id": user_id,
        "email": "member@example.org",
        "display_name": "Member",
        "organization_id": active_organization,
        "organization_name": "Current Research Group",
        "role": "researcher",
        "is_active": True,
        "password_hash": "stored-hash",
    }

    def load_user(db, email, organization_id=None):
        lookup_organizations.append(organization_id)
        return None if organization_id == preferred_organization else active_user

    monkeypatch.setattr(auth.settings, "app_secret_key", "test-secret-" + "x" * 32)
    monkeypatch.setattr(auth, "_load_user", load_user)
    monkeypatch.setattr(auth, "enforce_rate_limit", lambda *args, **kwargs: None)
    class FakePasswordHash:
        def verify(self, password, stored_hash):
            return True

    monkeypatch.setattr(auth, "password_hash", FakePasswordHash())
    monkeypatch.setattr(auth, "_create_access_token", lambda uid, oid, role: "fallback-token")

    result = auth.login(
        auth.LoginRequest(
            email="member@example.org",
            password="correct-password",
            organization_id=preferred_organization,
        ),
        request=type("Request", (), {"client": type("Client", (), {"host": "127.0.0.1"})()})(),
        db=object(),
    )

    assert lookup_organizations == [preferred_organization, None]
    assert result["access_token"] == "fallback-token"
    assert result["user"]["organization_id"] == str(active_organization)



def test_authenticated_user_binds_transaction_local_organization_context(monkeypatch):
    from app.routers import auth

    user_id = uuid4()
    organization_id = uuid4()
    calls = []

    class FakeResult:
        def mappings(self):
            return self

        def first(self):
            return {
                "id": user_id,
                "email": "member@example.org",
                "display_name": "Member",
                "organization_id": organization_id,
                "role": "researcher",
                "is_active": True,
                "organization_name": "Research Group",
            }

    class FakeDatabase:
        def execute(self, statement, parameters):
            calls.append((str(statement), parameters))
            return FakeResult()

    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda token, *args, **kwargs: {"sub": str(user_id), "org": str(organization_id)},
    )
    user = auth.get_current_user(token="valid-signed-token", db=FakeDatabase())

    assert user["organization_id"] == str(organization_id)
    assert len(calls) == 3
    assert "set_config('app.organization_id', :organization_id, true)" in calls[1][0]
    assert calls[1][1] == {"organization_id": str(organization_id)}
    assert "set_config('app.user_id', :user_id, true)" in calls[2][0]
    assert calls[2][1] == {"user_id": str(user_id)}

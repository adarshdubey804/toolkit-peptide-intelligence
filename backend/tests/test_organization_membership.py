import pytest
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
    captured = {}

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
            captured["statement"] = str(statement)
            captured["parameters"] = parameters
            return FakeResult()

    monkeypatch.setattr(auth, "_create_access_token", lambda uid, oid, role: "switched-token")
    result = auth.switch_organization(
        auth.SwitchOrganizationRequest(organization_id=organization_id),
        {"id": str(user_id), "organization_id": str(uuid4()), "role": "researcher"},
        FakeDatabase(),
    )

    assert "om.organization_id = :organization_id" in captured["statement"]
    assert captured["parameters"] == {"user_id": str(user_id), "organization_id": organization_id}
    assert result["access_token"] == "switched-token"
    assert result["user"]["organization_id"] == str(organization_id)
    assert result["user"]["role"] == "reviewer"

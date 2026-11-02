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

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROUTERS = BACKEND_ROOT / "app" / "routers"


def _source(name: str) -> str:
    return (ROUTERS / name).read_text(encoding="utf-8")


def test_dossier_and_curation_decisions_keep_owner_organization():
    dossiers = _source("dossiers.py")
    curation = _source("curation.py")
    assert "owner_organization_id)" in dossiers
    assert "owner_organization_id" in curation
    assert "cr.owner_organization_id = :organization_id" in curation
    assert "cr.owner_organization_id = :org" in curation


def test_enrichment_and_evidence_claim_access_use_review_owner_not_current_memberships():
    for filename in ("enrichment.py", "evidence_intelligence.py"):
        source = _source(filename)
        assert "owner_organization_id" in source, filename
        assert "JOIN organization_memberships om ON om.user_id=cr.submitted_by" not in source, filename


def test_interaction_submissions_are_owner_scoped_and_not_public_by_verification_alone():
    source = _source("interactions.py")
    assert "owner_organization_id, visibility_scope" in source
    assert "'organization'" in source
    assert "a.visibility_scope='public'" in source
    assert "a.owner_organization_id=:org" in source
    assert "JOIN organization_memberships om ON om.user_id=a.submitted_by" not in source


def test_interaction_and_decision_owner_migration_is_present():
    migration = (
        BACKEND_ROOT.parent / "database" / "migrations" / "041_interaction_and_decision_ownership.sql"
    ).read_text(encoding="utf-8")
    assert "curation_decisions" in migration
    assert "molecular_interaction_assessments" in migration
    assert "owner_organization_id" in migration
    assert "visibility_scope" in migration



def test_batch_analytical_result_cannot_reference_another_organizations_private_method():
    source = _source("vendor_materials.py")
    assert "visibility_scope='public' OR owner_organization_id=:org" in source
    assert '{"id": payload.method_id, "org": org}' in source


def test_public_material_offerings_do_not_expose_unverified_site_identifiers():
    source = _source("vendor_materials.py")
    assert "site.id AS site_id" in source
    assert "v.legal_name AS vendor_name, o.site_id" not in source



def test_authenticated_request_sets_transaction_local_rls_organization_context():
    auth_source = (BACKEND_ROOT / "app" / "routers" / "auth.py").read_text(encoding="utf-8")
    assert "set_config('app.organization_id', :organization_id, true)" in auth_source
    assert "UUID(claims[\"org\"])" in auth_source

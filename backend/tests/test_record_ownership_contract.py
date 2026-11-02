from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "database" / "migrations"


def test_explicit_record_ownership_migration_preserves_ambiguous_legacy_rows():
    sql = (MIGRATIONS / "038_explicit_record_ownership.sql").read_text(encoding="utf-8")
    for expected in (
        "owner_organization_id",
        "visibility_scope TEXT NOT NULL DEFAULT 'restricted'",
        "HAVING count(*) = 1",
        "SET visibility_scope = 'restricted'",
        "formulation_visibility_scope_check",
        "process_knowledge_visibility_scope_check",
        "analytical_method_visibility_scope_check",
        "formulation_owner_scope_check",
        "process_knowledge_owner_scope_check",
        "analytical_method_owner_scope_check",
    ):
        assert expected in sql


def test_formulation_and_process_submissions_persist_tenant_owner():
    formulations = (ROOT / "backend" / "app" / "routers" / "formulations.py").read_text(encoding="utf-8")
    process = (ROOT / "backend" / "app" / "routers" / "process_knowledge.py").read_text(encoding="utf-8")
    assert "owner_organization_id, visibility_scope" in formulations
    assert "'in_review', :submitter, :org, 'organization'" in formulations
    assert "fp.owner_organization_id=:org" in formulations
    assert "fp.visibility_scope='public'" in formulations
    assert "owner_organization_id, visibility_scope" in process
    assert "'in_review', :submitter, :org, 'organization'" in process
    assert "pk.owner_organization_id=:org" in process
    assert "pk.visibility_scope='public'" in process


def test_analytical_method_submission_persists_tenant_owner_and_hides_private_records():
    methods = (ROOT / "backend" / "app" / "routers" / "analytical_methods.py").read_text(encoding="utf-8")
    assert "owner_organization_id, visibility_scope" in methods
    assert "'in_review', :submitter, :org, 'organization'" in methods
    assert "am.owner_organization_id=:org" in methods
    assert "am.visibility_scope='public'" in methods


def test_curation_review_uses_persisted_owner_not_current_submitter_membership():
    curation = (ROOT / "backend" / "app" / "routers" / "curation.py").read_text(encoding="utf-8")
    assert "submitted_by, owner_organization_id)" in curation
    assert "cr.owner_organization_id = :organization_id" in curation
    assert "cr.owner_organization_id = :org" in curation
    assert "JOIN organization_memberships om ON om.user_id = cr.submitted_by" not in curation

def test_organization_applicability_and_lab_claims_are_private_by_default():
    migration = (MIGRATIONS / "038_explicit_record_ownership.sql").read_text(encoding="utf-8")
    methods = (ROOT / "backend" / "app" / "routers" / "analytical_methods.py").read_text(encoding="utf-8")
    for expected in (
        "ALTER TABLE peptide_method_applicability",
        "ALTER TABLE peptide_test_applicability",
        "ALTER TABLE laboratory_capability_claims",
        "peptide_method_applicability_visibility_check",
        "peptide_test_applicability_visibility_check",
        "laboratory_capability_visibility_check",
    ):
        assert expected in migration
    assert "a.visibility_scope='public'" in methods
    assert "lc.visibility_scope='public'" in methods
    assert "m.visibility_scope='public'" in methods
    assert "owner_organization_id=:org" in methods

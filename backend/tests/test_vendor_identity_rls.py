from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_vendor_identity_site_certification_rls_covers_all_owner_tables():
    sql = (MIGRATIONS / "054_vendor_identity_site_certification_row_level_security.sql").read_text(encoding="utf-8")
    for table in (
        "vendors", "vendor_sources", "vendor_review_decisions",
        "vendor_sites", "vendor_site_sources", "vendor_site_decisions",
        "vendor_certifications", "vendor_certification_decisions",
    ):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "vendor_sites.organization_id=vendor.organization_id" in sql
    assert "site.vendor_id=vendor_certifications.vendor_id" in sql
    assert "vendor_certifications.organization_id" not in sql

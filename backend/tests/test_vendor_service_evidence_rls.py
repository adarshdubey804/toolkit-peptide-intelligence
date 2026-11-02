from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_vendor_service_evidence_rls_covers_services_links_and_decisions():
    sql = (MIGRATIONS / "055_vendor_service_evidence_row_level_security.sql").read_text(encoding="utf-8")
    for table in (
        "vendor_services", "vendor_service_decisions",
        "vendor_service_evidence_links", "vendor_service_evidence_link_decisions",
    ):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "vendor_services.site_id" in sql
    assert "vendor_service_evidence_links.review_status='verified'" in sql
    assert "peptide.review_status='verified'" in sql
    assert "method.review_status='verified'" in sql

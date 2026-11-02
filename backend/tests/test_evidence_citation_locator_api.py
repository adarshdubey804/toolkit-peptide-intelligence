import pytest
from pydantic import ValidationError

from app.routers.evidence_intelligence import CitationLocatorInput


def test_citation_locator_input_trims_locator_value_and_accepts_sha256_hash():
    payload = CitationLocatorInput(
        claim_source_id="00000000-0000-0000-0000-000000000001",
        locator_type="figure",
        locator_value="  Figure 3  ",
        quoted_text_hash="a" * 64,
    )
    assert payload.locator_value == "Figure 3"
    assert payload.quoted_text_hash == "a" * 64


@pytest.mark.parametrize("value", ["", "   ", "Figure " + "x" * 1000])
def test_citation_locator_input_rejects_blank_or_oversized_locator_values(value):
    with pytest.raises(ValidationError):
        CitationLocatorInput(
            claim_source_id="00000000-0000-0000-0000-000000000001",
            locator_type="figure",
            locator_value=value,
        )


@pytest.mark.parametrize("digest", ["A" * 64, "z" * 64, "1234"])
def test_citation_locator_input_rejects_noncanonical_sha256_hash(digest):
    with pytest.raises(ValidationError):
        CitationLocatorInput(
            claim_source_id="00000000-0000-0000-0000-000000000001",
            locator_type="figure",
            locator_value="Figure 3",
            quoted_text_hash=digest,
        )


def test_citation_locator_route_checks_claim_source_organization_and_version_link():
    import inspect
    from app.routers import evidence_intelligence

    source = inspect.getsource(evidence_intelligence.add_citation_locator)
    assert "owner_organization_id=:org" in source
    assert "version.source_record_id=:source_record_id" in source
    assert "INSERT INTO claim_source_locators" in source
    assert "db.commit()" in source

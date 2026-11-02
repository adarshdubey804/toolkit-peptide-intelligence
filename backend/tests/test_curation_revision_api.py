def test_curation_revision_routes_are_registered_and_revision_scoped():
    paths = app.openapi()["paths"]
    assert "/api/v1/curation/claims/{claim_id}/revisions" in paths
    assert "get" in paths["/api/v1/curation/claims/{claim_id}/revisions"]
    assert "/api/v1/curation/reviews/{review_id}/claim-revision" in paths
    assert "get" in paths["/api/v1/curation/reviews/{review_id}/claim-revision"]

    from inspect import getsource
    from app.routers import curation

    revisions_source = getsource(curation.list_claim_revisions)
    review_source = getsource(curation.get_review_claim_revision)
    assert "owner_organization_id=:org" in revisions_source
    assert "owner_organization_id=:org" in review_source
    assert "review.evidence_claim_revision_id" in review_source
    assert "revision.claim_id=review.entity_id" in review_source

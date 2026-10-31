from app.services.ai_synthesis import _audit_answer


def test_citation_audit_accepts_allowed_inline_identifiers():
    records = [{"citation_id": "pubmed:123"}]

    audit = _audit_answer(
        "Supported finding [pubmed:123].",
        records,
    )

    assert audit["valid_ids"] == ["pubmed:123"]
    assert audit["invalid_ids"] == []
    assert audit["uncited_sentence_count"] == 0
    assert audit["status"] == "passed"


def test_citation_audit_flags_unknown_and_uncited_sentences():
    records = [{"citation_id": "pubmed:123"}]

    audit = _audit_answer(
        "Supported finding [pubmed:123]. Unknown citation [fake:999]. Uncited statement.",
        records,
    )

    assert audit["valid_ids"] == ["pubmed:123"]
    assert audit["invalid_ids"] == ["fake:999"]
    assert audit["uncited_sentence_count"] == 2
    assert audit["status"] == "warning"

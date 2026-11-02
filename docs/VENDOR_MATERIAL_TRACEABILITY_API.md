# Vendor material and batch traceability API

These endpoints record source-backed vendor catalogue offerings, physical lots and analytical reports. They are research/provenance records, not a purchasing system, live inventory feed, product release decision or clinical recommendation.

## Submission and discovery

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/v1/vendor-materials/offerings` | Public | List only public, reviewed offerings tied to verified vendor, peptide and exact chemical form records |
| POST | `/api/v1/vendor-materials/offerings` | Authenticated organization submitter | Submit a vendor offering and source evidence |
| GET | `/api/v1/vendor-materials/offerings/{offering_id}/batches` | Owning organization | List physical lots for an offering |
| POST | `/api/v1/vendor-materials/offerings/{offering_id}/batches` | Authenticated organization submitter | Submit a source-backed physical lot |
| POST | `/api/v1/vendor-materials/batches/{batch_id}/test-results` | Authenticated organization submitter | Attach a source-backed analytical result to a lot |
| GET | `/api/v1/vendor-materials/reviews` | Organization curator/reviewer | View pending offerings, lots and analytical results |
| POST | `/api/v1/vendor-materials/reviews/{record_type}/{record_id}/decisions` | Organization curator/reviewer | Record an independent review decision |

## Evidence and review rules

- Every submission requires a source name, source identifier, HTTPS source URL and a concise statement of what the source supports.
- An offering must identify the exact reviewed chemical form; a peptide sequence alone is insufficient.
- Offerings require a verified vendor identity and, when supplied, a verified site/service belonging to that vendor.
- A lot identifier is unique within its offering. Manufacture, retest and expiry dates are checked for chronological consistency.
- Analytical results must reference reviewed analytical test and method catalogue records and include an observed numeric or textual result.
- A reported `pass` is a supplier/laboratory-reported result, not proof of method validation, product suitability or clinical safety.
- Submission records begin in `in_review`. Submitters cannot review their own records.
- Only a reviewer decision can verify an offering and assign its visibility scope. New offerings are restricted by default.
- Lot records and analytical reports remain organization-scoped. Public discovery exposes offerings only when they are verified and explicitly marked `public`.
- Evidence fields are immutable after submission. Corrections should be new, superseding records; review state and reviewer-controlled offering visibility are separate moderation fields.
- Supplier availability is a recorded source statement, not live stock.

## Example offering submission

```json
{
  "vendor_id": "00000000-0000-0000-0000-000000000001",
  "peptide_id": "00000000-0000-0000-0000-000000000002",
  "chemical_form_id": "00000000-0000-0000-0000-000000000003",
  "product_name": "Example peptide material",
  "source_name": "Supplier catalogue",
  "source_identifier": "CAT-123",
  "source_url": "https://supplier.example/catalogue/CAT-123",
  "evidence_scope": "Catalogue page identifies the supplier product and stated material description."
}
```

## Example batch analytical result

```json
{
  "test_id": "00000000-0000-0000-0000-000000000004",
  "method_id": "00000000-0000-0000-0000-000000000005",
  "observed_value": 98.2,
  "result_unit": "%",
  "result_status": "pass",
  "source_name": "Supplier certificate of analysis",
  "source_identifier": "COA-LOT-123",
  "source_url": "https://supplier.example/reports/COA-LOT-123",
  "evidence_scope": "Reported purity result for the named supplier lot."
}
```

The API stores these values as submitted evidence and does not infer that the result establishes product release, a universal acceptance criterion or validated analytical performance.

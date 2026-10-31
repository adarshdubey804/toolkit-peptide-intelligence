# Data governance

## Source provenance
Every imported record must retain source name, stable source identifier, canonical source URL, retrieval timestamp, source version where available, content hash and raw source metadata. Re-fetching a record should update its last-seen metadata and create a new immutable source-record version when the content hash changes. Do not silently overwrite the prior payload.

## Entity resolution
Cross-database mappings are candidate relationships, not proof of identity. A UniProt protein accession, PDB structure, PubChem compound CID, peptide sequence and clinical-trial intervention may describe related but non-identical entities. Store the relationship type, match method and confidence; require human review before asserting same-entity equivalence or attaching properties to a peptide profile.

## Scientific claims and evidence
For every published scientific claim retain claim text, source identifier/URL, retrieval date, study design/model, population or experimental system, result, limitations, evidence classification, review status, reviewer and review date. Distinguish measured, calculated, predicted and manually curated values. Preserve conflicting records and correction history. High-impact clinical, analytical, regulatory and quality claims require qualified review.

## Editorial review
Imported source records begin as unreviewed. Review queues must track assignment, priority, status and rationale. Decisions are append-only and must preserve reviewer identity, timestamp, prior status, new status and explanation. A verified record means editorial review of the record; it does not mean regulatory approval, clinical endorsement or validation for manufacturing use.

## Access control
The current schema is a data foundation, not a complete authorization implementation. Do not expose review or decision mutation endpoints until authentication, role-based authorization, organization isolation, audit logging and reviewer qualification checks are implemented and tested.

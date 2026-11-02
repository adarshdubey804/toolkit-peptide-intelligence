# Database Architecture Audit

**Audit date:** 2026-11-02  
**Scope:** Repository schema and application access patterns on `main`, migrations 001–045, and relevant backend routers.  
**Important limitation:** This is a repository-level architecture review. It does not establish the live PostgreSQL database's current schema, data quality, query plans, backup state, or deployment configuration. Those require access to the deployed database and environment.

## Executive assessment

The database is moving in a sound direction. It has a normalized scientific core, source provenance, review workflows, separate analytical testing and peptide applicability models, vendor/facility evidence, regulatory versioning, organization memberships, and append-only decision histories.

It is not yet ready to be treated as a complete, production-grade scientific data platform. The main risks are not a lack of tables; they are inconsistent ownership semantics, incomplete peptide chemical identity, uneven version history, and reliance on application SQL for tenant isolation without visible PostgreSQL row-level security policies.

**Recommendation:** Stabilize the domain model and governance contracts before bulk-importing large peptide/vendor/protocol datasets or expanding AI write capabilities.

## What is already strong

1. **Scientific entities are separated:** peptides, aliases, sequences, chemical properties, structures, targets, pathways, publications, studies, claims, and claim sources are separate relations rather than one overloaded peptide table.
2. **Provenance is a first-class concern:** source records, external entity links, source-record versions, and source-backed relationships exist.
3. **Curation is not merely a status field:** review queues and decision-history tables exist, and many decision tables reject UPDATE/DELETE.
4. **Evidence appraisal preserves distinct dimensions:** study design, evidence level, risk of bias, replication status, limitations, and independent decisions are not collapsed into a misleading single score.
5. **Analytical test architecture is maturing:** a test catalogue, catalogue sources, peptide-specific applicability, reference frameworks, and laboratory capability claims are represented separately.
6. **Vendor claims are more granular than vendor marketing profiles:** services, facilities, certifications, evidence links, and review decisions have separate structures.
7. **Regulatory information has version and observation workflows:** source registries, observations, poll runs, change events, and decisions are represented.
8. **Organization memberships and project membership are explicit:** the schema correctly treats membership as the authorization source of truth rather than relying solely on the legacy profile organization field.

## Findings and risks

### P0 — Tenant ownership is not consistently explicit

The schema deliberately separates shared scientific master data from organization-submitted records. Migrations 038–041 introduce explicit `owner_organization_id` and visibility scopes for curation reviews/decisions, analytical methods, formulation profiles, process-knowledge profiles, and molecular-interaction assessments. The associated submission, review, evidence-claim, dossier, and enrichment access paths are being aligned to those stored owners rather than deriving tenant scope from a submitter's current memberships.

The remaining ownership work is operational and defensive: ambiguous legacy rows must be resolved through a controlled process, every new submission path must set its owner, and cross-tenant negative tests must cover every router. A verified record is not automatically public where its visibility scope remains organization-private.

**Required design:** Keep immutable owner IDs on organization submissions and explicit visibility/publication state. Child records inherit access only through an explicitly owned parent. Shared master data such as peptides, publications, targets, pathways, and source records must not receive arbitrary tenant ownership. Public promotion must be a separate, reviewed transition.


**Current ownership model after migrations 038–041:**

| Data class | Ownership and visibility rule |
|---|---|
| Curation submissions | Review request stores owner organization; decisions inherit the review owner. |
| Analytical methods, formulations, process knowledge | Parent record stores owner organization and visibility scope; verified organization submissions remain private until separately promoted. |
| Molecular interaction assessments | Parent record stores owner organization and public/organization/restricted visibility; verified status alone does not publish it. |
| Applicability and laboratory capability claims | Organization ID plus explicit visibility scope; verified status alone does not publish them. |
| Vendor services/certifications and regulatory versions/events | Ownership is inherited through the organization-owned vendor or regulatory guidance parent; child-to-parent scope must be enforced. |
| Shared scientific master data | Global/system-owned; public access follows verified publication rules, not submitter membership. |

Legacy records with ambiguous owners remain NULL/restricted and must be resolved manually. Do not assign them to whichever organization the submitter currently has selected.

### P0 — Tenant isolation is application-enforced, not visibly database-enforced

The inspected migrations contain organization membership and organization-scoped query patterns, but no PostgreSQL `ENABLE ROW LEVEL SECURITY` or `CREATE POLICY` statements were found in the migration set.

A missed organization predicate in one endpoint can therefore expose another tenant's data.

**Required design:** Decide explicitly between (a) PostgreSQL RLS with transaction-local tenant context and carefully scoped service roles, or (b) a rigorously centralized repository/service layer with mandatory tenant scope and comprehensive cross-tenant integration tests. RLS is recommended for organization-private records. Public, verified scientific master data should remain deliberately readable according to its publication rules. Do not enable RLS without testing connection-pool context reset and background-worker behavior.

### P1 — Peptide chemical identity is not yet canonical

The initial schema stores sequence, terminal annotations, stereochemistry notes, and modifications JSONB, but the inspected schema does not define a canonical identity representation or a uniqueness strategy for chemically identical records.

Risks include duplicate records caused by aliases, sequence formatting, D/L residues, noncanonical residues, terminal chemistry, cyclization, conjugation, salts, and different chemical forms. A plain amino-acid sequence is not enough to establish chemical identity.

**Required design:** Introduce a versioned canonical identity model:
- Preserve the submitted/raw representation and source.
- Store a normalized sequence/monomer representation with explicit residue identifiers and stereochemistry.
- Represent modifications and terminal chemistry as structured, validated records (not unconstrained JSON alone).
- Distinguish peptide entity, molecular/chemical form, and batch/material.
- Store a deterministic identity fingerprint with a documented canonicalization version.
- Keep calculated descriptors separate from experimentally measured values and preserve calculation method/tool/version and parameters.

Do not impose a uniqueness constraint until canonicalization rules and collision/alias handling are tested against representative peptides.

### P1 — Version history is uneven across domain entities

Source records have version support and several decision tables are append-only. However, important mutable scientific parent records (for example formulation/process profiles, vendor service details, method records, and peptide properties) do not share one clearly defined universal revision/supersession contract in the inspected schema.

**Required design:** Add explicit record revisions or immutable snapshots for material scientific changes. Preserve who changed what, when, why, the source basis, and which revision a decision reviewed. A review decision should apply to a specific revision, not silently to a record that may later have changed.

### P1 — Evidence linkage needs a more complete citation locator

Claim/source links retain a publication or source record and an excerpt/relationship, which is a good base. For reproducible scientific review, the system should also support stable citation locators such as DOI/PMID, page, figure, table, section, supplementary file, source content hash, retrieval timestamp, and exact quoted span where licensing permits.

**Required design:** Make evidence links revision-aware and distinguish direct evidence, contextual source, contradiction, and derivative citation. Preserve source/license constraints and avoid copying restricted full text into metadata.

### P1 — Analytical test model is promising but needs method lifecycle semantics

The test catalogue, reference-framework crosswalk, peptide applicability, and lab capability claims are valuable separations. The next layer should distinguish:
- test intent / quality attribute,
- method procedure and version,
- instrument/platform and sample matrix,
- reference standard and traceability,
- validation/verification scope,
- acceptance criteria and the source that authorizes them,
- laboratory/site capability and evidence validity period.

Do not treat a test name or a vendor capability claim as proof that a particular method is validated for a particular peptide/material/purpose. Do not invent universal acceptance criteria.

### P2 — Constraints and normalization need a dedicated pass

The schema contains useful foreign keys, CHECK constraints, and indexes, but the audit has not yet verified every FK's delete behavior, every uniqueness rule, all nullability assumptions, or query-plan adequacy. DOI/PMID normalization, sequence normalization, controlled vocabularies, and duplicate-resolution policies deserve explicit contracts.

**Required design:** Build a machine-readable schema inventory and add integration tests for duplicate identifiers, invalid state transitions, cross-organization references, orphan prevention, and referential integrity.

### P2 — Audit and operational controls remain in progress

PR #40 has been merged: migration 037 adds per-organization SHA-256 audit chains, append-only UPDATE/DELETE protection, and organization-admin event listing/integrity verification. Migration 036 adds shared PostgreSQL rate limits for login, registration, agent execution, and public research discovery. Remaining controls include independent external hash anchoring, rate limits for other sensitive write/enrichment routes, trusted proxy identity configuration, production DB role separation, backup/restore testing, and privileged-operator threat controls.

## Target ownership model

Use three explicit data classes:

| Class | Examples | Ownership and access |
|---|---|---|
| Shared scientific master | canonical peptide identities, publications, targets, pathways, public reference methods | system/global ownership; public read only after governed publication |
| Organization contribution | vendor submissions, private formulations, process records, internal appraisals, project files, internal SOPs | explicit organization owner; accessible only to active members with suitable roles |
| Curated public contribution | organization-submitted record promoted to shared catalogue | retain origin organization and submitter; promotion requires independent review and public visibility state |

A record should not become globally visible merely because a reviewer changed its status to `verified`. The publication scope and verification status are separate dimensions.

## Recommended implementation sequence

1. **Validate merged migrations 036–037 in the target deployment environment**; verify shared rate-limit behavior, audit-chain append/immutability/integrity, and rollback/backup strategy against the actual PostgreSQL version and role permissions.
2. **Create a schema inventory and ownership matrix** for every table: global, organization-owned, derived/cache, append-only history, or operational.
3. **Resolve tenant ownership** for formulation, process knowledge, curation, and other organization-contributed records. Add cross-tenant integration tests before any RLS rollout.
4. **Design canonical peptide identity** with test fixtures covering linear peptides, D-amino acids, noncanonical residues, terminal modifications, cyclization, conjugates, salts, and sequence aliases.
5. **Add revision/supersession semantics** to scientific parent records and bind decisions to exact revisions.
6. **Strengthen citation locators and source versioning** while respecting source licenses.
7. **Run PostgreSQL integration and query-plan checks** against realistic seed volumes; test migrations from an empty database and from the current deployed version.
8. **Only then expand bulk ingestion and AI write workflows.** AI agents should create draft, source-linked contributions; they should not self-verify or publish scientific claims.

## Acceptance criteria for the next schema milestone

- Every table is classified by data ownership and visibility.
- Every tenant-owned table has an explicit organization key and tested access boundary.
- Cross-organization reads/writes fail in integration tests, including direct object-ID access.
- Shared master records have a clear publication/verification policy.
- Canonical peptide identity is deterministic, versioned, and collision-tested.
- Scientific decisions refer to immutable record revisions.
- Source locators and provenance can reconstruct why a claim was accepted.
- Migration tests pass on clean PostgreSQL and upgrade paths.
- No production readiness claim is made until deployed DB, backups, restore, monitoring, secrets, TLS, rate limiting, and role separation are verified.

## Audit conclusion

**Direction: correct. Readiness: still developmental.**

The strongest next move is not to add more tables indiscriminately. It is to formalize ownership, identity, revision, and provenance contracts across the existing modules, then validate them against a real PostgreSQL deployment and realistic scientific records.

## Table ownership inventory (repository-level classification)

The following is the intended classification inferred from the current schema and route behavior. It is a design recommendation, not proof that every existing row already obeys it.

| Table group | Current examples | Target classification | Ownership contract to enforce |
|---|---|---|---|
| Scientific identity | `peptides`, `peptide_aliases`, `peptide_sequences`, `chemical_properties`, `structures` | Shared scientific master | Global after curation; retain source and revision provenance |
| Scientific references | `targets`, `pathways`, `publications`, `research_studies`, `study_publications` | Shared scientific master | Global records with stable external identifiers and source links |
| Claims and citations | `evidence_claims`, `claim_sources`, `external_entity_links` | Curated public master plus organization drafts | Explicit owner/visibility for drafts; published claims remain globally traceable |
| Source registry | `source_records`, `source_record_versions` | Shared source registry | Global deduplication by source identity; preserve license and content hash |
| Curation workflow | `curation_reviews`, `curation_decisions` | Organization-owned workflow | Persist organization owner on the review row; decisions inherit and verify same owner |
| Enrichment workflow | `enrichment_candidates`, `enrichment_candidate_decisions`, ingestion runs | Organization or system-owned operational records | Explicit tenant/system owner and source ingestion scope |
| Vendor intelligence | `vendors`, `vendor_sites`, `vendor_services`, `vendor_certifications`, source/decision/link tables | Organization contribution with curated-public promotion | Organization owner on submissions; explicit publication state; facility-specific evidence |
| Analytical methods | `analytical_methods`, method sources and decisions | Shared method catalogue plus organization drafts | Explicit owner/visibility; method revision and validation scope |
| Formulation knowledge | `formulation_profiles`, components, stability observations, sources, decisions | Organization-owned contribution; optional curated-public promotion | Explicit organization owner on profile; child rows inherit owner; decisions bind to profile revision |
| Process knowledge | `process_knowledge_profiles`, stages, sources, decisions | Organization-owned contribution; optional curated-public promotion | Explicit organization owner on profile; child rows inherit owner; decisions bind to profile revision |
| Molecular interactions | `molecular_interaction_assessments`, decisions | Organization contribution plus reviewed public assertions | Explicit organization owner or explicit global/system origin |
| AI sessions | `agent_sessions`, `agent_session_messages` | Organization/user-private operational data | Enforce owner user and organization on every read/write |
| Evidence appraisal | `evidence_appraisals`, duplicate candidates and decisions | Organization-owned review records | Explicit organization scope; preserve independent reviewer and immutable decisions |
| Regulatory intelligence | guidance, versions, change events, source registry, observations, poll runs, decisions | Shared public source data plus system-owned ingestion state and organization review | Separate system ingestion from organization decisions; immutable source/version identity |
| Analytical test catalogue | catalogue, sources, decisions, reference frameworks and links | Shared reference catalogue plus governed revisions | Public visibility only after review; reference framework version/effective dates |
| Peptide test applicability | `peptide_test_applicability`, decisions | Organization contribution plus curated-public promotion | Explicit owner, revision-bound decision, source and method scope |
| Platform security | rate-limit buckets, maintenance markers, audit events and chain heads | System operational records; audit events organization/global scoped | Restricted service ownership, retention, append-only policy and independent hash anchoring |

### Ownership invariants to test

- Every organization-owned row has a non-null organization owner that does not depend on the submitter's current membership.
- A child row cannot reference a parent owned by another organization unless the relationship is explicitly a public-master reference.
- A review decision's organization must match the reviewed record's owner.
- Public catalogue queries return only records explicitly published as public, not merely records with a `verified` review status.
- System ingestion records are not implicitly owned by whichever user happens to trigger a poll.
- User suspension or removal does not orphan or silently reassign their organization's scientific contributions.
- Every background worker sets and clears tenant context safely if PostgreSQL RLS is adopted.

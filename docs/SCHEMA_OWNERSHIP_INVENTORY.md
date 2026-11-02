# Schema ownership and governance inventory

**Baseline:** migrations 001–064 on `main` (2026-11-02)  
**Purpose:** define the intended ownership, visibility, provenance, and lifecycle contract for the existing schema before expanding ingestion or AI write access.

> This is a repository-level design inventory. It does not assert that every existing row is compliant, that every route enforces the contract, or that the live PostgreSQL deployment has this exact schema. Validate against the deployed database before enabling database policies or bulk imports.

## Classification vocabulary

- **Shared master:** globally addressable scientific/reference data. Organization membership must not alter its ownership.
- **Organization contribution:** submitted or curated material owned by one immutable organization ID. Visibility is separate from review status.
- **System operational:** ingestion, scheduling, rate-limit, audit, or service state owned by the system or a service principal.
- **User-private:** personal agent/session data scoped to its user and, where applicable, organization.
- **Append-only history:** decision, observation, event, or audit history whose corrections are new records rather than destructive edits.
- **Derived/cache:** reproducible computed output with explicit source/version/tool provenance; never silently promoted to experimental evidence.

## Table-group inventory

| Domain | Existing schema objects / examples | Intended class | Required invariant |
|---|---|---|---|
| Peptide identity | `peptides`, `peptide_aliases`, `peptide_sequences`, `chemical_properties`, `structures`, canonical chemical-form records | Shared master | Keep raw submitted identity, source, chemical form, stereochemistry, and curation state distinct. Sequence equality alone is not chemical identity. |
| Scientific references | `targets`, `pathways`, `publications`, `research_studies`, `study_publications` | Shared master | Stable external identifiers; preserve source and organism/context; do not infer peptide-target causality from a reference link. |
| Claims and citations | `evidence_claims`, `claim_sources`, `external_entity_links` | Shared curated master plus organization drafts | Draft owner and visibility explicit; claims cite exact source and locator; verification and publication are separate. |
| Source provenance | `source_records`, `source_record_versions` | Shared registry; append-only versions | Preserve canonical source identity, retrieval time, content hash, license, and raw source metadata. |
| Curation | `curation_reviews`, `curation_decisions` | Organization contribution; append-only decisions | Review owner immutable; decisions scoped to same owner and exact reviewed revision. |
| Enrichment | `enrichment_candidates`, candidate decisions, ingestion runs | System operational or organization contribution | Triggering user does not determine system ownership; extracted candidates remain unreviewed until a human decision. |
| Vendor intelligence | `vendors`, `vendor_sites`, `vendor_services`, `vendor_certifications`, facility/capability evidence, vendor material offerings and batches | Organization contribution plus reviewed public catalogue | Vendor marketing claims are not independent verification. Keep site, service, certificate, material, batch, test result, source, and visibility separate. |
| Analytical methods | `analytical_methods`, method sources and decisions | Shared catalogue plus organization drafts | Method name is not validation. Preserve version, matrix, instrument, purpose, reference standard, validation scope, and evidence. |
| Formulation | `formulation_profiles`, components, stability observations, sources and decisions | Organization contribution; optional public promotion | Parent owns children; formulation revisions and evidence are traceable; no universal stability claims without source-specific conditions. |
| Process knowledge | `process_knowledge_profiles`, stages, sources and decisions | Organization contribution; optional public promotion | Parent owns children; distinguish process description from validated manufacturing instructions and record revision/evidence. |
| Molecular interactions | `molecular_interaction_assessments`, decisions | Organization contribution or explicit system-origin record | Preserve assay/model context, species, conditions, evidence type, and reviewer; prediction is not experimental confirmation. |
| AI sessions | `agent_sessions`, `agent_session_messages` | User-private / organization-private | RLS now enforces both authenticated user and organization scope on session/message reads and writes; agents produce source-linked drafts, never self-verify or publish. |
| Evidence appraisal | `evidence_appraisals`, duplicate candidates and decisions | Organization contribution; append-only decisions | Preserve reviewer independence, appraisal framework/version, limitations, and exact evidence revision. |
| Regulatory intelligence | Guidance, versions, observations, poll runs, change events and decisions | Shared source data plus system ingestion and organization review | Keep official source observation separate from interpretation; preserve jurisdiction, effective date, retrieval and source version. |
| Analytical test catalogue | Test catalogue, sources, decisions, reference frameworks and crosswalks | Shared reference catalogue plus governed revisions | Applicability is material/purpose-specific; a catalogue entry or vendor claim is not proof of validated capability. |
| Peptide-test applicability | `peptide_test_applicability`, applicability decisions | Organization contribution plus curated-public promotion | Record chemical form, method revision, intended purpose, source, reviewer and limitations. |
| Platform security | Rate-limit buckets, audit events and chain heads, maintenance markers | System operational; append-only audit | Restrict service ownership, preserve tenant context, prevent destructive mutation, and independently anchor hashes where required. |

## Cross-cutting invariants

1. Every organization-owned parent stores a non-null immutable `owner_organization_id`; never infer ownership from a user's current organization membership.
2. Every child of an organization-owned parent inherits access through that parent and cannot be attached to a different tenant's parent.
3. Shared scientific master records are not assigned arbitrary tenant ownership. Contributions retain submitter/origin metadata even after public promotion.
4. Verification status and publication visibility are independent. A verified organization-private record remains private.
5. Decisions reference the exact immutable revision they reviewed. A later edit must not silently inherit an earlier approval.
6. Machine-extracted, predicted, vendor-asserted, and experimentally measured data remain distinguishable.
7. Every scientific assertion can be traced to a source version and, where permitted, a stable locator (DOI/PMID, page, figure, table, section, or accession).
8. Background jobs use explicit system/service identity and cannot inherit a request user's tenant context.
9. Tenant isolation must cover direct-ID access, list/search, nested resources, exports, agent context, and background jobs.
10. RLS rollout requires transaction-local context, connection-pool reset tests, service-role review, and explicit public-master policies. Do not enable RLS by blanket policy without these tests.

## Known gaps / not yet proven

- Migrations 044–063 now enable RLS across vendor materials, analytical methods, formulations, process knowledge, molecular interactions, evidence appraisal, curation workflows, agent sessions, regulatory guidance and scheduler records, vendor identity and services, laboratory capability claims, peptide applicability, analytical test-catalogue decisions, audit events, extraction artifacts and enrichment artifacts. Regulatory feed registrations now have organization RLS plus a dedicated column-limited scheduler role. The shared scientific `source_records` registry is intentionally global. Remaining tenant-owned tables, routes and background workers still require table-by-table verification.
- The audit does not prove every organization contribution and child table has a complete owner key or that every router has negative cross-tenant tests.
- The audit does not establish live PostgreSQL schema parity, production role permissions, query plans, backup/restore, monitoring, TLS, or secret management.
- Canonical peptide identity has a chemical-form foundation, but a complete deterministic identity fingerprint and collision-tested normalization for D-residues, noncanonical residues, terminal chemistry, cyclization, conjugates, salts, and aliases is not yet established.
- Scientific parent-record revision/supersession is not universal; decisions must be bound to exact revisions before broad ingestion.
- The inventory groups related child tables where exact ownership inheritance must be confirmed from migrations and routes. It is not a claim that all named groups have already passed table-by-table verification.

## Required validation before expanding data ingestion

- Produce a table-by-table schema inventory from the live migration chain and compare it with deployed PostgreSQL.
- Build an ownership matrix from actual columns, foreign keys, route predicates, and background-worker access.
- Add negative cross-tenant tests for every organization-owned parent and nested child, including guessed UUID access.
- Verify clean-install and upgrade migration paths on supported PostgreSQL versions.
- Test duplicate external identifiers, invalid state transitions, orphan prevention, and cross-organization foreign-key references.
- Define peptide identity fixtures before adding a uniqueness constraint or importing large catalogues.
- Keep AI outputs as cited, unreviewed candidates until an authorized independent reviewer accepts a specific revision.

## Decision

The next implementation sequence should prioritize ownership and identity contracts, then revision/provenance, then ingestion breadth and AI write workflows. The existence of a domain table is not evidence that its data is complete, validated, public, or production-ready.

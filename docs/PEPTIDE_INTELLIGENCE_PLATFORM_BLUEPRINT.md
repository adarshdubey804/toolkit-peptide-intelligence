# Peptide Intelligence Platform — Product and Technical Blueprint

**Status:** Approved architectural direction; implementation roadmap, not a claim that the capabilities below are already deployed.

## 1. Product objective

Build a continuously maintained, evidence-first peptide intelligence platform that provides a unified scientific dossier for each peptide or chemically distinct peptide form. The platform must cover:

- FDA-approved peptide drug products and their exact approved labels, indications, routes, dosage forms, approval history, and jurisdiction.
- Peptides that are not FDA-approved, including investigational, preclinical, discontinued, withdrawn, rejected, and research-only candidates.
- Peptide candidates proposed for future development, but only when traceable literature, patents, target biology, unmet need, or other documented rationale exists.
- Identity, sequence, stereochemistry, chemical modifications, structure, physicochemical properties, targets, mechanisms, pharmacology, clinical and preclinical evidence, safety signals, regulatory history, analytical characterization, formulation/stability evidence, manufacturing/process-development literature, suppliers and facilities, and source provenance.
- A continuously refreshed global research and regulatory update stream.
- AI research agents and computational workbenches for evidence synthesis, peptide comparison, interaction hypotheses, combination/synergy analysis, and safety-signal exploration.

The platform is an evidence and research intelligence system. It is not a clinical decision-support system, a patient-specific treatment recommender, or an automated authority for regulatory or manufacturing decisions.

## 2. Core scientific and regulatory rules

### 2.1 Approval is a product-, indication-, and jurisdiction-specific fact

Do not store a single unqualified boolean such as `is_fda_approved` on a peptide identity. Regulatory authorization attaches to a particular product/chemical form, sponsor/holder, formulation, route, indication, label and jurisdiction at a point in time.

Represent at least:
- jurisdiction and authority;
- application / authorization identifier and pathway where available;
- exact product and active ingredient / chemical form;
- sponsor or marketing authorization holder;
- indication, population, route and dosage form as stated by the source;
- original approval, supplemental approvals, current status, withdrawal/discontinuation dates and reasons when officially documented;
- label/document version, source URL, retrieval time and effective date;
- evidence status: official source, secondary source, unresolved mapping, or curator-reviewed.

“Not FDA-approved” must not be inferred from absence in one search. Use explicit states such as `not_found_in_checked_sources`, `investigational`, `not_approved_in_jurisdiction` (only with adequate evidence), `withdrawn`, `discontinued`, `rejected`, and `unknown`. Preserve country differences. A medicine approved by EMA, MHRA, CDSCO or another authority is not thereby FDA-approved.

### 2.2 Evidence classes must never be collapsed

Every scientific value and claim must identify its origin and evidence class:
- measured experimental result;
- human clinical observation or trial result;
- animal / in-vivo preclinical result;
- in-vitro / ex-vivo result;
- computational prediction or simulation;
- source-reported assertion;
- AI-extracted candidate claim;
- curator interpretation.

Retain study design, organism/population, sample size where reported, comparator, endpoint, assay/model, conditions, result, uncertainty, limitations, source locator, and conflicts. A publication, trial registration, patent, vendor claim, or AI summary is not itself proof of efficacy, safety, approval, purity, or validated capability.

### 2.3 Predictions are hypotheses, not proven outcomes

Combination synergy, target interaction, efficacy, toxicity and future ADR models must display model type, training/evaluation domain, assumptions, calibration, uncertainty, applicability domain and known limitations. Do not present a predicted interaction or ADR as experimentally or clinically confirmed. Do not provide patient-specific combination recommendations, dosing, or instructions for self-administration.

## 3. The peptide dossier: one-click access

Each canonical peptide identity should have a stable dossier route, with chemically distinct forms and product presentations represented as linked but non-interchangeable entities.

Suggested dossier sections:
1. Overview and identity confidence
2. Regulatory status by jurisdiction and exact product
3. Sequence, residue encoding, stereochemistry and modifications
4. Chemical forms, salts, conjugates, cyclization and identity fingerprints
5. Structure and computational/experimental structural evidence
6. Targets, mechanisms and pathway context
7. Pharmacology and PK/PD evidence
8. Human clinical trials and publications
9. Preclinical and in-vitro evidence
10. Safety / ADR evidence and signal history
11. Combination research and interaction hypotheses
12. Analytical testing, method applicability and validation evidence
13. Formulation, delivery and stability evidence
14. Process-development and manufacturing literature (non-operational evidence catalogue)
15. Vendors, facilities, certificates, materials and batch traceability
16. Patent and future-development landscape
17. Global research updates and timeline
18. Complete source register, review decisions, revisions and audit history

The user-facing interface should load a concise dossier summary quickly, with expandable sections and direct links to original sources. Use a relational database and stable peptide IDs as the source of truth; do not create one physical database table or manually maintained filesystem directory per peptide. Provide a virtual per-peptide folder/dossier view. Store large source documents and derived artifacts in object storage using a predictable path such as `/peptides/{peptide_id}/{artifact_type}/{source_record_id}/{version}`, while metadata and permissions remain in PostgreSQL. A dossier must be accessible from catalogue search in one click.

## 4. Regulatory and development lifecycle taxonomy

Use separate dimensions rather than one overloaded development-status field.

### Regulatory status (per product and jurisdiction)
- approved;
- conditionally / emergency authorized (where the authority uses that category);
- under review;
- refused / rejected;
- authorization withdrawn;
- discontinued / no longer marketed;
- not found in checked official sources;
- unknown / unresolved.

### Research / development stage (per candidate)
- discovery / design;
- computationally proposed;
- in-vitro research;
- in-vivo preclinical;
- IND/CTA-enabling (source-supported);
- clinical phase I, II, III;
- filed / under regulatory review;
- marketed in at least one jurisdiction;
- paused / suspended;
- terminated / discontinued;
- stage unknown.

These states are not interchangeable. A peptide can be approved in one country and investigational in another. A research candidate is not “future-ready” merely because an AI agent generated it.

## 5. Global daily intelligence and automatic ingestion

### 5.1 Source families

Build source adapters with source-specific terms of use, API limits, licensing, identifiers and update semantics. Prioritize official or primary sources:

- Regulatory: FDA Drugs@FDA, FDA labels / DailyMed, FDA safety communications and relevant official databases; EMA, MHRA, CDSCO, WHO and other national authority sources where machine-readable access is available.
- Trials: ClinicalTrials.gov and other official trial registries with documented APIs.
- Literature: PubMed / NCBI, Europe PMC and publisher metadata feeds where permitted.
- Chemistry and identity: PubChem, UniProt and authoritative sequence/structure resources, with identity resolution review.
- Structure: RCSB PDB and AlphaFold DB, preserving experimental versus predicted status.
- Patents: official patent-office / WIPO sources and licensed metadata providers.
- Safety: official regulatory safety notices, label changes and public pharmacovigilance sources with denominator and reporting-bias caveats.
- Research signals: preprints and other secondary sources clearly labelled as non-peer-reviewed.

The list is extensible. Source availability, licensing, API terms and actual update frequency must be checked before each integration is enabled.

### 5.2 Daily update pipeline

Implement a scheduled, resumable, idempotent pipeline:
1. Discover changed/new source records using official APIs, feeds, cursors, ETags, modified dates or source-specific incremental methods.
2. Persist raw retrieval metadata and payload or permitted archival representation before transformation.
3. Compute content hashes and immutable source versions; never overwrite prior source payloads.
4. Normalize identifiers, dates, organizations, products, peptide aliases and source links.
5. Resolve candidate entity matches with method, confidence and evidence; uncertain matches go to a review queue.
6. Extract structured claims with model/version and extraction provenance.
7. Validate schemas, required fields, identifiers, date logic, source domain, content hash, duplicate keys, foreign keys, tenant scope and state transitions.
8. Run scientific consistency checks and compare changes with existing claims, including contradictions and retractions.
9. Auto-publish only low-risk, deterministic metadata from allowlisted authoritative sources under explicit rules. Keep scientific interpretations, safety conclusions, regulatory mappings and uncertain identity matches in a review queue.
10. Update search indexes, dossier caches and the global update feed only after validation and policy checks.
11. Record every run, source cursor, counts, errors, retries, rejected rows, review backlog and last-success timestamp.
12. Alert operators when a source fails, schema changes, ingestion falls behind, or an unusual change is detected.

“Without manual requirement” means routine discovery, retrieval, deduplication, deterministic validation, versioning, indexing and dashboard refresh are automated. It does not mean bypassing scientific review for ambiguous or high-impact claims. No system can guarantee that every global publication or regulatory change is discovered immediately; show source coverage and last-checked times.

### 5.3 Reliability requirements

- Per-source schedules and rate limits; no single global cron that can silently fail.
- Idempotency keys and replay-safe processing.
- Retry with backoff, dead-letter handling and operator-visible failures.
- Per-source watermarks/cursors and gap detection.
- Monitoring for source schema changes, broken feeds and stale data.
- Immutable run logs and audit events.
- Reconciliation jobs to detect missing or changed upstream records.
- Tests for duplicate deliveries, interrupted runs, replay, out-of-order updates and partial failures.
- Secrets stored in deployment secret management, never committed to the repository.
- A manual pause / kill switch for a misbehaving source or pipeline.

## 6. AI agent architecture

Agents should be specialized, tool-limited and evidence-grounded. Each agent run stores the question, peptide/form IDs, retrieved source IDs and versions, tool calls, model/provider/version, prompt/template version, output, uncertainty, validation result and review state.

Proposed agents:
- Regulatory & Label Agent: tracks official approval, label, jurisdiction and status changes.
- Literature Surveillance Agent: daily new publications, trials, preprints and retractions.
- Peptide Identity Agent: alias and chemical-form resolution; uncertain matches remain candidates.
- Sequence / Structure Agent: sequence, structure, modifications and model-confidence interpretation.
- Mechanism & Target Agent: maps targets and pathways while separating association from causality.
- Clinical Evidence Agent: extracts trial design, populations, endpoints, results and limitations.
- Safety / ADR Agent: organizes reported events and official safety actions; does not infer incidence from spontaneous reports without suitable denominators.
- Combination Research Agent: evaluates mechanistic rationale and available combination evidence.
- Synergy Modelling Agent: runs pre-registered, reproducible analyses when compatible experimental data exist.
- Analytical / Quality Agent: maps identity, purity, impurities, assay and method-validation evidence.
- Formulation / Stability Evidence Agent: indexes published evidence and conditions.
- Vendor / Facility Evidence Agent: verifies source-linked claims and certificate scope.
- Scientific Review Agent: checks evidence completeness, contradictions, unsupported claims and source quality.
- Daily Briefing Agent: produces a concise, cited digest of validated new and changed records.

Agents must not self-approve, self-publish high-impact claims, alter source evidence, or silently overwrite curated records. All writes are drafts with provenance and validation state.

## 7. Combination and synergy computation

The platform should support a research-grade combination workbench, not an unqualified “synergy calculator”.

### Required inputs
- exact peptide chemical-form identity and batch/material context where relevant;
- each component's experimental concentration or exposure range and units;
- compatible assay, biological system, endpoint, time point and experimental design;
- single-agent dose-response curves and combination response matrix;
- replicate count, controls, normalization and uncertainty;
- source dataset / publication and provenance.

### Analysis methods
Support only methods whose assumptions fit the experiment, potentially including:
- Bliss independence;
- Loewe additivity / isobolographic analysis;
- Highest Single Agent (HSA);
- ZIP response-surface analysis;
- dose-response and response-surface models with confidence intervals / bootstrap uncertainty.

Do not treat different synergy models as interchangeable. Report each method's assumptions, fitted parameters, goodness-of-fit, uncertainty, sensitivity and applicability. Require compatible single-agent and combination measurements. If only literature rationale or docking evidence exists, return a mechanistic hypothesis, not a numerical synergy score. If data are insufficient, abstain.

For three or more components, account for combinatorial explosion, sparse designs, interaction terms, multiplicity and overfitting. Do not extrapolate beyond tested concentration ranges without an explicit warning and validated model.

### ADR and safety exploration for combinations

Build a separate safety evidence graph and prediction module:
- observed adverse events from trials, labels and published studies;
- official safety communications and label changes;
- preclinical toxicity and mechanistic evidence;
- known class effects and target/pathway overlap;
- pharmacokinetic / pharmacodynamic interaction evidence where available;
- spontaneous-report signals only with explicit reporting-system bias, confounding and lack of exposure denominators.

A predicted future ADR must be labelled `hypothesis` or `model_prediction`, with evidence links, rationale, confidence/uncertainty, model version, applicability domain and required validation experiments. Do not state that an ADR “will occur”. Do not calculate patient-specific risk or recommend a peptide combination for use.

## 8. Data architecture principles

Use normalized PostgreSQL entities with immutable histories and materialized read models for fast dossier display. Key entity groups:
- peptide identities and aliases;
- peptide sequences and chemical forms;
- products / presentations and jurisdiction-specific regulatory authorizations;
- development programs and lifecycle events;
- source records and immutable source versions;
- publications, trials, patents and regulatory documents;
- evidence claims, claim-source locators, appraisals and decisions;
- targets, pathways, structures and interaction evidence;
- ADR / safety observations and safety actions;
- combination experiments, response matrices, synergy analyses and model runs;
- formulation, stability, process and analytical method evidence;
- vendors, facilities, certifications, materials and batches;
- ingestion sources, schedules, cursors, runs, artifacts and validation findings;
- agent definitions, runs, tool events, drafts and approvals;
- global update feed events and dossier index/cache metadata.

All records must have stable identifiers, explicit ownership/visibility, source provenance, created/updated timestamps, version semantics and audit coverage appropriate to their data class. Decisions must bind to immutable revisions. Preserve original units and source values alongside normalized values; never silently convert or replace the source observation.

## 9. Fast, uncluttered user experience

- Global search by peptide name, alias, sequence, product, target, trial, publication or regulatory identifier.
- Search result opens the dossier directly.
- Dossier overview shows identity, regulatory status by jurisdiction, development stage, evidence summary, safety notices and last successful update.
- Tabs / sections keep content organized; filters distinguish approved, investigational, preclinical, withdrawn, unknown and future-development candidates.
- “Latest global updates” feed with date, source, peptide, update type, evidence class, review state and direct dossier link.
- Clearly distinguish new, changed, under review, validated metadata, curator verified, prediction and conflicting evidence.
- Load summary and cached high-value facts first; lazy-load heavy publications, structures and analysis artifacts.
- Each visible claim should open its source locator and show when it was retrieved and reviewed.
- Show data gaps explicitly rather than rendering empty values as facts.

## 10. Implementation roadmap and release gates

### Phase 0 — Architecture and acceptance contracts
- Freeze entity boundaries, approval taxonomy, evidence classes, update states, ownership and agent governance.
- Map existing schema/routes/integrations to target entities and identify reuse versus gaps.
- Define representative test fixtures and end-to-end acceptance criteria.

### Phase 1 — Regulatory product truth
- Model product-level authorization by jurisdiction, label and immutable status history.
- Integrate official FDA sources first; then add other authorities through source adapters.
- Build the regulatory timeline and reviewable mapping to peptide chemical forms.

### Phase 2 — Per-peptide dossier and global search
- Complete dossier API/read model and one-click profile navigation.
- Build sections, evidence links, source timeline and data completeness indicators.

### Phase 3 — Automated research surveillance
- Add scheduled source connectors, incremental sync, validation, immutable versions, retries, monitoring and update feed.
- Begin with PubMed, ClinicalTrials.gov and official FDA updates; expand only after source-specific tests and licensing review.

### Phase 4 — Safety and evidence intelligence
- Normalize clinical/preclinical safety observations, ADR terminology, label changes and signal limitations.
- Build contradiction/retraction handling and evidence-quality review.

### Phase 5 — Combination and synergy workbench
- Add experiment schema and validated statistical methods.
- Test against published benchmark datasets and synthetic fixtures with known behavior.
- Require input compatibility checks, uncertainty reporting and abstention.

### Phase 6 — AI agent orchestration
- Implement specialized agents, source-retrieval allowlists, tool permissions, reproducible run logs and draft-only writes.
- Add semantic support review beyond simple citation-ID matching.

### Phase 7 — Scale and operational hardening
- Load testing, indexing, caching, observability, backup/restore drills, source coverage dashboards, security review and deployment validation.

### Release gates
No phase is complete merely because tables or UI pages exist. Require migration tests, API tests, frontend build, source adapter fixtures, security/tenant tests, provenance tests and documented limitations. Production ingestion additionally requires configured credentials/secrets, deployed scheduler/worker, monitoring, alerting, backup/restore validation and verified source terms.

## 11. Initial measurable acceptance criteria

- Regulatory status cannot be displayed without authority, jurisdiction, exact product/form mapping, source and last-checked timestamp.
- A missing FDA match never automatically becomes a confirmed “not approved” claim.
- Every imported source has immutable version history and reproducible retrieval metadata.
- A replayed ingestion event creates no duplicate source or claim.
- Invalid, conflicting or ambiguous records are quarantined without corrupting curated data.
- Dossier pages expose source links, evidence class, review state and last-updated time.
- Every AI output is reproducible from a stored run manifest and supplied source versions.
- A synergy score is unavailable when required single-agent / combination data or compatible assay context is missing.
- A model prediction is always visibly distinguished from experimental or clinical evidence.
- High-impact regulatory, clinical and safety claims cannot be auto-published solely by an LLM.
- Scheduled ingestion failures are observable and recoverable; the system exposes last successful run per source.
- Cross-tenant data remains isolated across API, search, dossier, agent and background-worker paths.

## 12. Existing repository baseline and known gaps

The repository already contains useful foundations: PostgreSQL migrations through 065; peptide identity and chemical-form records; immutable revisions for chemical forms and evidence claims; source provenance; PubMed, ClinicalTrials.gov, UniProt, RCSB and PubChem discovery clients; regulatory guidance and polling infrastructure; evidence extraction/review; analytical, formulation, process, vendor and interaction modules; agent sessions and specialized research agents; and a Next.js peptide catalogue/profile.

These foundations do not yet establish the full product described here. In particular:
- the peptide sequence canonicalizer intentionally supports only unmodified standard linear sequences;
- regulatory guidance/polling infrastructure is not yet a complete product-level authorization and FDA-label history system;
- the existing discovery integrations are not equivalent to a production daily ingestion service with monitored schedules and complete source coverage;
- current peptide directory/profile shows curator-verified records, not a complete global peptide landscape;
- the AI synthesis citation audit checks identifier presence, not semantic claim support;
- no validated multi-peptide synergy analysis or prospective ADR prediction system is established by this blueprint;
- no guarantee of complete worldwide coverage or real-time discovery should be made.

**Architecture decision:** Build the platform as an evidence-first, source-versioned, multi-jurisdictional peptide knowledge system with automated ingestion and controlled scientific publication. Expand breadth only after identity, provenance, validation, safety and ownership guarantees are testable.

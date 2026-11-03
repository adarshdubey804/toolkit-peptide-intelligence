# Global peptide catalogue and dossier identity model

## Goal

Build the broadest practical, globally sourced peptide knowledge catalogue. It must cover approved products, investigational and preclinical candidates, endogenous peptides, research peptides, peptide antibiotics/toxins, conjugates and peptide fragments without implying that any single public database is complete.

## Canonical peptide dossier versus discovery observation

- A **canonical peptide** is a curated identity in `peptides`. Its stable UUID is the dossier key and its profile route is `/peptides/{peptide_id}`.
- A **discovery candidate** is a source-specific observation in `peptide_discovery_candidates`. It may be a new peptide, an alias, a product/formulation, a fragment, a duplicate, a non-peptide, or an ambiguous name match.
- Every candidate preserves its source record, source entity identifier, URL, raw metadata, reported sequence/form, source-reported lifecycle text, and source-specific mechanism hint.
- Candidate observations are append-only and content-addressed. Curation decisions are append-only. A candidate is never silently promoted into a verified canonical peptide.
- Identity resolution must consider sequence, stereochemistry, noncanonical residues, terminal chemistry, cyclization, conjugation and exact chemical form. Name matching alone is insufficient.

## Lifecycle and regulatory separation

Source-reported development status is retained as source-specific text. Regulatory approval remains a separate product-, form-, indication-, authority- and jurisdiction-specific record in `regulatory_product_authorizations`. A candidate's source status must never set a global FDA-approved flag. No result from a bounded source search is proof of worldwide absence.

## Candidate classification

Supported broad kinds include therapeutic peptides, endogenous peptides, peptide conjugates, fragments, peptide hormones, research peptides, peptide antibiotics, peptide toxins, other and unknown. These categories are indexing aids, not mutually exclusive biological ontologies.

## Source acquisition strategy

Build modular adapters and record source timestamps, source version, query scope, identifier, URL and payload hash. Prioritize:
1. Official regulator labels and authorization sources by jurisdiction (FDA Drugs@FDA, DailyMed, FDA Purple Book; EMA, MHRA, Health Canada, TGA, PMDA and other national authorities).
2. Clinical development registries (ClinicalTrials.gov and national/regional registries).
3. Curated protein/peptide sequence and chemistry resources (UniProt, reviewed peptide-specific resources, PubChem, ChEMBL and structural databases).
4. Primary literature (PubMed and publisher/DOI metadata), patents and public research repositories.
5. Commercial catalogues only as leads; vendor listings do not establish identity, quality, regulatory status or human use.

Each adapter must disclose coverage, query/date window, licensing and known omissions. Avoid scraping where terms or API policies do not permit it.

## Dossier folder experience

Each canonical peptide has one stable virtual dossier folder keyed by UUID. It should be opened from a single catalogue row/card and provide clear sections:
- Overview and identity
- Aliases and sequence
- Chemical forms and structures
- Regulatory products and jurisdictional status
- Mechanism of action
- Targets and pathways
- Pharmacology and pharmacokinetics
- Clinical and preclinical studies
- Safety and adverse-event evidence
- Formulation and stability
- Analytical methods and testing
- Process-development knowledge
- Vendors and facilities
- Publications, patents and source history
- Change log and curator review

A section with no curated data must say "not yet curated" or "not found in checked sources", not imply that the property does not exist.

## Quality controls

- Deduplicate source observations by source identity and payload hash, not fuzzy name alone.
- Never merge chemical entities automatically from name similarity.
- Keep original source payload and a normalized projection.
- Make ingestion idempotent; retries must not create duplicate candidates or observations.
- Record every material source change and every curator decision.
- Keep public/curator visibility controls; private draft submissions are not exposed in public search.
- Require human review for canonical identity merges, high-impact regulatory assertions and mechanism claims.
- Report source coverage and freshness. Do not claim "all peptides in the world" as a completed state; describe the exact sources, query scopes and last successful retrievals.

## Initial implementation boundary

Migration 068 creates the discovery registry, immutable source observation history and immutable curation decision history. It does not yet claim that global ingestion or full source coverage is running. Source adapters, ingestion schedules, candidate review UI and catalogue search integration are subsequent implementation work.


## First named provisional dossier: BPC-157

Migration 069 seeds a provisional BPC-157 candidate from the FDA's official compounding safety page. It preserves the FDA statement under the exact section “Bulk drug substances nominated but withdrawn”, including the agency's stated immunogenicity and peptide impurity/API-characterization concerns.

The record is deliberately:
- a source-specific US regulatory/compounding observation, not an FDA marketing-authorization record;
- `needs_review` with `identity_match_status=unresolved`;
- missing sequence, stereochemistry and chemical-form fields until independently sourced;
- linked to an immutable normalized source snapshot and discovery observation.

The candidate dossier opens at `/peptide-discovery/{candidate_id}`. It must not be promoted to a canonical peptide or labelled FDA-approved/not-approved from this single compounding page alone. Curators must resolve exact sequence/form and check product-level authorization sources separately.

Official source: https://www.fda.gov/drugs/human-drug-compounding/certain-bulk-drug-substances-use-compounding-may-present-significant-safety-risks


### BPC-157 literature mechanism note

Migration 070 adds PubMed PMID 40005999 (2025 review) as a second source observation on the same BPC-157 candidate dossier. The provisional mechanism hint summarizes proposed NOS interaction, HO-1/antioxidant expression and VEGF-receptor modulation. It is explicitly labelled literature-reported and predominantly preclinical. It is not a curator-verified mechanism, a demonstrated human pathway or evidence of clinical efficacy. The exact review, DOI, PMCID, excerpt, source URL and evidence-scope limitation are retained in the dossier and immutable observation history.

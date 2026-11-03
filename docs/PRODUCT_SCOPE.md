# Product scope

## Product vision

Toolkit Peptide Intelligence is an evidence-first, continuously updated peptide intelligence platform. Its target scope is a unified, one-click scientific dossier for each peptide and chemically distinct form, spanning regulatory authorization by jurisdiction, approved products and labels, investigational and preclinical candidates, future-development research, identity and chemistry, mechanisms and targets, clinical and preclinical evidence, safety / ADR observations, analytical characterization, formulation and stability evidence, process-development literature, vendors and facilities, and complete source provenance.

The platform will provide a global research and regulatory update feed, automated source surveillance and validation, and specialized AI research agents. Computational combination and synergy analysis is a research workbench: it must require suitable experimental inputs, report model assumptions and uncertainty, and never present hypotheses as established efficacy or safety.

See [Peptide Intelligence Platform Blueprint](PEPTIDE_INTELLIGENCE_PLATFORM_BLUEPRINT.md) for the detailed architecture, evidence model, automation workflow, agent governance, synergy requirements, roadmap and release gates.

## Product boundaries

Public MVP: curator-reviewed peptide profiles, scientific references, trial/regulatory links and analytical-method explainers.

Planned expanded platform: product-level regulatory status by jurisdiction, investigational/preclinical candidate landscape, complete peptide dossiers, global update feed, source-versioned daily ingestion, evidence-grounded AI agents, safety intelligence, combination research workbench, saved workspaces, advanced search, private projects and collaboration.

## Evidence and safety boundaries

- Regulatory authorization is specific to product, chemical form, indication, label, authority and jurisdiction; absence from a search is not proof of non-approval.
- Every claim distinguishes measured, clinical, preclinical, computational, source-asserted and AI-extracted evidence.
- Automated ingestion may retrieve, normalize, validate, version and index source data. Ambiguous identity mappings and high-impact clinical, safety and regulatory interpretations require governed review.
- AI predictions, synergy scores and future ADR hypotheses must never be represented as proven outcomes.
- The platform does not provide patient-specific diagnosis or treatment, unapproved peptide dosing, self-administration recommendations, material release decisions or GMP execution instructions.

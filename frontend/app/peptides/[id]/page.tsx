"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type Profile = {
  peptide: { id: string; preferred_name: string; peptide_category?: string | null; description?: string | null; development_status?: string | null; intended_use_class: string };
  aliases: { alias: string }[];
  sequences: { sequence: string; sequence_type: string; modifications: unknown[] }[];
  chemical_properties: { chemical_form?: string; molecular_formula?: string; average_molecular_mass?: number; monoisotopic_mass?: number; property_origin: string; method_or_tool?: string }[];
  chemical_forms: {
    id: string;
    peptide_sequence_id?: string | null;
    form_name: string;
    form_type: string;
    normalized_sequence?: string | null;
    residue_encoding: unknown;
    stereochemistry: unknown;
    noncanonical_residues: unknown;
    terminal_chemistry: unknown;
    post_translational_modifications: unknown;
    cyclization: unknown;
    conjugation: unknown;
    salt_and_counterions: unknown;
    chemical_formula?: string | null;
    average_molecular_mass?: number | null;
    monoisotopic_mass?: number | null;
    canonical_smiles?: string | null;
    inchi?: string | null;
    inchikey?: string | null;
    identity_fingerprint?: string | null;
    canonicalization_method?: string | null;
    canonicalization_version?: string | null;
  }[];
  regulatory_authorizations: {
    id: string;
    chemical_form_name?: string | null;
    product_name?: string | null;
    active_ingredient_name: string;
    application_identifier?: string | null;
    authorization_identifier?: string | null;
    jurisdiction_code: string;
    jurisdiction_name: string;
    authority_name: string;
    regulatory_status: string;
    indication_text?: string | null;
    route_of_administration?: string | null;
    dosage_form?: string | null;
    strength_text?: string | null;
    marketing_authorization_holder?: string | null;
    original_approval_date?: string | null;
    effective_date?: string | null;
    status_end_date?: string | null;
    status_reason?: string | null;
    label_version?: string | null;
    label_url?: string | null;
    source_locator?: string | null;
    source_checked_at: string;
    source_name: string;
    source_url?: string | null;
  }[];
  structures: { structure_type: string; external_identifier?: string; method_or_prediction_tool?: string }[];
  mechanisms_of_action: {
    id: string;
    chemical_form_name?: string | null;
    mechanism_title: string;
    mechanism_statement: string;
    mechanism_class: string;
    target_name?: string | null;
    target_identifier?: string | null;
    target_action?: string | null;
    binding_or_interaction?: string | null;
    downstream_signaling?: string | null;
    pathway_context?: string | null;
    biological_effect?: string | null;
    tissue_or_cell_context?: string | null;
    species_or_population?: string | null;
    evidence_level: string;
    evidence_type: string;
    confidence_score?: number | null;
    limitations?: string | null;
    source_locator?: string | null;
    source_excerpt?: string | null;
    model_or_method?: string | null;
    source_name: string;
    source_url?: string | null;
  }[];
  evidence_claims: { id: string; claim_text: string; claim_domain: string; evidence_type: string; confidence_label: string; limitations?: string; doi?: string; pmid?: string; publication_title?: string; publication_url?: string }[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function Section({ title, children, id }: { title: string; children: React.ReactNode; id?: string }) {
  return <section id={id} className="panel scroll-mt-24 p-5"><h2 className="text-lg font-semibold">{title}</h2><div className="mt-4">{children}</div></section>;
}

export default function PeptideProfilePage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${API_BASE}/api/v1/peptides/${encodeURIComponent(params.id)}`, { signal: controller.signal });
        if (response.status === 404) throw new Error("This peptide profile is not available as a verified public record.");
        if (!response.ok) throw new Error("Unable to retrieve the peptide profile.");
        setProfile(await response.json());
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Unexpected profile error.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, [params.id]);

  if (loading) return <main className="container py-12"><p className="muted">Loading scientific profile…</p></main>;
  if (error || !profile) return <main className="container py-12"><Link href="/peptides" className="text-sm text-emerald-300">← Back to peptide database</Link><div role="alert" className="panel mt-8 p-6 text-sm text-rose-200">{error || "Profile not found."}</div></main>;

  const peptide = profile.peptide;
  return <main className="container min-h-screen py-10">
    <Link href="/peptides" className="text-sm text-emerald-300 hover:text-emerald-200">← Peptide database</Link>
    <header className="mt-9 max-w-4xl"><span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">Curator verified</span><h1 className="mt-4 text-4xl font-semibold md:text-5xl">{peptide.preferred_name}</h1><p className="muted mt-4 leading-7">{peptide.description || "No curated description available."}</p><div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-400">{peptide.peptide_category && <span className="rounded-full border border-slate-700 px-3 py-1">{peptide.peptide_category}</span>}<span className="rounded-full border border-slate-700 px-3 py-1">{peptide.intended_use_class}</span>{peptide.development_status && <span className="rounded-full border border-slate-700 px-3 py-1">{peptide.development_status}</span>}</div></header>
    <nav aria-label="Peptide dossier sections" className="panel mt-6 p-4">
      <p className="text-xs uppercase tracking-[.16em] text-slate-400">Dossier folders</p>
      <div className="mt-3 flex flex-wrap gap-2 text-sm">
        {[
          ["regulatory", "Regulatory status"],
          ["mechanism", "Mechanism of action"],
          ["identity", "Aliases & sequence"],
          ["chemistry", "Chemical forms"],
          ["structure", "Structure"],
          ["evidence", "Evidence"],
        ].map(([id, label]) => <a key={id} href={`#${id}`} className="rounded-full border border-slate-700 px-3 py-2 text-emerald-300 hover:border-emerald-400">{label}</a>)}
      </div>
      <p className="muted mt-3 text-xs">This unique peptide profile is the permanent dossier folder for this record. Sections open directly within the same dossier.</p>
    </nav>
    <Section id="mechanism" title="Mechanism of action">
      {profile.mechanisms_of_action?.length ? <div className="space-y-5">
        {profile.mechanisms_of_action.map((mechanism) => <article key={mechanism.id} className="border-b border-slate-800 pb-5 last:border-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium">{mechanism.mechanism_title}</h3>
            <span className="rounded-full border border-slate-700 px-2 py-1 text-xs">{mechanism.mechanism_class.replaceAll("_", " ")}</span>
            <span className="rounded-full border border-slate-700 px-2 py-1 text-xs">{mechanism.evidence_level.replaceAll("_", " ")}</span>
          </div>
          <p className="mt-3 text-sm leading-6">{mechanism.mechanism_statement}</p>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <dt className="muted">Target</dt><dd>{mechanism.target_name || "Not established"}</dd>
            <dt className="muted">Target action</dt><dd>{mechanism.target_action || "Not reported"}</dd>
            <dt className="muted">Binding / interaction</dt><dd>{mechanism.binding_or_interaction || "Not reported"}</dd>
            <dt className="muted">Downstream signalling</dt><dd>{mechanism.downstream_signaling || "Not reported"}</dd>
            <dt className="muted">Pathway context</dt><dd>{mechanism.pathway_context || "Not reported"}</dd>
            <dt className="muted">Biological effect</dt><dd>{mechanism.biological_effect || "Not reported"}</dd>
            <dt className="muted">Tissue / cell context</dt><dd>{mechanism.tissue_or_cell_context || "Not reported"}</dd>
            <dt className="muted">Species / population</dt><dd>{mechanism.species_or_population || "Not specified"}</dd>
            {mechanism.chemical_form_name && <><dt className="muted">Chemical form</dt><dd>{mechanism.chemical_form_name}</dd></>}
            {mechanism.confidence_score !== null && mechanism.confidence_score !== undefined && <><dt className="muted">Curated confidence score</dt><dd>{mechanism.confidence_score.toFixed(2)}</dd></>}
          </dl>
          {mechanism.limitations && <p className="muted mt-3 text-xs">Limitations: {mechanism.limitations}</p>}
          {mechanism.source_excerpt && <blockquote className="mt-3 border-l-2 border-slate-700 pl-3 text-xs text-slate-300">{mechanism.source_excerpt}</blockquote>}
          <p className="muted mt-3 text-xs">Evidence type: {mechanism.evidence_type.replaceAll("_", " ")} · Source: {mechanism.source_name}{mechanism.source_locator ? ` · ${mechanism.source_locator}` : ""}</p>
          {mechanism.source_url && <a href={mechanism.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-300">Open supporting source ↗</a>}
        </article>)}
      </div> : <p className="muted text-sm">No curator-verified mechanism records are currently available. This means the mechanism has not yet been established in this dossier; it does not mean the peptide has no biological mechanism.</p>\n        <Link href="/enrichment" className="mt-3 inline-block text-sm text-emerald-300 underline">Search source evidence and submit a mechanism for curator review →</Link>}
      <p className="muted mt-4 text-xs">Evidence levels are shown separately. Computational, AI-extracted, animal and in-vitro mechanisms are not presented as established human mechanisms or proof of clinical benefit.</p>
    </Section>
    <div className="mt-8 grid gap-4 lg:grid-cols-2">
      <Section id="identity" title="Aliases">{profile.aliases.length ? <ul className="flex flex-wrap gap-2">{profile.aliases.map((item) => <li key={item.alias} className="rounded-full border border-slate-700 px-3 py-1 text-sm">{item.alias}</li>)}</ul> : <p className="muted text-sm">No reviewed aliases recorded.</p>}</Section>
      <Section title="Sequence and modifications">{profile.sequences.length ? profile.sequences.map((item,index)=><div key={index} className="mb-3"><p className="text-xs text-slate-400">{item.sequence_type}</p><p className="mt-1 break-all font-mono text-sm">{item.sequence}</p><p className="muted mt-1 text-xs">Modifications: {item.modifications?.length ? JSON.stringify(item.modifications) : "None recorded"}</p></div>) : <p className="muted text-sm">No reviewed sequence data.</p>}</Section>
      <Section id="chemistry" title="Reviewed chemical forms">
        {profile.chemical_forms?.length ? <div className="space-y-5">
          {profile.chemical_forms.map((form) => <article key={form.id} className="border-b border-slate-800 pb-4 last:border-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-medium">{form.form_name}</h3>
              <span className="rounded-full border border-slate-700 px-2 py-1 text-xs text-slate-300">{form.form_type.replaceAll("_", " ")}</span>
            </div>
            {form.normalized_sequence && <p className="mt-3 break-all font-mono text-sm">{form.normalized_sequence}</p>}
            <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <dt className="muted">Chemical formula</dt><dd>{form.chemical_formula || "Not reported"}</dd>
              <dt className="muted">Average mass</dt><dd>{form.average_molecular_mass ?? "Not reported"}</dd>
              <dt className="muted">Monoisotopic mass</dt><dd>{form.monoisotopic_mass ?? "Not reported"}</dd>
              <dt className="muted">InChIKey</dt><dd className="break-all font-mono text-xs">{form.inchikey || "Not reported"}</dd>
              <dt className="muted">Canonicalization</dt><dd>{form.canonicalization_method ? `${form.canonicalization_method} · v${form.canonicalization_version || "unspecified"}` : "Not canonicalized"}</dd>
            </dl>
            <details className="mt-3 text-xs">
              <summary className="cursor-pointer text-emerald-300">Chemical-form annotations</summary>
              <div className="mt-3 grid gap-3">
                {([
                  ["Residue encoding", form.residue_encoding],
                  ["Stereochemistry", form.stereochemistry],
                  ["Noncanonical residues", form.noncanonical_residues],
                  ["Terminal chemistry", form.terminal_chemistry],
                  ["Post-translational modifications", form.post_translational_modifications],
                  ["Cyclization", form.cyclization],
                  ["Conjugation", form.conjugation],
                  ["Salts and counterions", form.salt_and_counterions],
                ] as [string, unknown][]).map(([label, value]) => <div key={label}>
                  <p className="muted">{label}</p>
                  <pre className="mt-1 whitespace-pre-wrap break-words text-slate-300">{JSON.stringify(value, null, 2)}</pre>
                </div>)}
              </div>
            </details>
          </article>)}
          <p className="muted text-xs">Fingerprints and canonicalization labels are technical identifiers only. They do not independently establish chemical equivalence between materials.</p>
        </div> : <p className="muted text-sm">No curator-verified chemical forms are currently recorded.</p>}
      </Section>
      <Section title="Chemical properties">{profile.chemical_properties.length ? profile.chemical_properties.map((item,index)=><dl key={index} className="grid grid-cols-2 gap-3 text-sm"><dt className="muted">Chemical form</dt><dd>{item.chemical_form || "Not reported"}</dd><dt className="muted">Formula</dt><dd>{item.molecular_formula || "Not reported"}</dd><dt className="muted">Average mass</dt><dd>{item.average_molecular_mass ?? "Not reported"}</dd><dt className="muted">Monoisotopic mass</dt><dd>{item.monoisotopic_mass ?? "Not reported"}</dd><dt className="muted">Origin</dt><dd>{item.property_origin}</dd><dt className="muted">Method/tool</dt><dd>{item.method_or_tool || "Not reported"}</dd></dl>) : <p className="muted text-sm">No reviewed chemical properties.</p>}</Section>
      <Section id="structure" title="Structure references">{profile.structures.length ? profile.structures.map((item,index)=><div key={index} className="mb-2 text-sm"><p>{item.structure_type}</p><p className="muted text-xs">{item.external_identifier || "No external identifier"} · {item.method_or_prediction_tool || "Method not reported"}</p></div>) : <p className="muted text-sm">No reviewed structure records.</p>}</Section>
    </div>
    <Section id="regulatory" title="Regulatory authorizations">
      {profile.regulatory_authorizations?.length ? <div className="space-y-5">
        {profile.regulatory_authorizations.map((item) => <article key={item.id} className="border-b border-slate-800 pb-5 last:border-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium">{item.product_name || item.active_ingredient_name}</h3>
            <span className="rounded-full border border-slate-700 px-2 py-1 text-xs">{item.regulatory_status.replaceAll("_", " ")}</span>
            <span className="rounded-full border border-slate-700 px-2 py-1 text-xs">{item.jurisdiction_code}</span>
          </div>
          <p className="muted mt-2 text-xs">{item.authority_name} · {item.jurisdiction_name}</p>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <dt className="muted">Active ingredient</dt><dd>{item.active_ingredient_name}</dd>
            <dt className="muted">Chemical form</dt><dd>{item.chemical_form_name || "Not specified"}</dd>
            <dt className="muted">Application ID</dt><dd>{item.application_identifier || "Not reported"}</dd>
            <dt className="muted">Authorization ID</dt><dd>{item.authorization_identifier || "Not reported"}</dd>
            <dt className="muted">Dosage form / route</dt><dd>{[item.dosage_form, item.route_of_administration].filter(Boolean).join(" · ") || "Not reported"}</dd>
            <dt className="muted">Strength</dt><dd>{item.strength_text || "Not reported"}</dd>
            <dt className="muted">Indication</dt><dd>{item.indication_text || "Not reported"}</dd>
            <dt className="muted">Authorization holder</dt><dd>{item.marketing_authorization_holder || "Not reported"}</dd>
            <dt className="muted">Original approval</dt><dd>{item.original_approval_date || "Not reported"}</dd>
            <dt className="muted">Effective / end date</dt><dd>{[item.effective_date, item.status_end_date].filter(Boolean).join(" – ") || "Not reported"}</dd>
            <dt className="muted">Label version</dt><dd>{item.label_version || "Not reported"}</dd>
          </dl>
          {item.status_reason && <p className="muted mt-3 text-xs">Status note: {item.status_reason}</p>}
          <p className="muted mt-3 text-xs">Source checked: {new Date(item.source_checked_at).toLocaleDateString()} · {item.source_name}{item.source_locator ? ` · ${item.source_locator}` : ""}</p>
          {item.label_url && <a href={item.label_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-300">Open product label ↗</a>}
          {item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer" className="ml-4 mt-2 inline-block text-xs text-emerald-300">Open source record ↗</a>}
        </article>)}
      </div> : <p className="muted text-sm">No curator-verified product authorization records are currently linked. This does not establish non-approval; only the documented source checks and exact product records can support a regulatory conclusion.</p>}
      <p className="muted mt-4 text-xs">Regulatory status is product-, jurisdiction-, authority- and time-specific. An authorization in one country does not imply authorization in another. An empty section is not proof of non-approval.</p>
    </Section>
    <Section id="evidence" title="Evidence claims">
      {profile.evidence_claims.length ? <div className="space-y-4">{profile.evidence_claims.map((claim)=><article key={claim.id} className="border-b border-slate-800 pb-4 last:border-0"><div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-wide text-emerald-300"><span>{claim.evidence_type}</span><span>·</span><span>{claim.claim_domain}</span></div><p className="mt-2 text-sm leading-6">{claim.claim_text}</p><p className="muted mt-2 text-xs">Confidence: {claim.confidence_label}. {claim.limitations || "No limitations statement supplied."}</p>{claim.publication_url && <a href={claim.publication_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-300">{claim.publication_title || "Source publication"} ↗</a>}</article>)}</div> : <p className="muted text-sm">No reviewed evidence claims are currently linked to this profile.</p>}
    </Section>
    <p className="muted mt-8 text-xs">A curator-verified record is not a clinical recommendation, proof of efficacy, or confirmation of regulatory approval. Evidence must be interpreted in its original study context.</p>
  </main>;
}

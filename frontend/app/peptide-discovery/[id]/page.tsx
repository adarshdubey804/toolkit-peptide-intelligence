"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getAccessToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type DiscoveryDossier = {
  candidate: {
    id: string;
    source_record_id: string;
    candidate_name: string;
    candidate_kind: string;
    source_development_status?: string | null;
    source_jurisdiction_code?: string | null;
    reported_sequence?: string | null;
    reported_sequence_type?: string | null;
    reported_chemical_form?: string | null;
    reported_target?: string | null;
    reported_mechanism?: string | null;
    identity_match_status: string;
    match_confidence?: number | null;
    match_rationale?: string | null;
    candidate_status: string;
    canonical_peptide_id?: string | null;
    canonical_peptide_name?: string | null;
    first_seen_at: string;
    last_seen_at: string;
    last_observed_at: string;
    raw_metadata: Record<string, unknown>;
    source_name: string;
    source_identifier: string;
    source_url: string;
    source_retrieved_at?: string | null;
    license_notes?: string | null;
  };
  observations: {
    id: string;
    source_version?: string | null;
    payload_hash: string;
    observed_at: string;
    payload: Record<string, unknown>;
  }[];
  decisions: {
    id: string;
    decision: string;
    canonical_peptide_id?: string | null;
    rationale: string;
    decided_at: string;
    reviewer_name?: string | null;
  }[];
  permissions: { can_review: boolean };
  dossier_notice: string;
};

type JsonRecord = Record<string, unknown>;
type SavedDossierSection = { section_key: string; citations: JsonRecord[]; media: JsonRecord[]; revision: number };
function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? value as JsonRecord : {};
}
function asRecords(value: unknown): JsonRecord[] {
  return Array.isArray(value) ? value.filter(x => x && typeof x === "object" && !Array.isArray(x)) as JsonRecord[] : [];
}
function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not reported";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  const object = asRecord(value);
  return typeof object.name === "string" ? object.name : JSON.stringify(value) ?? String(value);
}

export default function DiscoveryCandidateDossierPage() {
  const params = useParams<{ id: string }>();
  const [token, setToken] = useState("");
  const [data, setData] = useState<DiscoveryDossier | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [decision, setDecision] = useState("needs_more_evidence");
  const [canonicalPeptideId, setCanonicalPeptideId] = useState("");
  const [rationale, setRationale] = useState("");
  const [savedSections, setSavedSections] = useState<SavedDossierSection[]>([]);

  const loadDossier = useCallback(async (authToken: string) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        API_BASE + "/api/v1/enrichment/discovery-candidates/" + encodeURIComponent(params.id),
        { headers: { Authorization: "Bearer " + authToken } },
      );
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Could not load this candidate dossier.");
      setData(result as DiscoveryDossier);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Candidate dossier request failed.");
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    const storedToken = getAccessToken();
    if (!storedToken) {
      setError("Sign in to the peptide discovery workspace to open this provisional dossier.");
      setLoading(false);
      return;
    }
    setToken(storedToken);
    void loadDossier(storedToken);
  }, [loadDossier]);

  useEffect(() => {
    if (!token || !params.id) return;
    fetch(API_BASE + "/api/v1/dossiers/candidates/" + encodeURIComponent(params.id) + "/sections", {
      headers: { Authorization: "Bearer " + token },
    }).then(async response => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Could not load curated references and images.");
      setSavedSections((result.items || []) as SavedDossierSection[]);
    }).catch(() => setSavedSections([]));
  }, [token, params.id]);

  async function submitDecision(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const body: Record<string, string> = { decision, rationale: rationale.trim() };
      if (decision === "accepted_as_existing_peptide") {
        body.canonical_peptide_id = canonicalPeptideId.trim();
      }
      const response = await fetch(
        API_BASE + "/api/v1/enrichment/discovery-candidates/" + encodeURIComponent(params.id) + "/decisions",
        {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
          body: JSON.stringify(body),
        },
      );
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Could not record the curation decision.");
      setNotice(result.notice || "Curation decision recorded.");
      setRationale("");
      setCanonicalPeptideId("");
      await loadDossier(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Curation decision failed.");
    } finally {
      setSaving(false);
    }
  }

  const field = "w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-emerald-400";
  const label = "mb-2 block text-xs font-medium text-slate-300";

  if (loading) return <main className="container py-12"><p className="muted">Loading provisional peptide dossier…</p></main>;

  if (!token) return <main className="container py-12">
    <Link href="/peptide-discovery" className="text-sm text-emerald-300">← Peptide discovery workspace</Link>
    <div role="alert" className="panel mt-8 p-6 text-sm">{error}</div>
  </main>;

  if (error && !data) return <main className="container py-12">
    <Link href="/peptide-discovery" className="text-sm text-emerald-300">← Peptide discovery workspace</Link>
    <div role="alert" className="panel mt-8 p-6 text-sm text-rose-200">{error}</div>
  </main>;

  if (!data) return null;
  const candidate = data.candidate;
  const sourceRecord = asRecord(candidate.raw_metadata.source_record);
  const dbaaspActivities = asRecords(sourceRecord.target_activities);
  const dbaaspAntibiofilm = asRecords(sourceRecord.antibiofilm_activities);
  const dbaaspCytotoxic = asRecords(sourceRecord.hemolytic_cytotoxic_activities);
  const dbaaspCombinations = asRecords(sourceRecord.reported_combination_activity);
  const dbaaspArticles = asRecords(sourceRecord.references);
  const literatureSources = asRecords(candidate.raw_metadata.literature_sources);
  const dailymedMechanism = typeof sourceRecord.mechanism_of_action === "string" ? sourceRecord.mechanism_of_action : "";
  const chemblMechanisms = asRecords(sourceRecord.mechanism_records);

  return <main className="container min-h-screen py-10">
    <Link href="/peptide-discovery" className="text-sm text-emerald-300 hover:text-emerald-200">← Peptide discovery workspace</Link>
    <header className="mt-8 max-w-4xl">
      <p className="accent text-xs tracking-[.2em]">PROVISIONAL PEPTIDE DOSSIER</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-amber-400/40 px-3 py-1 text-xs text-amber-300">{candidate.candidate_status.replaceAll("_", " ")}</span>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs">{candidate.identity_match_status.replaceAll("_", " ")}</span>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs">{candidate.source_name}</span>
      </div>
      <h1 className="mt-4 break-words text-4xl font-semibold md:text-5xl">{candidate.candidate_name}</h1>
      <p className="muted mt-3 text-sm">{candidate.source_identifier} · {candidate.candidate_kind.replaceAll("_", " ")}</p>
      <p className="muted mt-4 leading-7">{data.dossier_notice}</p>
      {candidate.canonical_peptide_id && <Link href={"/peptides/" + candidate.canonical_peptide_id} className="mt-4 inline-block text-sm text-emerald-300">Open linked canonical peptide dossier →</Link>}
      <Link href={"/peptide-discovery/" + candidate.id + "/edit"} className="mt-4 ml-4 inline-block rounded-full border border-emerald-400/50 px-4 py-2 text-sm text-emerald-300">Edit scientific dossier →</Link>
    </header>

    <nav aria-label="Candidate dossier sections" className="panel mt-6 p-4">
      <p className="text-xs uppercase tracking-[.16em] text-slate-400">Individual peptide dossier</p>
      <div className="mt-3 flex flex-wrap gap-2 text-sm">
        {([
          ["identity", "Identity & source"],
          ["sequence", "Sequence & chemistry"],
          ["mechanism", "Targets & MOA"],
          ...(literatureSources.length ? [["literature-evidence", "Supporting literature"]] : []),
          ...(candidate.source_name.includes("DBAASP") ? [["dbaasp-evidence", "DBAASP evidence"]] : []),
          ...(candidate.source_name.includes("ChEMBL") ? [["chembl-evidence", "ChEMBL evidence"]] : []),
          ...(dailymedMechanism ? [["dailymed-mechanism", "DailyMed MOA"]] : []),
          ...(candidate.source_name.includes("European Medicines Agency") ? [["ema-product", "EMA product"]] : []),
          ["source-metadata", "Source metadata"],
          ["source-history", "Source history"],
          ["curation-history", "Curation history"],
          ...(data.permissions.can_review ? [["curation", "Curator review"]] : []),
        ] as [string, string][]).map(([id, label]) => <a key={id} href={`#${id}`} className="rounded-full border border-slate-700 px-3 py-2 text-emerald-300 hover:border-emerald-400">{label}</a>)}
      </div>
      <p className="muted mt-3 text-xs">This source candidate has its own stable dossier URL. If identity is confirmed against an existing peptide, the dossier links to that canonical peptide folder; unresolved candidates remain separate until reviewed.</p>
    </nav>

    {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {notice && <div role="status" className="mt-5 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4 text-sm text-emerald-200">{notice}</div>}

    {savedSections.length > 0 && <section className="panel mt-8 p-5">
      <p className="accent text-xs tracking-widest">CURATED SOURCES & VISUAL ASSETS</p>
      <h2 className="mt-2 text-xl font-semibold">References and scientific images</h2>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        {savedSections.flatMap(section => section.media.map((asset, index) => ({...asset, section_key: section.section_key, key: section.section_key + "-" + index}))).map(asset => {
          const imageUrl = typeof asset.image_url === "string" && asset.image_url.startsWith("https://") ? asset.image_url : "";
          return <article key={asset.key} className="rounded-xl border border-slate-700 p-4">
            {imageUrl && <a href={imageUrl} target="_blank" rel="noreferrer"><img src={imageUrl} loading="lazy" referrerPolicy="no-referrer" alt={String(asset.alt_text || asset.title || "Peptide scientific visual")} className="mb-3 max-h-64 w-full rounded-lg object-contain bg-slate-950" /></a>}
            <h3 className="font-medium">{displayValue(asset.title)}</h3>
            <p className="muted mt-1 text-xs">{displayValue(asset.caption)}</p>
            <p className="muted mt-2 text-xs">Source: {displayValue(asset.source_name)} · {displayValue(asset.source_identifier)}</p>
            <p className="muted mt-1 text-xs">Attribution/licence: {displayValue(asset.attribution)} · {displayValue(asset.license_or_reuse_terms)}</p>
            {imageUrl && <a className="mt-2 inline-block text-xs text-emerald-300" href={imageUrl} target="_blank" rel="noreferrer">Open original asset →</a>}
          </article>;
        })}
        {savedSections.flatMap(section => section.citations.map((citation, index) => ({...citation, section_key: section.section_key, key: section.section_key + "-citation-" + index}))).map(citation => {
          const url = typeof citation.url === "string" && citation.url.startsWith("https://") ? citation.url : "";
          return <article key={citation.key} className="rounded-xl border border-slate-700 p-4">
            <h3 className="font-medium">{displayValue(citation.title)}</h3>
            <p className="mt-1 text-sm">{displayValue(citation.claim_text)}</p>
            <p className="muted mt-1 text-xs">{displayValue(citation.source_name)} · {displayValue(citation.evidence_type)}</p>
            <p className="muted mt-1 text-xs">Locator: {displayValue(citation.locator)} · DOI: {displayValue(citation.doi)} · PMID: {displayValue(citation.pmid)}</p>
            {url && <a className="mt-2 inline-block text-xs text-emerald-300" href={url} target="_blank" rel="noreferrer">Open source →</a>}
          </article>;
        })}
      </div>
    </section>}
    <div className="mt-8 grid gap-4 lg:grid-cols-2">
      <section id="identity" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">Identity and source</h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <dt className="muted">Source identifier</dt><dd className="break-all">{candidate.source_identifier}</dd>
          <dt className="muted">Jurisdiction</dt><dd>{candidate.source_jurisdiction_code || "Not applicable / not reported"}</dd>
          <dt className="muted">Source-reported lifecycle</dt><dd>{candidate.source_development_status || "Not reported"}</dd>
          <dt className="muted">First seen</dt><dd>{new Date(candidate.first_seen_at).toLocaleString()}</dd>
          <dt className="muted">Last seen</dt><dd>{new Date(candidate.last_seen_at).toLocaleString()}</dd>
          <dt className="muted">Last source observation</dt><dd>{new Date(candidate.last_observed_at).toLocaleString()}</dd>
          <dt className="muted">Match confidence</dt><dd>{candidate.match_confidence == null ? "Not assessed" : candidate.match_confidence.toFixed(2)}</dd>
        </dl>
        {candidate.match_rationale && <p className="muted mt-4 text-xs">Identity review: {candidate.match_rationale}</p>}
        {typeof sourceRecord.source_statement === "string" && <div className="mt-4 rounded-xl border border-amber-400/20 bg-amber-400/5 p-4">
          <p className="text-xs font-semibold text-amber-200">Source-reported regulatory / safety note</p>
          <p className="mt-2 text-sm leading-6">{sourceRecord.source_statement}</p>
          <p className="muted mt-2 text-xs">This is a quotation-level source assertion, not an independent safety assessment or a drug-approval determination.</p>
        </div>}
        <a href={candidate.source_url} target="_blank" rel="noreferrer" className="mt-5 inline-block text-sm text-emerald-300">Open original source ↗</a>
        {candidate.license_notes && <p className="muted mt-3 text-xs">Source license: {candidate.license_notes}</p>}
      </section>

      <section id="sequence" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">Sequence and chemical form</h2>
        <p className="muted mt-3 text-xs">Source-reported data only; not canonicalized or chemically validated.</p>
        <p className="mt-4 text-xs font-medium text-slate-400">Reported sequence ({candidate.reported_sequence_type || "type not specified"})</p>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all rounded-xl bg-slate-950 p-3 text-sm">{candidate.reported_sequence || "No sequence reported by this source."}</pre>
        <p className="mt-4 text-xs font-medium text-slate-400">Reported chemical form / SMILES</p>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all rounded-xl bg-slate-950 p-3 text-xs">{candidate.reported_chemical_form || "No chemical-form representation reported."}</pre>
      </section>

      <section id="mechanism" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">Target and mechanism hints</h2>
        <p className="muted mt-3 text-xs">These fields are source assertions and must not be treated as verified mechanisms.</p>
        <p className="mt-4 text-xs font-medium text-slate-400">Reported target</p>
        <p className="mt-2 text-sm">{candidate.reported_target || "Not reported"}</p>
        <p className="mt-4 text-xs font-medium text-slate-400">Reported mechanism</p>
        <p className="mt-2 text-sm">{candidate.reported_mechanism || "Not reported"}</p>
        {literatureSources.length > 0 && <div id="literature-evidence" className="mt-4 scroll-mt-24 border-t border-slate-800 pt-4">
          <p className="text-xs font-semibold text-slate-300">Supporting literature · source-reported, not curated</p>
          <div className="mt-3 space-y-3">
            {literatureSources.map((item, index) => <article key={String(item.source_identifier ?? index)} className="rounded-xl border border-slate-800 p-3">
              <p className="text-sm font-medium">{displayValue(item.title)}</p>
              <p className="muted mt-1 text-xs">{displayValue(item.publication_date)} · {displayValue(item.publication_type)} · PMID {displayValue(item.source_identifier)}</p>
              <p className="mt-2 text-xs leading-5">{displayValue(item.evidence_scope)}</p>
              {typeof item.source_excerpt === "string" && <blockquote className="mt-2 border-l-2 border-slate-700 pl-3 text-xs leading-5">{item.source_excerpt}</blockquote>}
              {typeof item.source_url === "string" && <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-300">Open PubMed source ↗</a>}
            </article>)}
          </div>
        </div>}
      </section>

      {candidate.source_name.includes("DBAASP") && <section id="dbaasp-evidence" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">DBAASP experimental evidence</h2>
        <p className="muted mt-1 text-xs">Source-reported laboratory observations. Preserve assay context; these are not clinical efficacy or incidence estimates.</p>
        {dbaaspActivities.length > 0 && <div className="mt-4"><h3 className="text-sm font-semibold">Target activity ({dbaaspActivities.length})</h3>
          <div className="mt-2 space-y-2">{dbaaspActivities.map((item, index) => <article key={String(item.id ?? index)} className="rounded-xl border border-slate-800 p-3 text-xs">
            <p className="font-semibold">{displayValue(asRecord(item.targetSpecies).name)} · {displayValue(asRecord(item.activityMeasureGroup).name)}</p>
            <p className="mt-1">{displayValue(item.activityMeasureValue)} {displayValue(asRecord(item.unit).name)} · Concentration: {displayValue(item.concentration)}</p>
            <p className="muted mt-1">Medium: {displayValue(asRecord(item.medium).name)} · pH: {displayValue(item.ph)} · Ionic strength: {displayValue(item.ionicStrength)} · CFU: {displayValue(item.cfu)}</p>
            <p className="muted mt-1">Reference: {displayValue(item.reference)}</p>
          </article>)}</div>
        </div>}
        {dbaaspAntibiofilm.length > 0 && <div className="mt-4"><h3 className="text-sm font-semibold">Antibiofilm activity ({dbaaspAntibiofilm.length})</h3>
          <div className="mt-2 space-y-2">{dbaaspAntibiofilm.map((item, index) => <article key={String(item.id ?? index)} className="rounded-xl border border-slate-800 p-3 text-xs">
            <p className="font-semibold">{displayValue(asRecord(item.targetSpecies).name)} · {displayValue(asRecord(item.activityMeasureGroup).name)}</p>
            <p className="muted mt-1">Value: {displayValue(item.activityMeasureValue)} {displayValue(asRecord(item.unit).name)} · Concentration: {displayValue(item.concentration)} · Medium: {displayValue(asRecord(item.medium).name)}</p>
            <p className="muted mt-1">Reference: {displayValue(item.reference)}</p>
          </article>)}</div>
        </div>}
        {dbaaspCytotoxic.length > 0 && <div className="mt-4"><h3 className="text-sm font-semibold">Hemolytic / cytotoxic activity ({dbaaspCytotoxic.length})</h3>
          <div className="mt-2 space-y-2">{dbaaspCytotoxic.map((item, index) => <article key={String(item.id ?? index)} className="rounded-xl border border-slate-800 p-3 text-xs">
            <p className="font-semibold">{displayValue(asRecord(item.targetCell).name)} · {displayValue(asRecord(item.activityMeasureForLysisGroup).name)}</p>
            <p className="muted mt-1">Value: {displayValue(item.activityMeasureForLysisValue)} · Concentration: {displayValue(item.concentration)} {displayValue(asRecord(item.unit).name)}</p>
            <p className="muted mt-1">pH: {displayValue(item.ph)} · Ionic strength: {displayValue(item.ionicStrength)} · Reference: {displayValue(item.reference)}</p>
          </article>)}</div>
        </div>}
        {dbaaspCombinations.length > 0 && <div className="mt-4"><h3 className="text-sm font-semibold">Reported combination observations ({dbaaspCombinations.length})</h3>
          <p className="muted mt-1 text-xs">These may be peptide–antibiotic combinations; they are not automatically peptide–peptide synergy evidence.</p>
          <div className="mt-2 space-y-2">{dbaaspCombinations.map((item, index) => <article key={String(item.id ?? index)} className="rounded-xl border border-amber-400/20 p-3 text-xs">
            <p className="font-semibold">Peptide + {displayValue(item.antibioticName)}</p>
            <p className="muted mt-1">Peptide activity: {displayValue(item.peptideActivity)} · Combination activity: {displayValue(item.peptideAntibioticActivity)} · Antibiotic activity: {displayValue(item.antibioticActivity)}</p>
            <p className="muted mt-1">Source-reported FICI: {displayValue(item.fici)} · Reference: {displayValue(item.reference)}</p>
          </article>)}</div>
        </div>}
        {dbaaspArticles.length > 0 && <div className="mt-4"><h3 className="text-sm font-semibold">Source publications ({dbaaspArticles.length})</h3>
          <ul className="mt-2 space-y-2 text-xs">{dbaaspArticles.map((item, index) => <li key={index} className="rounded-lg border border-slate-800 p-3">{displayValue(item.title)} ({displayValue(item.year)}) · PMID: {displayValue(asRecord(item.pubmed).pubmedId)}</li>)}</ul>
        </div>}
      </section>}
      {candidate.source_name.includes("ChEMBL") && <section id="chembl-evidence" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">ChEMBL peptide biotherapeutic evidence</h2>
        <p className="muted mt-1 text-xs">HELM notation and mechanism entries are copied from ChEMBL; source-reported only and not a canonical chemical identity or regulatory determination.</p>
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <p>ChEMBL ID: {displayValue(sourceRecord.molecule_chembl_id)}</p>
          <p>Molecule type: {displayValue(sourceRecord.molecule_type)}</p>
          <p>Maximum clinical phase in source: {displayValue(sourceRecord.max_phase)}</p>
          <p>ChEMBL release: {displayValue(sourceRecord.source_version)}</p>
        </div>
        <p className="mt-4 text-xs font-medium text-slate-400">HELM peptide notation</p>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all rounded-xl bg-slate-950 p-3 text-xs">{displayValue(sourceRecord.helm_notation)}</pre>
        {chemblMechanisms.length > 0 && <div className="mt-4">
          <h3 className="text-sm font-semibold">ChEMBL mechanism records ({chemblMechanisms.length})</h3>
          <div className="mt-2 space-y-2">{chemblMechanisms.map((item, index) => <article key={String(item.mechanism_id ?? index)} className="rounded-xl border border-slate-800 p-3 text-xs">
            <p className="font-semibold">{displayValue(item.mechanism_of_action)}</p>
            <p className="muted mt-1">Action: {displayValue(item.action_type)} · Target: {displayValue(item.target_name || item.target_chembl_id)}</p>
            <p className="muted mt-1">Comment: {displayValue(item.mechanism_comment)}</p>
          </article>)}</div>
        </div>}
        <p className="muted mt-3 text-xs">ChEMBL data are CC BY-SA 3.0. Attribution and share-alike obligations apply. A ChEMBL mechanism is not automatically a complete pathway or proof of clinical effect.</p>
      </section>}
      {dailymedMechanism && <section id="dailymed-mechanism" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">Source-extracted mechanism of action</h2>
        <p className="muted mt-1 text-xs">DailyMed SPL Section 12.1 · source-reported · not yet curator-verified</p>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{dailymedMechanism}</p>
        <p className="muted mt-2 text-xs">{displayValue(sourceRecord.mechanism_extraction_notice)}</p>
      </section>}
      {candidate.source_name.includes("European Medicines Agency") && <section id="ema-product" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">EMA Article 57 product observation</h2>
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <p>Product: {displayValue(sourceRecord.product_name)}</p>
          <p>Active substance: {displayValue(sourceRecord.active_substance)}</p>
          <p>Route: {displayValue(sourceRecord.route_of_administration)}</p>
          <p>Authorisation country: {displayValue(sourceRecord.country_of_authorisation)}</p>
          <p>Marketing authorisation holder: {displayValue(sourceRecord.marketing_authorisation_holder)}</p>
          <p>Snapshot status: {displayValue(sourceRecord.source_status)}</p>
        </div>
        <p className="muted mt-3 text-xs">{displayValue(sourceRecord.coverage_notice)}</p>
      </section>}
      <section id="source-metadata" className="panel scroll-mt-24 p-5">
        <h2 className="text-lg font-semibold">Source metadata</h2>
        <details className="mt-3">
          <summary className="cursor-pointer text-sm text-emerald-300">View original normalized source payload</summary>
          <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-slate-950 p-3 text-xs">{JSON.stringify(candidate.raw_metadata, null, 2)}</pre>
        </details>
      </section>
    </div>

    <section id="source-history" className="panel mt-5 scroll-mt-24 p-5">
      <h2 className="text-lg font-semibold">Source observation history</h2>
      <p className="muted mt-2 text-xs">Immutable source snapshots; changed source content creates a new observation.</p>
      {data.observations.length ? <div className="mt-4 space-y-3">
        {data.observations.map(observation => <article key={observation.id} className="rounded-xl border border-slate-800 p-4">
          <div className="flex flex-wrap justify-between gap-2 text-xs">
            <span>{new Date(observation.observed_at).toLocaleString()}</span>
            <span>{observation.source_version || "Source version not provided"}</span>
          </div>
          <p className="muted mt-2 break-all text-[10px]">SHA-256: {observation.payload_hash}</p>
          <details className="mt-3">
            <summary className="cursor-pointer text-xs text-emerald-300">View snapshot payload</summary>
            <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-slate-950 p-3 text-xs">{JSON.stringify(observation.payload, null, 2)}</pre>
          </details>
        </article>)}
      </div> : <p className="muted mt-4 text-sm">No source observations have been recorded yet.</p>}
    </section>

    <section id="curation-history" className="panel mt-5 scroll-mt-24 p-5">
      <h2 className="text-lg font-semibold">Curation decision history</h2>
      {data.decisions.length ? <div className="mt-4 space-y-3">
        {data.decisions.map(item => <article key={item.id} className="rounded-xl border border-slate-800 p-4">
          <p className="text-sm font-medium">{item.decision.replaceAll("_", " ")}</p>
          <p className="muted mt-1 text-xs">{item.reviewer_name || "Reviewer"} · {new Date(item.decided_at).toLocaleString()}</p>
          <p className="mt-3 text-sm">{item.rationale}</p>
          {item.canonical_peptide_id && <p className="muted mt-2 text-xs">Canonical peptide: {item.canonical_peptide_id}</p>}
        </article>)}
      </div> : <p className="muted mt-4 text-sm">No curation decisions have been recorded.</p>}
    </section>

    {data.permissions.can_review && <section id="curation" className="panel mt-5 scroll-mt-24 p-5">
      <h2 className="text-lg font-semibold">Curator review</h2>
      <p className="muted mt-2 text-xs">Decisions are append-only. Corrective decisions create new history entries; source observations are never overwritten.</p>
      <form onSubmit={submitDecision} className="mt-4 space-y-4">
        <label className="block"><span className={label}>Decision</span>
          <select className={field} value={decision} onChange={event => setDecision(event.target.value)}>
            <option value="needs_more_evidence">Needs more evidence</option>
            <option value="accepted_as_existing_peptide">Accept as existing verified peptide</option>
            <option value="accepted_as_new_peptide">Accept as new peptide identity</option>
            <option value="duplicate">Duplicate / ambiguous record</option>
            <option value="rejected">Reject candidate</option>
          </select>
        </label>
        {decision === "accepted_as_existing_peptide" && <label className="block"><span className={label}>Verified canonical peptide UUID</span>
          <input className={field} required value={canonicalPeptideId} onChange={event => setCanonicalPeptideId(event.target.value)} placeholder="Paste verified peptide UUID" />
        </label>}
        <label className="block"><span className={label}>Evidence-based rationale (minimum 20 characters)</span>
          <textarea className={field + " min-h-28"} required minLength={20} maxLength={4000} value={rationale} onChange={event => setRationale(event.target.value)} placeholder="Explain the identity evidence, sequence/form comparison, source limitations and reason for this decision." />
        </label>
        <button disabled={saving} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{saving ? "Recording…" : "Record curation decision"}</button>
      </form>
    </section>}
  </main>;
}

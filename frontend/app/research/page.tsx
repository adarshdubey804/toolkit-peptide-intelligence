"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type RecordItem = {
  [key: string]: string | number | boolean | null | undefined | string[] | Record<string, unknown>;
  source?: string;
  curation_status?: string;
  url?: string | null;
  title?: string | null;
  nct_id?: string | null;
  accession?: string | null;
  pdb_id?: string | null;
  pmid?: string | null;
};
type SourceResult = { status: string; source: string; total: number | null; items: RecordItem[]; error?: string | null };
type SearchResult = {
  query: string;
  retrieved_at: string;
  sources: Record<string, SourceResult>;
  summary: { sources_available: number; sources_total: number; records_returned: number };
  curation_notice: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const labels: Record<string, string> = {
  pubmed: "PubMed", clinicaltrials: "ClinicalTrials.gov", uniprot: "UniProtKB", rcsb: "RCSB PDB",
};

function getTitle(item: RecordItem) {
  return String(item.title || item.protein_name || item.entry_name || item.pdb_id || item.accession || item.pmid || item.nct_id || "Untitled source record");
}
function getIdentifier(item: RecordItem) {
  return String(item.pmid || item.nct_id || item.accession || item.pdb_id || "");
}
function getDescription(item: RecordItem) {
  return String(item.brief_summary || item.journal || item.organism || item.experimental_methods || item.study_type || "");
}
function getUrl(item: RecordItem) {
  return typeof item.url === "string" ? item.url : null;
}

export default function ResearchWorkspacePage() {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeSource, setActiveSource] = useState("all");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (query.trim().length < 3) { setError("Enter at least three characters to search."); return; }
    setLoading(true); setError(""); setResult(null); setActiveSource("all");
    try {
      const params = new URLSearchParams({ q: query.trim(), limit: String(limit) });
      const response = await fetch(`${API_BASE}/api/v1/research/workspace?${params}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Research search failed.");
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected research search error.");
    } finally { setLoading(false); }
  }

  const sourceEntries = result ? Object.entries(result.sources) : [];
  const visibleSources = sourceEntries.filter(([key]) => activeSource === "all" || activeSource === key);

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300 hover:text-emerald-200">← Toolkit home</Link>
    <header className="mt-9 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">SCIENTIFIC DISCOVERY WORKSPACE</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Research intelligence</h1>
      <p className="muted mt-4 leading-7">Search scientific literature, clinical-trial registrations, protein records and structural biology resources together. Results retain their source identity and review status.</p>
    </header>

    <form onSubmit={submit} className="panel mt-8 grid gap-4 p-5 md:grid-cols-[1fr_150px_auto] md:items-end">
      <label className="block"><span className="text-xs text-slate-400">Research question, peptide, protein or target</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="e.g. peptide receptor binding, GLP-1..." className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-emerald-400" /></label>
      <label className="block"><span className="text-xs text-slate-400">Results per source</span><select value={limit} onChange={(event) => setLimit(Number(event.target.value))} className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm"><option value={3}>3 records</option><option value={5}>5 records</option><option value={10}>10 records</option></select></label>
      <button disabled={loading} className="rounded-xl bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{loading ? "Searching…" : "Search sources →"}</button>
    </form>

    {error && <div role="alert" className="mt-4 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {loading && <div className="panel mt-5 p-8 text-sm muted">Searching connected scientific sources in parallel…</div>}

    {result && <>
      <section className="mt-7 grid gap-3 sm:grid-cols-3">
        <div className="panel p-4"><p className="muted text-xs">Sources available</p><p className="mt-2 text-2xl font-semibold">{result.summary.sources_available}/{result.summary.sources_total}</p></div>
        <div className="panel p-4"><p className="muted text-xs">Records returned</p><p className="mt-2 text-2xl font-semibold">{result.summary.records_returned}</p></div>
        <div className="panel p-4"><p className="muted text-xs">Retrieved</p><p className="mt-2 text-sm font-medium">{new Date(result.retrieved_at).toLocaleString()}</p></div>
      </section>

      <div className="mt-6 flex flex-wrap gap-2">
        <button onClick={() => setActiveSource("all")} className={`rounded-full border px-3 py-2 text-xs ${activeSource === "all" ? "border-emerald-300 bg-emerald-300/10 text-emerald-200" : "border-slate-700 text-slate-300"}`}>All sources</button>
        {sourceEntries.map(([key]) => <button key={key} onClick={() => setActiveSource(key)} className={`rounded-full border px-3 py-2 text-xs ${activeSource === key ? "border-emerald-300 bg-emerald-300/10 text-emerald-200" : "border-slate-700 text-slate-300"}`}>{labels[key] || key}</button>)}
      </div>

      <div className="mt-5 space-y-5">
        {visibleSources.map(([key, source]) => <section key={key} className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-semibold">{labels[key] || source.source}</h2><p className="muted mt-1 text-xs">{source.total === null ? "Total count not supplied" : `${source.total.toLocaleString()} matching records reported`}</p></div><span className={`rounded-full border px-3 py-1 text-xs ${source.status === "success" ? "border-emerald-400/30 text-emerald-300" : "border-amber-400/30 text-amber-300"}`}>{source.status.replaceAll("_", " ")}</span></div>
          {source.status !== "success" && <p className="muted mt-4 text-sm">{source.error || "This source could not be searched."}</p>}
          {source.items.length > 0 && <div className="mt-4 space-y-3">{source.items.map((item, index) => <article key={getIdentifier(item) || index} className="rounded-xl border border-slate-700/80 bg-slate-950/40 p-4">
            <div className="flex flex-wrap items-start justify-between gap-2"><h3 className="max-w-3xl text-sm font-semibold leading-6">{getTitle(item)}</h3><span className="rounded-full border border-amber-400/30 px-2 py-1 text-[10px] text-amber-300">Not reviewed</span></div>
            {getIdentifier(item) && <p className="muted mt-1 text-xs">{getIdentifier(item)}</p>}
            {getDescription(item) && <p className="muted mt-2 text-sm leading-6">{getDescription(item)}</p>}
            {item.publication_date && <p className="muted mt-2 text-xs">Publication date: {String(item.publication_date)}</p>}
            {getUrl(item) && <a href={getUrl(item)!} target="_blank" rel="noreferrer" className="mt-3 inline-block text-xs text-emerald-300 hover:text-emerald-200">Open original source ↗</a>}
          </article>)}</div>}
          {source.status === "success" && source.items.length === 0 && <p className="muted mt-4 text-sm">No matching records returned by this source.</p>}
        </section>)}
      </div>
      <p className="muted mt-6 rounded-xl border border-amber-400/20 bg-amber-400/5 p-4 text-xs leading-6">{result.curation_notice}</p>
    </>}
    {!result && !loading && <div className="panel mt-6 p-8"><h2 className="font-semibold">Connected discovery sources</h2><div className="mt-4 grid gap-3 sm:grid-cols-2">{Object.entries(labels).map(([key, label]) => <div key={key} className="rounded-xl border border-slate-700 p-4"><p className="text-sm font-medium">{label}</p><p className="muted mt-1 text-xs">{key === "pubmed" ? "Scientific publications and abstracts" : key === "clinicaltrials" ? "Registered interventional and observational studies" : key === "uniprot" ? "Protein identity and sequence references" : "Macromolecular structure records"}</p></div>)}</div><p className="muted mt-5 text-xs">PubMed requires NCBI_EMAIL to be configured by the platform operator.</p></div>}
    <p className="muted mt-10 border-t border-slate-800 pt-5 text-xs">External search is discovery, not scientific verification. Confirm findings in the original record and assess study design, model, limitations and conflicting evidence.</p>
  </main>;
}

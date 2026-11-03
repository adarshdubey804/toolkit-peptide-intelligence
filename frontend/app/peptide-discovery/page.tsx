"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { getPreferredOrganizationId, setPreferredOrganizationId } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const AVAILABLE_SOURCES = [
  { id: "fda_drugsfda", label: "FDA Drugs@FDA" },
  { id: "fda_purple_book", label: "FDA Purple Book" },
  { id: "gtopdb", label: "IUPHAR/BPS Guide to PHARMACOLOGY (API key required)" },
  { id: "dramp", label: "DRAMP 5.0 (Antimicrobial peptides)" },
  { id: "dailymed", label: "DailyMed" },
  { id: "health_canada_dpd", label: "Health Canada DPD" },
  { id: "clinicaltrials", label: "ClinicalTrials.gov" },
  { id: "pubmed", label: "PubMed" },
] as const;

type DiscoveryCandidate = {
  id: string;
  candidate_name: string;
  candidate_kind: string;
  source_development_status?: string | null;
  source_jurisdiction_code?: string | null;
  reported_sequence?: string | null;
  reported_chemical_form?: string | null;
  reported_target?: string | null;
  reported_mechanism?: string | null;
  identity_match_status: string;
  candidate_status: string;
  canonical_peptide_id?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  source_name: string;
  source_identifier: string;
  source_url: string;
  observation_count: number;
};
type CandidateResponse = { items: DiscoveryCandidate[]; total: number; limit: number; offset: number; scope: string };

export default function PeptideDiscoveryPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [userLabel, setUserLabel] = useState("");
  const [query, setQuery] = useState("");
  const [sources, setSources] = useState<string[]>(["fda_drugsfda", "fda_purple_book", "dailymed", "health_canada_dpd", "clinicaltrials", "pubmed"]);
  const [status, setStatus] = useState("all");
  const [candidates, setCandidates] = useState<CandidateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadCandidates = useCallback(async (authToken: string, nextStatus = status) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ limit: "50", offset: "0", candidate_status: nextStatus });
      const response = await fetch(API_BASE + "/api/v1/enrichment/discovery-candidates?" + params.toString(), {
        headers: { Authorization: "Bearer " + authToken },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load global discovery candidates.");
      setCandidates(data as CandidateResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Discovery catalogue request failed.");
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    if (token) void loadCandidates(token);
  }, [token, loadCandidates]);

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch(API_BASE + "/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, organization_id: getPreferredOrganizationId() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Sign in failed.");
      if (!["organization_admin", "curator", "reviewer", "researcher"].includes(data.user.role)) {
        throw new Error("A researcher, curator or reviewer role is required.");
      }
      setPreferredOrganizationId(data.user.organization_id);
      setToken(data.access_token);
      setUserLabel(data.user.display_name + " · " + data.user.role);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  async function runDiscovery(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSearching(true);
    setError("");
    setNotice("");
    try {
      const response = await fetch(API_BASE + "/api/v1/enrichment/discover-peptides", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify({ query: query.trim(), sources, limit: 20 }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Peptide discovery failed.");
      setNotice("Discovery completed. " + data.persisted_count + " source-backed observations were saved for review.");
      await loadCandidates(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Peptide discovery failed.");
    } finally {
      setSearching(false);
    }
  }

  function toggleSource(source: string) {
    setSources(current => current.includes(source)
      ? current.filter(item => item !== source)
      : [...current, source]);
  }

  const field = "w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-emerald-400";
  const label = "mb-2 block text-xs font-medium text-slate-300";

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-9 max-w-4xl">
      <p className="accent text-xs tracking-[.2em]">GLOBAL PEPTIDE INTELLIGENCE</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Peptide discovery workspace</h1>
      <p className="muted mt-4 leading-7">Search regulatory labels, clinical-trial records and scientific literature. Every result is retained with source provenance and remains an unresolved candidate until its peptide identity is reviewed.</p>
      <div className="mt-5 flex flex-wrap gap-3 text-xs">
        <Link href="/peptides" className="rounded-full border border-slate-600 px-4 py-2">Verified peptide dossiers</Link>
        <Link href="/enrichment" className="rounded-full border border-slate-600 px-4 py-2">Existing peptide enrichment</Link>
      </div>
    </header>

    {!token ? <section className="panel mt-8 max-w-xl p-6">
      <h2 className="text-xl font-semibold">Researcher / curator sign in</h2>
      <form onSubmit={signIn} className="mt-5 space-y-4">
        <label className="block"><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e => setEmail(e.target.value)} /></label>
        <label className="block"><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
        <button disabled={loading} className="rounded-full bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{loading ? "Signing in…" : "Sign in"}</button>
      </form>
    </section> : <>
      <div className="panel mt-7 flex flex-wrap items-center justify-between gap-3 p-4">
        <div><p className="text-sm font-semibold">{userLabel}</p><p className="muted mt-1 text-xs">Authenticated research session</p></div>
        <button onClick={() => { setToken(""); setCandidates(null); setUserLabel(""); }} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Sign out</button>
      </div>

      <section className="panel mt-5 p-5">
        <h2 className="text-lg font-semibold">Discover a peptide or peptide-related record</h2>
        <form onSubmit={runDiscovery} className="mt-4 space-y-4">
          <label className="block"><span className={label}>Peptide name, alias or scientific search term</span><input className={field} required minLength={2} maxLength={160} value={query} onChange={e => setQuery(e.target.value)} placeholder="e.g. tirzepatide, oxytocin, antimicrobial peptide" /></label>
          <fieldset>
            <legend className={label}>Sources to search</legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {AVAILABLE_SOURCES.map(source => <label key={source.id} className="flex items-center gap-3 rounded-xl border border-slate-700 p-3 text-sm">
                <input type="checkbox" checked={sources.includes(source.id)} onChange={() => toggleSource(source.id)} />
                {source.label}
              </label>)}
            </div>
          </fieldset>
          <button disabled={searching || !query.trim() || sources.length === 0} className="rounded-full bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{searching ? "Searching and saving source records…" : "Search and save discovery records"}</button>
        </form>
        <p className="muted mt-3 text-xs">Each source is queried independently. A missing result is not evidence of non-existence or non-approval. Search matches are not automatically treated as peptide identities.</p>
      </section>

      <section className="mt-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><h2 className="text-2xl font-semibold">Global discovery records</h2><p className="muted mt-1 text-sm">{candidates ? candidates.total + " source observations in this result set" : "Source-backed candidate workspace"}</p></div>
          <div className="flex flex-wrap items-end gap-2">
            <label className="block"><span className={label}>Candidate status</span><select className={field} value={status} onChange={e => setStatus(e.target.value)}><option value="all">All statuses</option><option value="discovered">Discovered</option><option value="needs_review">Needs review</option><option value="accepted">Accepted</option><option value="rejected">Rejected</option><option value="duplicate">Duplicate</option><option value="superseded">Superseded</option></select></label>
            <button onClick={() => void loadCandidates(token)} className="rounded-full border border-slate-600 px-4 py-3 text-xs">Refresh</button>
          </div>
        </div>
        {loading && <div className="panel mt-4 p-6 text-sm muted">Loading source-backed discovery records…</div>}
        {!loading && candidates?.items.length === 0 && <div className="panel mt-4 p-8 text-center"><h3 className="font-semibold">No discovery records yet</h3><p className="muted mt-2 text-sm">Search for a peptide above to create the first source-backed candidate observations.</p></div>}
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {candidates?.items.map(item => <article key={item.id} className="panel p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><p className="text-xs text-emerald-300">{item.source_name}</p><h3 className="mt-2 text-lg font-semibold">{item.candidate_name}</h3><p className="muted mt-1 break-all text-xs">{item.source_identifier}</p></div>
              <span className="rounded-full border border-amber-400/40 px-3 py-1 text-[10px] uppercase text-amber-200">{item.identity_match_status.replaceAll("_", " ")}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-400">
              <span className="rounded-full border border-slate-700 px-3 py-1">{item.candidate_status.replaceAll("_", " ")}</span>
              {item.source_jurisdiction_code && <span className="rounded-full border border-slate-700 px-3 py-1">{item.source_jurisdiction_code}</span>}
              {item.source_development_status && <span className="rounded-full border border-slate-700 px-3 py-1">{item.source_development_status.replaceAll("_", " ")}</span>}
              <span className="rounded-full border border-slate-700 px-3 py-1">{item.observation_count} observations</span>
            </div>
            {(item.reported_sequence || item.reported_chemical_form || item.reported_target || item.reported_mechanism) && <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-2">
              {item.reported_sequence && <><dt className="muted">Reported sequence</dt><dd className="break-all">{item.reported_sequence}</dd></>}
              {item.reported_chemical_form && <><dt className="muted">Reported chemical form</dt><dd>{item.reported_chemical_form}</dd></>}
              {item.reported_target && <><dt className="muted">Reported target</dt><dd>{item.reported_target}</dd></>}
              {item.reported_mechanism && <><dt className="muted">Reported mechanism (unreviewed)</dt><dd>{item.reported_mechanism}</dd></>}
            </dl>}
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
              <p className="muted text-[10px]">Last observed {new Date(item.last_seen_at).toLocaleString()}</p>
              <div className="flex gap-3">
                <a href={item.source_url} target="_blank" rel="noreferrer" className="text-sm text-emerald-300">Open source ↗</a>
                {item.canonical_peptide_id && <Link href={"/peptides/" + item.canonical_peptide_id} className="text-sm text-emerald-300">Open peptide dossier →</Link>}
              </div>
            </div>
          </article>)}
        </div>
      </section>
      <p className="muted mt-10 border-t border-slate-800 pt-5 text-xs">Discovery records are not verified peptide entities. Regulatory authorization and mechanism-of-action claims are curated in their respective evidence models. Unknown or missing source data is kept explicit.</p>
    </>}
    {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {notice && <div role="status" className="mt-5 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4 text-sm text-emerald-200">{notice}</div>}
  </main>;
}

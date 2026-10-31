"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type Candidate = {
  candidate_id: string;
  source: string;
  source_identifier: string;
  source_url: string;
  title: string;
  publication_date?: string | null;
  study_type?: string | null;
  overall_status?: string | null;
  organism?: string | null;
  sequence_length?: number | null;
  summary?: string | null;
  match_basis: string;
  curation_status: string;
};
type SavedCandidate = { id: string; peptide_id: string; preferred_name: string; source_name: string; source_identifier: string; source_url: string; title: string; candidate_status: string; submitted_by: string; };
type EnrichmentResult = {
  peptide: { id: string; preferred_name: string; category?: string | null; existing_review_status: string };
  retrieval_query: string;
  sources: Record<string, { status: string; source: string; total?: number | null; items: unknown[]; error?: string | null }>;
  candidates: Candidate[];
  summary: { sources_available: number; candidate_count: number };
  next_step: string;
  governance: string;
};

export default function EnrichmentPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [userLabel, setUserLabel] = useState("");
  const [peptideId, setPeptideId] = useState("");
  const [result, setResult] = useState<EnrichmentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [queue, setQueue] = useState<SavedCandidate[]>([]);
  const [queueStatus, setQueueStatus] = useState("pending");
  const [queueLoading, setQueueLoading] = useState(false);
  const [rationales, setRationales] = useState<Record<string, string>>({});

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      const response = await fetch(API_BASE + "/api/v1/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Sign in failed.");
      if (!["organization_admin", "curator", "reviewer", "researcher"].includes(data.user.role)) {
        throw new Error("Your organization role cannot run peptide enrichment.");
      }
      setToken(data.access_token);
      setUserLabel(data.user.display_name + " · " + data.user.role);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally { setLoading(false); }
  }

  async function discover(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setLoading(true); setError(""); setNotice(""); setResult(null);
    try {
      const response = await fetch(API_BASE + "/api/v1/enrichment/peptides/" + encodeURIComponent(peptideId.trim()), {
        headers: { Authorization: "Bearer " + token },
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Enrichment discovery failed.");
      setResult(data);
      setNotice("Discovery completed. All returned candidates remain unreviewed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Enrichment request failed.");
    } finally { setLoading(false); }
  }


  async function saveCandidate(item: Candidate) {
    if (!token || !result) return;
    setError(""); setNotice("");
    try {
      const response = await fetch(API_BASE + "/api/v1/enrichment/peptides/" + result.peptide.id + "/candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify({
          source: item.source, source_identifier: item.source_identifier, source_url: item.source_url,
          title: item.title, summary: item.summary || null, match_basis: item.match_basis,
          raw_metadata: { publication_date: item.publication_date, study_type: item.study_type,
            overall_status: item.overall_status, organism: item.organism, sequence_length: item.sequence_length }
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not submit candidate.");
      setSavedIds(prev => [...prev, item.candidate_id]);
      setNotice("Candidate saved to your organization's curator queue.");
    } catch (err) { setError(err instanceof Error ? err.message : "Candidate submission failed."); }
  }

  async function loadQueue() {
    if (!token) return;
    setQueueLoading(true); setError("");
    try {
      const response = await fetch(API_BASE + "/api/v1/enrichment/candidates?candidate_status=" + queueStatus + "&limit=100", {
        headers: { Authorization: "Bearer " + token }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load enrichment queue.");
      setQueue(data.items || []);
    } catch (err) { setError(err instanceof Error ? err.message : "Queue request failed."); }
    finally { setQueueLoading(false); }
  }

  async function decideCandidate(candidate: SavedCandidate, decision: "accepted" | "rejected" | "duplicate" | "needs_review") {
    const rationale = (rationales[candidate.id] || "").trim();
    if (rationale.length < 20) { setError("Please enter a rationale of at least 20 characters."); return; }
    setError("");
    try {
      const response = await fetch(API_BASE + "/api/v1/enrichment/candidates/" + candidate.id + "/decisions", {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify({ decision, rationale })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Decision could not be recorded.");
      setNotice("Candidate decision recorded: " + decision.replace("_", " ") + ".");
      setRationales(prev => ({ ...prev, [candidate.id]: "" }));
      await loadQueue();
    } catch (err) { setError(err instanceof Error ? err.message : "Decision failed."); }
  }

  const field = "w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-emerald-400";
  const label = "mb-2 block text-xs font-medium text-slate-300";

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-9 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">SOURCE-GROUNDED DISCOVERY</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Peptide enrichment review</h1>
      <p className="muted mt-4 leading-7">Discover related literature, clinical studies, protein records and structures for an existing peptide dossier. Results are suggestions for expert inspection, never automatic scientific facts.</p>
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
        <div><p className="text-sm font-semibold">{userLabel}</p><p className="muted mt-1 text-xs">Authenticated discovery session</p></div>
        <div className="flex gap-2"><button onClick={() => void loadQueue()} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Load curator queue</button><button onClick={() => { setToken(""); setResult(null); setUserLabel(""); setQueue([]); }} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Sign out</button></div>
      </div>
      <section className="panel mt-5 p-5">
        <form onSubmit={discover} className="grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
          <label className="block"><span className={label}>Peptide dossier UUID</span><input className={field} required minLength={36} maxLength={36} value={peptideId} onChange={e => setPeptideId(e.target.value)} placeholder="Paste the peptide record UUID" /></label>
          <button disabled={loading || peptideId.trim().length !== 36} className="rounded-full bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{loading ? "Searching sources…" : "Discover evidence"}</button>
        </form>
        <p className="muted mt-3 text-xs">Find the UUID in a submitted dossier or the curation queue. Discovery currently searches the peptide's preferred name and aliases.</p>
      </section>
    </>}

    {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {notice && <div role="status" className="mt-5 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4 text-sm text-emerald-200">{notice}</div>}

    {result && <>
      <section className="panel mt-6 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="accent text-xs tracking-widest">TARGET DOSSIER</p><h2 className="mt-2 text-2xl font-semibold">{result.peptide.preferred_name}</h2><p className="muted mt-1 text-xs">Existing status: {result.peptide.existing_review_status} · {result.peptide.category || "Category not specified"}</p></div><span className="rounded-full border border-amber-400/40 px-3 py-1 text-xs text-amber-200">Discovery only</span></div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3"><div className="rounded-xl border border-slate-700 p-4"><p className="muted text-xs">Sources available</p><p className="mt-2 text-2xl font-semibold">{result.summary.sources_available}/4</p></div><div className="rounded-xl border border-slate-700 p-4"><p className="muted text-xs">Candidates found</p><p className="mt-2 text-2xl font-semibold">{result.summary.candidate_count}</p></div><div className="rounded-xl border border-slate-700 p-4"><p className="muted text-xs">Candidate review state</p><p className="mt-2 text-lg font-semibold text-amber-200">Unreviewed</p></div></div>
      </section>
      <section className="mt-7">
        <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-2xl font-semibold">Source results</h2><p className="muted mt-1 text-sm">Check original records before accepting any match.</p></div><span className="muted text-xs">Query: {result.retrieval_query}</span></div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(result.sources).map(([key, source]) => <div key={key} className="panel p-4"><div className="flex items-center justify-between gap-2"><h3 className="font-semibold">{source.source}</h3><span className={"text-[10px] uppercase " + (source.status === "success" ? "text-emerald-300" : "text-amber-200")}>{source.status.replace("_", " ")}</span></div><p className="muted mt-2 text-xs">{source.items.length} returned · {source.total ?? "total unavailable"} total</p>{source.error && <p className="mt-2 text-xs text-amber-200">{source.error}</p>}</div>)}</div>
      </section>
      <section className="mt-7">
        <h2 className="text-2xl font-semibold">Evidence candidates ({result.candidates.length})</h2>
        {result.candidates.length === 0 ? <div className="panel mt-4 p-8 text-sm muted">No candidates returned. Try checking aliases or searching the research workspace separately.</div> : <div className="mt-4 space-y-3">{result.candidates.map(item => <article key={item.candidate_id} className="panel p-5">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="accent text-[10px] uppercase tracking-widest">{item.source} · {item.source_identifier}</p><h3 className="mt-2 text-lg font-semibold">{item.title}</h3></div><span className="rounded-full border border-amber-400/40 px-3 py-1 text-[10px] text-amber-200">{item.curation_status}</span></div>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">{item.publication_date && <span>{item.publication_date}</span>}{item.study_type && <span>· {item.study_type}</span>}{item.overall_status && <span>· {item.overall_status}</span>}{item.organism && <span>· {item.organism}</span>}{item.sequence_length && <span>· {item.sequence_length} aa</span>}</div>
          {item.summary && <p className="mt-4 whitespace-pre-line text-sm leading-6 text-slate-300">{item.summary}</p>}
          <p className="muted mt-4 text-xs">{item.match_basis}</p>
          <div className="mt-3 flex flex-wrap items-center gap-4"><a href={item.source_url} target="_blank" rel="noreferrer" className="inline-block break-all text-sm text-emerald-300 underline">Inspect original source ↗</a><button disabled={savedIds.includes(item.candidate_id)} onClick={() => void saveCandidate(item)} className="rounded-full border border-emerald-400/50 px-4 py-2 text-xs text-emerald-200 disabled:opacity-50">{savedIds.includes(item.candidate_id) ? "Saved to review queue" : "Submit for curator review"}</button></div>
        </article>)}</div>}
      </section>
      <div className="panel mt-7 p-5"><h2 className="font-semibold">Scientific governance</h2><p className="muted mt-2 text-sm leading-6">{result.governance}</p><p className="mt-3 text-sm leading-6 text-slate-300">{result.next_step}</p><Link href="/curation" className="mt-4 inline-block text-sm text-emerald-300">Open curator review dashboard →</Link></div>
    </>}

    {token && <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="accent text-xs tracking-widest">ORGANIZATION WORKSPACE</p><h2 className="mt-2 text-2xl font-semibold">Enrichment review queue</h2><p className="muted mt-1 text-sm">Curators and reviewers can record decisions with a permanent rationale.</p></div><div className="flex gap-2"><select className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs" value={queueStatus} onChange={e => setQueueStatus(e.target.value)}><option value="pending">Pending</option><option value="accepted">Accepted</option><option value="rejected">Rejected</option><option value="duplicate">Duplicate</option><option value="needs_review">Needs review</option><option value="all">All</option></select><button onClick={() => void loadQueue()} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Refresh</button></div></div>
      {queueLoading && <div className="panel mt-4 p-5 text-sm muted">Loading candidates…</div>}
      {!queueLoading && queue.length === 0 && <div className="panel mt-4 p-6 text-sm muted">No candidates in this queue view.</div>}
      <div className="mt-4 space-y-3">{queue.map(candidate => <article key={candidate.id} className="panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="accent text-[10px] uppercase tracking-widest">{candidate.source_name} · {candidate.source_identifier}</p><h3 className="mt-2 text-lg font-semibold">{candidate.title}</h3><p className="muted mt-1 text-xs">{candidate.preferred_name} · {candidate.candidate_status}</p></div><a href={candidate.source_url} target="_blank" rel="noreferrer" className="text-xs text-emerald-300 underline">Original source ↗</a></div>
        {candidate.candidate_status === "pending" && ["organization_admin","curator","reviewer"].some(role => userLabel.endsWith(role)) && <div className="mt-4"><label className="block"><span className={label}>Decision rationale (minimum 20 characters)</span><textarea className={field} rows={2} value={rationales[candidate.id] || ""} onChange={e => setRationales(prev => ({ ...prev, [candidate.id]: e.target.value }))} placeholder="Explain identity checks, relevance, duplication or evidence limitations."/></label><div className="mt-3 flex flex-wrap gap-2">{(["accepted","rejected","duplicate","needs_review"] as const).map(decision => <button key={decision} onClick={() => void decideCandidate(candidate, decision)} className="rounded-full border border-slate-600 px-3 py-2 text-xs hover:border-emerald-400">{decision.replace("_"," ")}</button>)}</div></div>}
      </article>)}</div>
    </section>}
  </main>;
}

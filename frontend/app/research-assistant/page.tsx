"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type Citation = {
  citation_id: string;
  source: string;
  identifier: string;
  title: string;
  url: string;
  publication_date?: string | null;
  study_type?: string | null;
  overall_status?: string | null;
  organism?: string | null;
  experimental_methods?: string | null;
  curation_status: string;
};
type Brief = {
  mode: string;
  question: string;
  answer: string;
  citations: Citation[];
  retrieval_summary: { sources_queried: number; sources_with_records: number; records_retrieved: number; sources: string[] };
  limitations: string[];
  next_review_steps: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function ResearchAssistantPage() {
  const [question, setQuestion] = useState("");
  const [brief, setBrief] = useState<Brief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (question.trim().length < 8) { setError("Please enter a more specific research question (at least 8 characters)."); return; }
    setLoading(true); setError(""); setBrief(null);
    try {
      const params = new URLSearchParams({ question: question.trim(), limit: "5" });
      const response = await fetch(`${API_BASE}/api/v1/research/assistant/brief?${params}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "The research assistant could not retrieve sources.");
      setBrief(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected research assistant error.");
    } finally { setLoading(false); }
  }

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300 hover:text-emerald-200">← Toolkit home</Link>
    <header className="mt-9 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">EVIDENCE-GROUNDED RESEARCH AGENT</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">AI research assistant</h1>
      <p className="muted mt-4 leading-7">Ask a scientific research question and retrieve relevant records from connected databases. Every result links to its original source.</p>
    </header>

    <form onSubmit={submit} className="panel mt-8 p-5">
      <label className="block text-xs text-slate-400" htmlFor="research-question">What would you like to investigate?</label>
      <textarea id="research-question" value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} placeholder="Example: What clinical studies have investigated peptide-based GLP-1 receptor agonists, and what outcomes were reported?" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm leading-6 outline-none focus:border-emerald-400" />
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3"><p className="muted text-xs">Retrieves up to 5 records per source.</p><button disabled={loading} className="rounded-xl bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{loading ? "Retrieving evidence…" : "Build research brief →"}</button></div>
    </form>

    {error && <div role="alert" className="mt-4 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {loading && <div className="panel mt-5 p-8 text-sm muted">Retrieving source records. No scientific conclusions are generated from missing evidence.</div>}

    {brief && <>
      <section className="panel mt-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3"><p className="accent text-xs tracking-widest">RESEARCH BRIEF</p><span className="rounded-full border border-amber-400/30 px-3 py-1 text-xs text-amber-300">Retrieval-only mode</span></div>
        <h2 className="mt-3 text-xl font-semibold">Your question</h2>
        <p className="muted mt-2 text-sm leading-6">{brief.question}</p>
        <h3 className="mt-6 font-semibold">Evidence retrieval summary</h3>
        <p className="mt-2 text-sm leading-7">{brief.answer}</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-3"><div className="rounded-xl border border-slate-700 p-3"><p className="muted text-xs">Sources with records</p><p className="mt-1 text-xl font-semibold">{brief.retrieval_summary.sources_with_records}/{brief.retrieval_summary.sources_queried}</p></div><div className="rounded-xl border border-slate-700 p-3"><p className="muted text-xs">Records retrieved</p><p className="mt-1 text-xl font-semibold">{brief.retrieval_summary.records_retrieved}</p></div><div className="rounded-xl border border-slate-700 p-3"><p className="muted text-xs">Connected sources</p><p className="mt-1 text-sm font-semibold">{brief.retrieval_summary.sources.join(", ") || "None returned records"}</p></div></div>
      </section>

      <section className="mt-6"><div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Retrieved source records</h2><span className="muted text-xs">{brief.citations.length} records</span></div>
        {brief.citations.length ? <div className="mt-4 space-y-3">{brief.citations.map((citation) => <article key={citation.citation_id} className="panel p-5"><div className="flex flex-wrap items-start justify-between gap-2"><h3 className="text-sm font-semibold leading-6">{citation.title}</h3><span className="rounded-full border border-amber-400/30 px-2 py-1 text-[10px] text-amber-300">Not reviewed</span></div><p className="muted mt-2 text-xs">{citation.source} · {citation.identifier}{citation.publication_date ? ` · ${citation.publication_date}` : ""}</p><div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">{citation.study_type && <span className="rounded-full border border-slate-700 px-2 py-1">{citation.study_type}</span>}{citation.overall_status && <span className="rounded-full border border-slate-700 px-2 py-1">{citation.overall_status}</span>}{citation.organism && <span className="rounded-full border border-slate-700 px-2 py-1">{citation.organism}</span>}{citation.experimental_methods && <span className="rounded-full border border-slate-700 px-2 py-1">{citation.experimental_methods}</span>}</div><a href={citation.url} target="_blank" rel="noreferrer" className="mt-4 inline-block text-xs text-emerald-300">Open original source ↗</a></article>)}</div> : <div className="panel mt-4 p-6 text-sm muted">No source records were retrieved. Try a shorter or more specific query. This does not establish absence of published evidence.</div>}
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2"><div className="panel p-5"><h2 className="font-semibold">Limitations</h2><ul className="muted mt-3 list-disc space-y-2 pl-5 text-sm leading-6">{brief.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div><div className="panel p-5"><h2 className="font-semibold">Recommended review steps</h2><ol className="muted mt-3 list-decimal space-y-2 pl-5 text-sm leading-6">{brief.next_review_steps.map((item) => <li key={item}>{item}</li>)}</ol></div></section>
    </>}
    <p className="muted mt-10 border-t border-slate-800 pt-5 text-xs leading-6">Current implementation is retrieval-only, not a generative AI model. It does not infer results or replace expert interpretation. External records are unreviewed and are not clinical recommendations.</p>
  </main>;
}

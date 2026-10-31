"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Peptide = {
  id: string;
  preferred_name: string;
  peptide_category?: string | null;
  description?: string | null;
  development_status?: string | null;
  intended_use_class: string;
};

type SearchResponse = { items: Peptide[]; total: number; limit: number; offset: number };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function PeptideDirectoryPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(0);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");
      const params = new URLSearchParams({ limit: "25", offset: String(page * 25) });
      if (query.trim()) params.set("q", query.trim());
      if (category) params.set("category", category);
      try {
        const response = await fetch(`${API_BASE}/api/v1/peptides?${params.toString()}`, { signal: controller.signal });
        if (!response.ok) throw new Error(response.status === 503 ? "The catalogue service is temporarily unavailable." : "Could not load peptide records. Check that the API and database are running.");
        setData(await response.json());
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Unexpected catalogue error.");
          setData(null);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [query, category, page]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 25)) : 1;

  return (
    <main className="container min-h-screen py-10">
      <Link href="/" className="text-sm text-emerald-300 hover:text-emerald-200">← Toolkit home</Link>
      <div className="mt-10 max-w-3xl">
        <p className="accent text-xs tracking-[.2em]">SCIENTIFIC CATALOGUE</p>
        <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Peptide database</h1>
        <p className="muted mt-4 leading-7">Explore curator-verified peptide records. Search results are limited to records that have passed scientific review.</p>
      </div>

      <section className="panel mt-9 grid gap-3 p-4 md:grid-cols-[1fr_220px]">
        <label className="block">
          <span className="mb-2 block text-xs text-slate-400">Search by name, alias or description</span>
          <input value={query} onChange={(event) => { setQuery(event.target.value); setPage(0); }} placeholder="Search peptide records..." className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-emerald-400" />
        </label>
        <label className="block">
          <span className="mb-2 block text-xs text-slate-400">Category</span>
          <input value={category} onChange={(event) => { setCategory(event.target.value); setPage(0); }} placeholder="Optional category" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-emerald-400" />
        </label>
      </section>

      <div className="mt-6 flex items-center justify-between gap-4">
        <p className="muted text-sm">{loading ? "Searching verified records…" : data ? `${data.total} verified records` : "Catalogue status"}</p>
        <span className="rounded-full border border-emerald-400/30 px-3 py-1 text-xs text-emerald-300">Verified records only</span>
      </div>

      {error && <div role="alert" className="mt-4 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
      {loading && <div className="panel mt-4 p-8 text-sm text-slate-300">Loading catalogue…</div>}
      {!loading && !error && data?.items.length === 0 && (
        <div className="panel mt-4 p-10 text-center"><h2 className="text-lg font-semibold">No verified records found</h2><p className="muted mt-2 text-sm">The catalogue is awaiting its first curated peptide records, or your search returned no matches.</p></div>
      )}
      {!loading && data && data.items.length > 0 && (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {data.items.map((item) => (
            <article key={item.id} className="panel p-5">
              <div className="flex items-start justify-between gap-3"><h2 className="text-lg font-semibold">{item.preferred_name}</h2><span className="shrink-0 rounded-full bg-emerald-400/10 px-2 py-1 text-[10px] uppercase tracking-wide text-emerald-300">Verified</span></div>
              <p className="muted mt-2 text-sm">{item.description || "No curated description available."}</p>
              <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-400">{item.peptide_category && <span className="rounded-full border border-slate-700 px-3 py-1">{item.peptide_category}</span>}<span className="rounded-full border border-slate-700 px-3 py-1">{item.intended_use_class}</span></div>
              <Link href={`/peptides/${item.id}`} className="mt-5 inline-block text-sm text-emerald-300 hover:text-emerald-200">Open scientific profile →</Link>
            </article>
          ))}
        </div>
      )}
      {data && data.total > 25 && <div className="mt-8 flex items-center justify-between"><button disabled={page === 0} onClick={() => setPage((value) => Math.max(0, value - 1))} className="rounded-full border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">Previous</button><span className="muted text-xs">Page {page + 1} of {totalPages}</span><button disabled={page + 1 >= totalPages} onClick={() => setPage((value) => value + 1)} className="rounded-full border border-slate-700 px-4 py-2 text-sm disabled:opacity-40">Next</button></div>}
      <p className="muted mt-12 border-t border-slate-800 pt-5 text-xs">Scientific records are informational. A verified record indicates editorial review of the record, not regulatory approval or clinical endorsement.</p>
    </main>
  );
}

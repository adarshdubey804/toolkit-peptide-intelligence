"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const attributes = ["identity","purity","quantity","structure","composition","physical_state","microbiological_quality","potency","stability"] as const;
type Source = {source_name:string;source_identifier:string;source_url:string;evidence_scope:string};
type TestEntry = {
  id:string;catalogue_code:string;test_name:string;quality_attribute:string;test_intent:string;
  candidate_method_families:string[];material_considerations:string;interpretation_limitations:string;
  review_status:string;sources:Source[];
};

export default function AnalyticalTestCataloguePage() {
  const [items,setItems]=useState<TestEntry[]>([]);
  const [q,setQ]=useState("");
  const [attribute,setAttribute]=useState("");
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const pretty=(v:string)=>v.replaceAll("_"," ");
  async function load(e?:FormEvent) {
    e?.preventDefault();setLoading(true);setError("");
    try {
      const params=new URLSearchParams();if(q.trim())params.set("q",q.trim());if(attribute)params.set("quality_attribute",attribute);
      const response=await fetch(API+"/api/v1/analytical-methods/test-catalogue?"+params.toString());
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Test catalogue unavailable.");
      setItems(data.items||[]);
    }catch(err){setError(err instanceof Error?err.message:"Could not load test catalogue.");}
    finally{setLoading(false);}
  }
  useEffect(()=>{void load();},[]);
  return <main className="container min-h-screen py-10">
    <Link href="/analytical-methods" className="text-sm text-emerald-300">← Analytical methods</Link>
    <header className="mt-8 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">PEPTIDE QUALITY ATTRIBUTE FRAMEWORK</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Analytical test catalogue</h1>
      <p className="muted mt-4 leading-7">A structured index of peptide quality attributes, test intent, candidate analytical method families, material considerations and source evidence. It helps organize research; it does not prescribe a test panel or acceptance limits.</p>
    </header>
    <div className="panel mt-7 p-5">
      <form onSubmit={load} className="grid gap-3 md:grid-cols-[1fr_240px_auto]">
        <input className={field} value={q} onChange={e=>setQ(e.target.value)} placeholder="Search tests, attributes or intent"/>
        <select className={field} value={attribute} onChange={e=>setAttribute(e.target.value)}><option value="">All quality attributes</option>{attributes.map(x=><option key={x} value={x}>{pretty(x)}</option>)}</select>
        <button disabled={loading} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Search</button>
      </form>
    </div>
    {error&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    <div className="mt-7 flex items-center justify-between"><h2 className="text-2xl font-semibold">Reference entries</h2><span className="muted text-xs">{items.length} entries</span></div>
    {loading&&<p className="muted mt-4 text-sm">Loading catalogue…</p>}
    {!loading&&items.length===0&&<div className="panel mt-4 p-6 text-sm muted">No entries match this search.</div>}
    <section className="mt-4 grid gap-4 lg:grid-cols-2">
      {items.map(item=><article key={item.id} className="panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-2"><div><p className="accent text-xs tracking-wide">{item.catalogue_code}</p><h3 className="mt-1 text-lg font-semibold">{item.test_name}</h3></div><span className="rounded-full border border-amber-400/40 px-3 py-1 text-xs text-amber-200">{pretty(item.review_status)} · unreviewed</span></div>
        <p className="muted mt-2 text-xs uppercase tracking-wide">{pretty(item.quality_attribute)}</p>
        <p className="mt-4 text-sm leading-6">{item.test_intent}</p>
        <div className="mt-4"><p className="text-xs font-semibold">Candidate method families</p><div className="mt-2 flex flex-wrap gap-2">{item.candidate_method_families.map(x=><span key={x} className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">{x}</span>)}</div></div>
        <div className="mt-4 rounded-lg border border-slate-700 p-3"><p className="text-xs font-semibold">Material considerations</p><p className="muted mt-1 text-sm">{item.material_considerations}</p><p className="mt-3 text-xs font-semibold text-amber-200">Interpretation limitations</p><p className="muted mt-1 text-sm">{item.interpretation_limitations}</p></div>
        <div className="mt-4 border-t border-slate-700 pt-3"><p className="text-xs font-semibold">Source evidence</p>{item.sources.map(source=><div key={source.source_identifier} className="mt-2"><p className="muted text-xs">{source.evidence_scope}</p><a className="mt-1 block break-all text-xs text-emerald-300 underline" href={source.source_url} target="_blank" rel="noreferrer">{source.source_name} · {source.source_identifier} ↗</a></div>)}</div>
      </article>)}
    </section>
    <div className="panel mt-8 p-5"><h2 className="font-semibold">Important interpretation boundary</h2><p className="muted mt-2 text-sm leading-6">All initial entries are deliberately marked draft and unreviewed. Candidate method families are not evidence of suitability for a specific peptide. Test selection, analytical procedure qualification/validation, acceptance criteria and required specifications depend on the actual molecule, material stage, formulation, route, intended use, jurisdiction and supporting data. A citation does not by itself prove every statement in an entry.</p></div>
  </main>;
}

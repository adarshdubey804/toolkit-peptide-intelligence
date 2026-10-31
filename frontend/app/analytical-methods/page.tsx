"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const categories = ["chromatography","mass_spectrometry","spectroscopy","electrophoresis","amino_acid_analysis","endotoxin","sterility","microbiology","stability","physical_characterization","other"] as const;
type Method = { id:string; method_name:string; method_category:string; scientific_principle:string; intended_purpose:string; applicable_materials:string[]; method_classification:string; instrument_platform?:string; sample_requirements?:string; method_scope?:string; method_version?:string; reference_standard?:string; validation_status:string; acceptance_criteria_source?:string; limitations:string; sources:{source_name:string;source_identifier:string;source_url:string;evidence_scope:string}[] };
type Review = { id:string; method_name:string; method_category:string; method_classification:string; validation_status:string; intended_purpose:string; limitations:string; sources:{source_name:string;source_identifier:string;source_url:string;evidence_scope:string}[] };

const emptyForm = { method_name:"", method_category:"chromatography", scientific_principle:"", intended_purpose:"", applicable_materials:"synthetic peptide", method_classification:"published", instrument_platform:"", sample_requirements:"", method_scope:"", method_version:"", reference_standard:"", validation_status:"not_assessed", acceptance_criteria_source:"", limitations:"", source_name:"", source_identifier:"", source_url:"", evidence_scope:"" };

export default function AnalyticalMethodsPage() {
  const [methods,setMethods]=useState<Method[]>([]);
  const [reviews,setReviews]=useState<Review[]>([]);
  const [q,setQ]=useState("");
  const [category,setCategory]=useState("");
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [token,setToken]=useState("");
  const [role,setRole]=useState("");
  const [form,setForm]=useState({...emptyForm});
  const [rationales,setRationales]=useState<Record<string,string>>({});
  const [error,setError]=useState("");
  const [message,setMessage]=useState("");
  const [busy,setBusy]=useState(false);
  const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const label="mb-2 block text-xs text-slate-300";
  const pretty=(v:string)=>v.replaceAll("_"," ");

  async function loadMethods(e?:FormEvent) {
    e?.preventDefault();setBusy(true);setError("");
    try {
      const params=new URLSearchParams();if(q.trim())params.set("q",q.trim());if(category)params.set("category",category);
      const response=await fetch(API+"/api/v1/analytical-methods?"+params.toString());
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Could not load methods.");
      setMethods(data.items||[]);
    }catch(e){setError(e instanceof Error?e.message:"Method search failed.");}finally{setBusy(false);}
  }

  async function signIn(e:FormEvent) {
    e.preventDefault();setBusy(true);setError("");
    try {
      const response=await fetch(API+"/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Sign in failed.");
      setToken(data.access_token);setRole(data.user.role);setPassword("");setMessage("Signed in as "+data.user.role+".");
    }catch(e){setError(e instanceof Error?e.message:"Sign in failed.");}finally{setBusy(false);}
  }

  async function submit(e:FormEvent) {
    e.preventDefault();if(!token)return;setBusy(true);setError("");setMessage("");
    try {
      const payload={...form,applicable_materials:form.applicable_materials.split(",").map(x=>x.trim()).filter(Boolean)};
      const response=await fetch(API+"/api/v1/analytical-methods",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify(payload)});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Submission failed.");
      setMessage("Method submitted for scientific review. It is not yet publicly listed.");
      setForm({...emptyForm});await loadReviews();
    }catch(e){setError(e instanceof Error?e.message:"Submission failed.");}finally{setBusy(false);}
  }

  async function loadReviews() {
    if(!token)return;
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/reviews",{headers:{Authorization:"Bearer "+token}});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Review queue unavailable.");
      setReviews(data.items||[]);
    }catch(e){setError(e instanceof Error?e.message:"Queue request failed.");}
  }

  async function decide(method:Review,decision:"verified"|"rejected"|"needs_changes") {
    const rationale=(rationales[method.id]||"").trim();if(rationale.length<20){setError("Review rationale must contain at least 20 characters.");return;}
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/"+method.id+"/decisions",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({decision,rationale})});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Review decision failed.");
      setMessage("Method review recorded. Validation status remains "+pretty(data.validation_status)+".");
      setRationales(prev=>({...prev,[method.id]:""}));await loadReviews();if(decision==="verified")await loadMethods();
    }catch(e){setError(e instanceof Error?e.message:"Review decision failed.");}
  }

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-8 max-w-3xl"><p className="accent text-xs tracking-[.2em]">ANALYTICAL & CHARACTERIZATION SCIENCE</p><h1 className="mt-3 text-4xl font-semibold md:text-5xl">Analytical method intelligence</h1><p className="muted mt-4 leading-7">A source-linked catalogue of analytical principles, applications, material scope, reference standards and limitations for peptide characterization and quality research.</p><Link href="/analytical-methods/applicability" className="mt-4 inline-flex rounded-full border border-emerald-400/40 px-4 py-2 text-sm text-emerald-200">Open peptide-specific applicability matrix →</Link></header>
    {error&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {message&&<div role="status" className="mt-5 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{message}</div>}
    <section className="panel mt-7 p-5"><form onSubmit={loadMethods} className="grid gap-3 md:grid-cols-[1fr_220px_auto]"><input className={field} value={q} onChange={e=>setQ(e.target.value)} placeholder="Search method name or purpose"/><select className={field} value={category} onChange={e=>setCategory(e.target.value)}><option value="">All method categories</option>{categories.map(c=><option key={c} value={c}>{pretty(c)}</option>)}</select><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Search methods</button></form><p className="muted mt-3 text-xs">Only curator-reviewed records are displayed. No default or example methods are invented.</p></section>
    <section className="mt-8"><div className="flex items-center justify-between"><h2 className="text-2xl font-semibold">Reviewed methods</h2><button onClick={()=>void loadMethods()} className="text-sm text-emerald-300">Refresh</button></div>{methods.length===0?<div className="panel mt-4 p-7 text-sm muted">No verified method records found. Search or submit a source-backed method for review.</div>:<div className="mt-4 grid gap-4 lg:grid-cols-2">{methods.map(m=><article key={m.id} className="panel p-5"><div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="text-lg font-semibold">{m.method_name}</h3><p className="muted mt-1 text-xs">{pretty(m.method_category)} · {pretty(m.method_classification)}</p></div><span className="rounded-full border border-emerald-400/40 px-3 py-1 text-xs text-emerald-200">Reviewed</span></div><p className="mt-4 text-sm leading-6">{m.scientific_principle}</p><div className="mt-4 grid gap-3 sm:grid-cols-2"><div><p className="text-xs font-semibold">Intended purpose</p><p className="muted mt-1 text-sm">{m.intended_purpose}</p></div><div><p className="text-xs font-semibold">Applicable materials</p><p className="muted mt-1 text-sm">{m.applicable_materials.join(", ")}</p></div><div><p className="text-xs font-semibold">Validation status</p><p className="muted mt-1 text-sm">{pretty(m.validation_status)}</p></div><div><p className="text-xs font-semibold">Instrument platform</p><p className="muted mt-1 text-sm">{m.instrument_platform||"Not specified"}</p></div></div>{m.sample_requirements&&<p className="muted mt-3 text-sm"><b className="text-slate-200">Sample context:</b> {m.sample_requirements}</p>}{m.method_scope&&<p className="muted mt-2 text-sm"><b className="text-slate-200">Scope:</b> {m.method_scope}</p>}{m.reference_standard&&<p className="muted mt-2 text-sm"><b className="text-slate-200">Reference:</b> {m.reference_standard}</p>}<div className="mt-4 rounded-lg border border-amber-400/20 bg-amber-400/5 p-3"><p className="text-xs font-semibold text-amber-200">Limitations</p><p className="muted mt-1 text-sm">{m.limitations}</p></div><div className="mt-4">{m.sources.map((s,i)=><a key={i} href={s.source_url} target="_blank" rel="noreferrer" className="mt-1 block break-all text-xs text-emerald-300 underline">{s.source_name} · {s.source_identifier} ↗</a>)}</div></article>)}</div>}</section>
    {!token?<section className="panel mt-10 max-w-xl p-6"><h2 className="text-xl font-semibold">Researcher / curator sign in</h2><form onSubmit={signIn} className="mt-4 space-y-3"><label className="block"><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="block"><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Sign in</button></form></section>:<section className="mt-10 grid gap-6 lg:grid-cols-2"><div className="panel p-6"><h2 className="text-xl font-semibold">Submit analytical method</h2><p className="muted mt-2 text-xs">Signed in as {role}. Provide a source that supports the method description and intended use.</p><form onSubmit={submit} className="mt-5 space-y-3">{([
      ["method_name","Method name"],["scientific_principle","Scientific principle"],["intended_purpose","Intended purpose"],["applicable_materials","Applicable materials (comma-separated)"],["instrument_platform","Instrument platform (optional)"],["sample_requirements","Sample requirements / context"],["method_scope","Method scope"],["method_version","Method version"],["reference_standard","Reference standard"],["acceptance_criteria_source","Acceptance criteria source"],["limitations","Limitations"],["source_name","Source name"],["source_identifier","Source identifier (DOI, document ID etc.)"],["source_url","Source URL"],["evidence_scope","What does this source support?"]
    ] as const).map(([key,title])=><label key={key} className="block"><span className={label}>{title}</span>{["scientific_principle","intended_purpose","sample_requirements","method_scope","limitations","evidence_scope"].includes(key)?<textarea className={field} rows={3} required={["scientific_principle","intended_purpose","limitations","evidence_scope"].includes(key)} value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/>:<input className={field} required={["method_name","applicable_materials","source_name","source_identifier","source_url"].includes(key)} value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/>}</label>)}<label className="block"><span className={label}>Method category</span><select className={field} value={form.method_category} onChange={e=>setForm(prev=>({...prev,method_category:e.target.value}))}>{categories.map(c=><option key={c} value={c}>{pretty(c)}</option>)}</select></label><label className="block"><span className={label}>Method classification</span><select className={field} value={form.method_classification} onChange={e=>setForm(prev=>({...prev,method_classification:e.target.value}))}>{["compendial","published","manufacturer_method","in_house","research_use","unknown"].map(v=><option key={v} value={v}>{pretty(v)}</option>)}</select></label><label className="block"><span className={label}>Validation status (must be evidence-supported)</span><select className={field} value={form.validation_status} onChange={e=>setForm(prev=>({...prev,validation_status:e.target.value}))}>{["not_assessed","not_validated","development","partially_validated","validated"].map(v=><option key={v} value={v}>{pretty(v)}</option>)}</select></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit for review</button></form></div>
    <div className="panel p-6"><div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Scientific review queue</h2><button onClick={()=>void loadReviews()} className="text-xs text-emerald-300">Refresh</button></div>{reviews.length===0?<p className="muted mt-4 text-sm">Load your organization's review queue. Curator or reviewer permissions required.</p>:<div className="mt-4 space-y-4">{reviews.map(m=><article key={m.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{m.method_name}</h3><p className="muted mt-1 text-xs">{pretty(m.method_category)} · {pretty(m.method_classification)} · validation: {pretty(m.validation_status)}</p><p className="muted mt-3 text-sm">{m.intended_purpose}</p>{m.sources.map((s,i)=><a key={i} href={s.source_url} target="_blank" rel="noreferrer" className="mt-2 block break-all text-xs text-emerald-300 underline">{s.source_name} · {s.source_identifier} ↗</a>)}{["organization_admin","curator","reviewer"].includes(role)&&<><textarea className={field+" mt-3"} rows={2} value={rationales[m.id]||""} onChange={e=>setRationales(prev=>({...prev,[m.id]:e.target.value}))} placeholder="Review rationale (minimum 20 characters)"/><div className="mt-3 flex flex-wrap gap-2">{(["verified","rejected","needs_changes"] as const).map(d=><button key={d} onClick={()=>void decide(m,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs">{pretty(d)}</button>)}</div></>}</article>)}</div>}</div></section>}
    <section className="panel mt-8 p-5"><h2 className="font-semibold">Important scientific distinction</h2><p className="muted mt-2 text-sm leading-6">Curation review checks whether the record is sufficiently sourced and accurately described. It does not establish method validation, suitability for a specific product, compendial compliance, release acceptance criteria or regulatory approval. Those require separate evidence and qualified assessment. This catalogue is informational and does not replace validated laboratory procedures or controlled SOPs.</p></section>
  </main>;
}

"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Peptide = { id: string; preferred_name: string; peptide_category?: string };
type Method = { id: string; method_name: string; method_category: string; validation_status: string };
type Applicability = {
  id: string; peptide_id: string; peptide_name: string; method_id: string; method_name: string;
  method_category: string; method_classification: string; validation_status: string;
  test_purpose: string; material_form?: string; sample_matrix?: string;
  applicability_rationale: string; evidence_scope: string; limitations: string;
  source_name: string; source_identifier: string; source_url: string;
};
type Review = Applicability & { submitted_by: string };

export default function PeptideMethodApplicabilityPage() {
  const [peptides,setPeptides]=useState<Peptide[]>([]);
  const [methods,setMethods]=useState<Method[]>([]);
  const [items,setItems]=useState<Applicability[]>([]);
  const [reviews,setReviews]=useState<Review[]>([]);
  const [search,setSearch]=useState("");
  const [peptideId,setPeptideId]=useState("");
  const [methodId,setMethodId]=useState("");
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [token,setToken]=useState("");
  const [role,setRole]=useState("");
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [busy,setBusy]=useState(false);
  const [rationales,setRationales]=useState<Record<string,string>>({});
  const [form,setForm]=useState({
    test_purpose:"",material_form:"",sample_matrix:"",applicability_rationale:"",
    evidence_scope:"",limitations:"",source_name:"",source_identifier:"",source_url:""
  });
  const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const label="mb-2 block text-xs text-slate-300";
  const pretty=(value:string)=>value.replaceAll("_"," ");

  async function loadOptions(term="") {
    setBusy(true);setError("");
    try {
      const [p,m]=await Promise.all([
        fetch(API+"/api/v1/peptides?limit=100"+(term.trim()?"&q="+encodeURIComponent(term.trim()):"")),
        fetch(API+"/api/v1/analytical-methods?limit=100")
      ]);
      const pd=await p.json(),md=await m.json();
      if(!p.ok)throw new Error(pd.detail||"Could not load verified peptides.");
      if(!m.ok)throw new Error(md.detail||"Could not load verified methods.");
      setPeptides(pd.items||[]);setMethods(md.items||[]);
      if(!peptideId && pd.items?.length)setPeptideId(pd.items[0].id);
      if(!methodId && md.items?.length)setMethodId(md.items[0].id);
    }catch(e){setError(e instanceof Error?e.message:"Could not load peptide and method records.");}
    finally{setBusy(false);}
  }

  async function loadApplicability(id=peptideId) {
    if(!id)return;
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/applicability?peptide_id="+encodeURIComponent(id));
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Could not load applicability records.");
      setItems(data.items||[]);
    }catch(e){setError(e instanceof Error?e.message:"Applicability search failed.");}
  }

  async function signIn(e:FormEvent) {
    e.preventDefault();setBusy(true);setError("");
    try {
      const response=await fetch(API+"/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Sign in failed.");
      setToken(data.access_token);setRole(data.user.role);setPassword("");setNotice("Signed in as "+data.user.role+".");
    }catch(e){setError(e instanceof Error?e.message:"Sign in failed.");}
    finally{setBusy(false);}
  }

  async function submit(e:FormEvent) {
    e.preventDefault();if(!token)return;setBusy(true);setError("");setNotice("");
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/applicability",{
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},
        body:JSON.stringify({...form,peptide_id:peptideId,method_id:methodId})
      });
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Applicability submission failed.");
      setNotice("Peptide-specific method applicability submitted for independent review.");
      setForm({test_purpose:"",material_form:"",sample_matrix:"",applicability_rationale:"",evidence_scope:"",limitations:"",source_name:"",source_identifier:"",source_url:""});
      await loadReviews();
    }catch(e){setError(e instanceof Error?e.message:"Submission failed.");}
    finally{setBusy(false);}
  }

  async function loadReviews() {
    if(!token)return;
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/applicability/reviews",{headers:{Authorization:"Bearer "+token}});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Review queue unavailable.");
      setReviews(data.items||[]);
    }catch(e){setError(e instanceof Error?e.message:"Review queue unavailable.");}
  }

  async function decide(item:Review,decision:"verified"|"rejected"|"needs_changes") {
    const rationale=(rationales[item.id]||"").trim();
    if(rationale.length<20){setError("Review rationale must contain at least 20 characters.");return;}
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/applicability/"+item.id+"/decisions",{
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},
        body:JSON.stringify({decision,rationale})
      });
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Review decision failed.");
      setNotice("Applicability review recorded: "+pretty(data.review_status)+".");
      setRationales(prev=>({...prev,[item.id]:""}));await loadReviews();if(decision==="verified")await loadApplicability();
    }catch(e){setError(e instanceof Error?e.message:"Review decision failed.");}
  }

  useEffect(()=>{void loadOptions();},[]);
  useEffect(()=>{void loadApplicability();},[peptideId]);

  return <main className="container min-h-screen py-10">
    <Link href="/analytical-methods" className="text-sm text-emerald-300">← Analytical method catalogue</Link>
    <header className="mt-8 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">PEPTIDE-SPECIFIC TEST APPLICABILITY</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Method applicability matrix</h1>
      <p className="muted mt-4 leading-7">Connect a verified analytical method to a verified peptide only when a source supports the stated purpose, material form and sample matrix. This is evidence mapping, not a universal test panel or executable laboratory protocol.</p>
    </header>
    {error&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {notice&&<div role="status" className="mt-5 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{notice}</div>}
    <section className="panel mt-7 p-5">
      <form onSubmit={e=>{e.preventDefault();void loadOptions(search);}} className="grid gap-3 md:grid-cols-[1fr_auto]">
        <input className={field} value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search verified peptides by name or alias"/>
        <button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Find peptides</button>
      </form>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label><span className={label}>Verified peptide</span><select className={field} value={peptideId} onChange={e=>setPeptideId(e.target.value)}>{peptides.map(p=><option key={p.id} value={p.id}>{p.preferred_name}{p.peptide_category?" · "+p.peptide_category:""}</option>)}</select></label>
        <label><span className={label}>Verified analytical method</span><select className={field} value={methodId} onChange={e=>setMethodId(e.target.value)}>{methods.map(m=><option key={m.id} value={m.id}>{m.method_name} · {pretty(m.validation_status)}</option>)}</select></label>
      </div>
      {(!peptides.length||!methods.length)&&<p className="muted mt-3 text-xs">A peptide-specific applicability record requires both a verified peptide and a verified method. Populate and curate those catalogues first.</p>}
    </section>
    <section className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-2xl font-semibold">Verified applicability evidence</h2><button onClick={()=>void loadApplicability()} className="text-sm text-emerald-300">Refresh</button></div>
      {items.length===0?<div className="panel mt-4 p-6 text-sm muted">No verified applicability evidence is recorded for this peptide yet. This does not mean that no suitable analytical methods exist.</div>:<div className="mt-4 grid gap-4 lg:grid-cols-2">{items.map(item=><article key={item.id} className="panel p-5"><h3 className="font-semibold">{item.method_name}</h3><p className="muted mt-1 text-xs">{pretty(item.method_category)} · {pretty(item.method_classification)} · method validation: {pretty(item.validation_status)}</p><p className="mt-3 text-sm"><b>Test purpose:</b> {item.test_purpose}</p><p className="muted mt-2 text-sm"><b className="text-slate-200">Material / matrix:</b> {item.material_form||"Not specified"} · {item.sample_matrix||"Not specified"}</p><p className="muted mt-3 text-sm leading-6">{item.applicability_rationale}</p><div className="mt-3 rounded-lg border border-amber-400/20 p-3"><p className="text-xs font-semibold text-amber-200">Limitations</p><p className="muted mt-1 text-sm">{item.limitations}</p></div><a className="mt-3 block break-all text-xs text-emerald-300 underline" href={item.source_url} target="_blank" rel="noreferrer">{item.source_name} · {item.source_identifier}</a></article>)}</div>}
    </section>
    {!token?<section className="panel mt-10 max-w-xl p-6"><h2 className="text-xl font-semibold">Researcher / curator sign in</h2><form onSubmit={signIn} className="mt-4 space-y-3"><label><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Sign in</button></form></section>:<section className="mt-10 grid gap-6 lg:grid-cols-2">
      <div className="panel p-6"><h2 className="text-xl font-semibold">Submit applicability evidence</h2><p className="muted mt-2 text-xs">Signed in as {role}. The peptide and method must already be curator-verified.</p><form onSubmit={submit} className="mt-4 space-y-3">
        {([
          ["test_purpose","Test purpose"],["material_form","Peptide material form"],["sample_matrix","Sample matrix"],["applicability_rationale","Why does this source support applicability?"],["evidence_scope","What does the source actually support?"],["limitations","Limitations"],["source_name","Source name"],["source_identifier","Source identifier (DOI / document ID)"],["source_url","Source URL"]
        ] as const).map(([key,title])=><label key={key} className="block"><span className={label}>{title}</span>{["applicability_rationale","evidence_scope","limitations"].includes(key)?<textarea className={field} rows={3} required value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/>:<input className={field} required={["test_purpose","applicability_rationale","evidence_scope","limitations","source_name","source_identifier","source_url"].includes(key)} value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/>}</label>)}
        <button disabled={busy||!peptideId||!methodId} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit for review</button>
      </form></div>
      <div className="panel p-6"><div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Applicability review queue</h2><button onClick={()=>void loadReviews()} className="text-xs text-emerald-300">Refresh</button></div>{reviews.length===0?<p className="muted mt-4 text-sm">Load your organization's queue. Curator or reviewer permissions required.</p>:<div className="mt-4 space-y-4">{reviews.map(item=><article key={item.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{item.peptide_name} · {item.method_name}</h3><p className="muted mt-2 text-sm">{item.test_purpose}</p><a href={item.source_url} target="_blank" rel="noreferrer" className="mt-2 block break-all text-xs text-emerald-300 underline">{item.source_name} · {item.source_identifier}</a>{["organization_admin","curator","reviewer"].includes(role)&&<><textarea className={field+" mt-3"} rows={2} value={rationales[item.id]||""} onChange={e=>setRationales(prev=>({...prev,[item.id]:e.target.value}))} placeholder="Review rationale (minimum 20 characters)"/><div className="mt-3 flex flex-wrap gap-2">{(["verified","rejected","needs_changes"] as const).map(d=><button key={d} onClick={()=>void decide(item,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs">{pretty(d)}</button>)}</div></>}</article>)}</div>}</div>
    </section>}
    <section className="panel mt-8 p-5"><h2 className="font-semibold">Scientific interpretation</h2><p className="muted mt-2 text-sm leading-6">A verified applicability record means the evidence was reviewed for the stated peptide, method, material form and matrix. It does not establish universal method validation, compendial compliance, acceptance criteria or product release suitability. Check the original source and the method's separate validation status before use.</p></section>
  </main>;
}

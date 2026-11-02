"use client";

import { useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Item = {
  id:string;catalogue_code:string;test_name:string;quality_attribute:string;test_intent:string;
  candidate_method_families:string[];material_considerations:string;interpretation_limitations:string;
  organization_review_status?:string|null;organization_review_rationale?:string|null;
  sources:{source_name:string;source_identifier:string;source_url:string;evidence_scope:string}[];
};
export default function TestCatalogueReviewPage() {
  const [email,setEmail]=useState("");const [password,setPassword]=useState("");
  const [token,setToken]=useState("");const [role,setRole]=useState("");
  const [items,setItems]=useState<Item[]>([]);const [rationales,setRationales]=useState<Record<string,string>>({});
  const [error,setError]=useState("");const [notice,setNotice]=useState("");const [busy,setBusy]=useState(false);
  const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const pretty=(v:string)=>v.replaceAll("_"," ");
  async function load(accessToken=token) {
    if(!accessToken)return;setBusy(true);setError("");
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/test-catalogue/reviews",{headers:{Authorization:"Bearer "+accessToken}});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Review queue unavailable.");
      setItems(data.items||[]);
    }catch(e){setError(e instanceof Error?e.message:"Could not load review queue.");}
    finally{setBusy(false);}
  }
  async function signIn(e:React.FormEvent) {
    e.preventDefault();setBusy(true);setError("");setNotice("");
    try {
      const response=await fetch(API+"/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Sign in failed.");
      setToken(data.access_token);setRole(data.user.role);setPassword("");setNotice("Signed in as "+data.user.role+".");await load(data.access_token);
    }catch(e){setError(e instanceof Error?e.message:"Sign in failed.");}
    finally{setBusy(false);}
  }
  async function decide(item:Item,decision:"verified"|"rejected"|"needs_changes") {
    const rationale=(rationales[item.id]||"").trim();if(rationale.length<20){setError("Rationale must contain at least 20 characters.");return;}
    setError("");setNotice("");
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/test-catalogue/"+item.id+"/decisions",{
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},
        body:JSON.stringify({decision,rationale})
      });
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Decision could not be recorded.");
      setNotice("Organization review recorded: "+pretty(data.decision)+". Shared catalogue status remains draft.");
      setRationales(prev=>({...prev,[item.id]:""}));await load();
    }catch(e){setError(e instanceof Error?e.message:"Review decision failed.");}
  }
  return <main className="container min-h-screen py-10">
    <Link href="/analytical-methods/test-catalogue" className="text-sm text-emerald-300">← Test catalogue</Link>
    <header className="mt-8 max-w-3xl"><p className="accent text-xs tracking-[.2em]">SCIENTIFIC CURATION WORKSPACE</p><h1 className="mt-3 text-4xl font-semibold">Review test definitions</h1><p className="muted mt-4 leading-7">Review whether the reference entry accurately reflects its cited source, scope and limitations. Your decision is recorded for your organization only; it does not globally verify the shared catalogue.</p></header>
    {error&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {notice&&<div role="status" className="mt-5 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{notice}</div>}
    {!token?<section className="panel mt-7 max-w-xl p-6"><h2 className="text-xl font-semibold">Curator / reviewer sign in</h2><form onSubmit={signIn} className="mt-4 space-y-3"><label className="block"><span className="mb-2 block text-xs text-slate-300">Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="block"><span className="mb-2 block text-xs text-slate-300">Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Sign in</button></form></section>:<section className="mt-7"><div className="flex items-center justify-between gap-3"><p className="muted text-sm">Signed in as {role} · {items.length} entries</p><button onClick={()=>void load()} className="text-sm text-emerald-300">Refresh</button></div>{items.length===0?<div className="panel mt-4 p-6 text-sm muted">No catalogue entries available for review.</div>:<div className="mt-4 space-y-4">{items.map(item=><article key={item.id} className="panel p-5"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="accent text-xs">{item.catalogue_code} · {pretty(item.quality_attribute)}</p><h2 className="mt-1 text-lg font-semibold">{item.test_name}</h2></div><span className="rounded-full border border-slate-600 px-3 py-1 text-xs">{item.organization_review_status?pretty(item.organization_review_status):"not reviewed by organization"}</span></div><p className="mt-3 text-sm leading-6">{item.test_intent}</p><p className="muted mt-3 text-sm"><b className="text-slate-200">Candidate method families:</b> {item.candidate_method_families.join(", ")||"Not specified"}</p><p className="muted mt-2 text-sm"><b className="text-slate-200">Material considerations:</b> {item.material_considerations}</p><p className="muted mt-2 text-sm"><b className="text-slate-200">Limitations:</b> {item.interpretation_limitations}</p><div className="mt-3">{item.sources.map(s=><div key={s.source_identifier} className="mt-2"><p className="muted text-xs">{s.evidence_scope}</p><a className="break-all text-xs text-emerald-300 underline" href={s.source_url} target="_blank" rel="noreferrer">{s.source_name} · {s.source_identifier} ↗</a></div>)}</div><textarea className={field+" mt-4"} rows={3} placeholder="Review rationale (minimum 20 characters)" value={rationales[item.id]||""} onChange={e=>setRationales(prev=>({...prev,[item.id]:e.target.value}))}/><div className="mt-3 flex flex-wrap gap-2">{(["verified","needs_changes","rejected"] as const).map(d=><button key={d} onClick={()=>void decide(item,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs hover:border-emerald-400">{pretty(d)}</button>)}</div></article>)}</div>}</section>}
    <div className="panel mt-8 p-5"><h2 className="font-semibold">Review boundary</h2><p className="muted mt-2 text-sm leading-6">A source link is not proof that every statement is supported. Review each field against the cited material. These organization-level editorial decisions are not regulatory determinations, method validation or laboratory qualification.</p></div>
  </main>;
}

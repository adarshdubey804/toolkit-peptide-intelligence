"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Vendor = { id: string; legal_name: string; website_url: string; country_code: string; vendor_type: string; verification_status: string; services: { service_name: string; capability_description: string }[]; certifications: { certification_name: string; issuing_body?: string; scope?: string; valid_until?: string; verification_status: string }[] };
type Review = { id: string; legal_name: string; website_url: string; country_code: string; vendor_type: string; review_status: string; sources: { source_name: string; source_identifier: string; source_url: string; evidence_scope: string }[] };

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [q, setQ] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [role, setRole] = useState("");
  const [form, setForm] = useState({ legal_name: "", website_url: "", country_code: "", vendor_type: "analytical_laboratory", source_name: "", source_identifier: "", source_url: "", evidence_scope: "" });
  const [rationale, setRationale] = useState<Record<string,string>>({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const field = "w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const label = "mb-2 block text-xs text-slate-300";

  async function loadDirectory() {
    setBusy(true); setError("");
    try {
      const response = await fetch(API + "/api/v1/vendors?q=" + encodeURIComponent(q));
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Directory could not be loaded.");
      setVendors(data.items || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Directory request failed."); }
    finally { setBusy(false); }
  }

  async function signIn(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch(API + "/api/v1/auth/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({email,password}) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Sign in failed.");
      setToken(data.access_token); setRole(data.user.role); setPassword("");
      setMessage("Signed in as " + data.user.role + ".");
    } catch (e) { setError(e instanceof Error ? e.message : "Sign in failed."); }
    finally { setBusy(false); }
  }

  async function submitVendor(e: FormEvent) {
    e.preventDefault(); if (!token) return; setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch(API + "/api/v1/vendors", { method:"POST", headers:{"Content-Type":"application/json",Authorization:"Bearer "+token}, body:JSON.stringify(form) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Vendor submission failed.");
      setMessage("Vendor submitted for curator review. It is not yet visible in the public directory.");
      setForm({ legal_name:"", website_url:"", country_code:"", vendor_type:"analytical_laboratory", source_name:"", source_identifier:"", source_url:"", evidence_scope:"" });
      await loadReviews();
    } catch (e) { setError(e instanceof Error ? e.message : "Vendor submission failed."); }
    finally { setBusy(false); }
  }

  async function loadReviews() {
    if (!token) return;
    try {
      const response = await fetch(API + "/api/v1/vendors/reviews", {headers:{Authorization:"Bearer "+token}});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Review queue unavailable.");
      setReviews(data.items || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Queue request failed."); }
  }

  async function decide(vendor: Review, decision: "verified"|"rejected"|"needs_changes") {
    const why = (rationale[vendor.id] || "").trim();
    if (why.length < 20) { setError("Please provide a rationale of at least 20 characters."); return; }
    try {
      const response = await fetch(API + "/api/v1/vendors/" + vendor.id + "/decisions", {method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({decision,rationale:why})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Decision failed.");
      setMessage("Vendor review decision recorded: " + decision + ".");
      setRationale(prev=>({...prev,[vendor.id]:""}));
      await loadReviews();
      if (decision === "verified") await loadDirectory();
    } catch(e) { setError(e instanceof Error ? e.message : "Decision failed."); }
  }

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-8 max-w-3xl"><p className="accent text-xs tracking-[.2em]">INDUSTRY & LABORATORY INTELLIGENCE</p><h1 className="mt-3 text-4xl font-semibold md:text-5xl">Vendor & laboratory directory</h1><p className="muted mt-4 leading-7">Discover curator-verified organizations and submit source-backed vendor or laboratory records for review. Capability and certification claims are shown only when explicitly evidenced and reviewed.</p></header>
    <section className="panel mt-7 p-5"><form onSubmit={e=>{e.preventDefault();void loadDirectory();}} className="flex flex-wrap gap-3"><input className={field+" min-w-0 flex-1"} value={q} onChange={e=>setQ(e.target.value)} placeholder="Search verified vendor or laboratory name"/><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Search directory</button></form><p className="muted mt-3 text-xs">Only vendor identities reviewed and marked verified are included. An empty result does not mean no provider exists.</p></section>
    {error && <div role="alert" className="mt-4 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {message && <div role="status" className="mt-4 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{message}</div>}
    <section className="mt-7"><div className="flex items-center justify-between"><h2 className="text-2xl font-semibold">Verified directory</h2><button onClick={()=>void loadDirectory()} className="text-sm text-emerald-300">Refresh</button></div>{vendors.length===0?<div className="panel mt-4 p-7 text-sm muted">No verified vendors are currently listed. Submit a source-backed record or refresh the directory.</div>:<div className="mt-4 grid gap-4 md:grid-cols-2">{vendors.map(v=><article key={v.id} className="panel p-5"><div className="flex items-start justify-between gap-3"><div><h3 className="text-lg font-semibold">{v.legal_name}</h3><p className="muted mt-1 text-xs">{v.vendor_type.replaceAll("_"," ")} · {v.country_code}</p></div><span className="rounded-full border border-emerald-400/40 px-3 py-1 text-xs text-emerald-200">Verified</span></div><a className="mt-3 inline-block text-sm text-emerald-300 underline" href={v.website_url} target="_blank" rel="noreferrer">Official website ↗</a>{v.services.length>0&&<div className="mt-4"><p className="text-xs font-semibold">Reviewed services</p>{v.services.map((s,i)=><p key={i} className="muted mt-2 text-sm">{s.service_name}: {s.capability_description}</p>)}</div>}{v.certifications.length>0&&<div className="mt-4"><p className="text-xs font-semibold">Certification records</p>{v.certifications.map((c,i)=><p key={i} className="muted mt-2 text-sm">{c.certification_name} · {c.issuing_body || "Issuer not specified"} · {c.verification_status}</p>)}</div>}</article>)}</div>}</section>
    {!token?<section className="panel mt-10 max-w-xl p-6"><h2 className="text-xl font-semibold">Sign in to submit a provider</h2><form onSubmit={signIn} className="mt-4 space-y-3"><label className="block"><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="block"><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Sign in</button></form></section>:<section className="mt-10 grid gap-6 lg:grid-cols-2"><div className="panel p-6"><h2 className="text-xl font-semibold">Submit provider record</h2><p className="muted mt-2 text-xs">Signed in as {role}. Records remain in review until an authorized curator verifies them.</p><form onSubmit={submitVendor} className="mt-5 space-y-3">{([["legal_name","Legal name"],["website_url","Official website URL"],["country_code","Country code (ISO 2-letter)"],["source_name","Evidence source name"],["source_identifier","Source record identifier"],["source_url","Original source URL"],["evidence_scope","What does this source support?"]] as const).map(([key,title])=><label key={key} className="block"><span className={label}>{title}</span><input className={field} required value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/></label>)}<label className="block"><span className={label}>Provider type</span><select className={field} value={form.vendor_type} onChange={e=>setForm(prev=>({...prev,vendor_type:e.target.value}))}><option value="analytical_laboratory">Analytical laboratory</option><option value="peptide_manufacturer">Peptide manufacturer</option><option value="cdmo">CDMO</option><option value="cro">CRO</option><option value="research_reagent_supplier">Research reagent supplier</option><option value="other">Other</option></select></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit for review</button></form></div>
    <div className="panel p-6"><div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Vendor review queue</h2><button onClick={()=>void loadReviews()} className="text-xs text-emerald-300">Refresh</button></div>{reviews.length===0?<p className="muted mt-4 text-sm">Load the queue to inspect records submitted by your organization. Reviewer permissions required.</p>:<div className="mt-4 space-y-4">{reviews.map(v=><article key={v.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{v.legal_name}</h3><p className="muted mt-1 text-xs">{v.vendor_type} · {v.country_code}</p>{v.sources.map((s,i)=><a key={i} className="mt-2 block break-all text-xs text-emerald-300 underline" href={s.source_url} target="_blank" rel="noreferrer">{s.source_name}: {s.source_identifier} ↗</a>)}{["organization_admin","curator","reviewer"].includes(role)&&<><textarea className={field+" mt-3"} rows={2} value={rationale[v.id]||""} onChange={e=>setRationale(prev=>({...prev,[v.id]:e.target.value}))} placeholder="Review rationale (minimum 20 characters)"/><div className="mt-3 flex flex-wrap gap-2">{(["verified","rejected","needs_changes"] as const).map(d=><button key={d} onClick={()=>void decide(v,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs">{d.replace("_"," ")}</button>)}</div></>}</article>)}</div>}</div></section>}
    <div className="panel mt-8 p-5"><h2 className="font-semibold">Verification boundary</h2><p className="muted mt-2 text-sm leading-6">A vendor identity review does not certify a facility, service, quality system or regulatory compliance. Certifications require separate evidence of issuing body, site, scope, validity dates and independent verification. This initial directory records vendor-level source evidence only.</p></div>
  </main>;
}

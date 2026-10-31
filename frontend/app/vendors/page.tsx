"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Vendor = { id: string; legal_name: string; website_url: string; country_code: string; vendor_type: string; verification_status: string; services: { service_name: string; capability_description: string }[]; certifications: { certification_name: string; issuing_body?: string; scope?: string; valid_until?: string; verification_status: string }[] };
type Review = { id: string; legal_name: string; website_url: string; country_code: string; vendor_type: string; review_status: string; sources: { source_name: string; source_identifier: string; source_url: string; evidence_scope: string }[] };
type ServiceReview = { id: string; vendor_id: string; legal_name: string; service_name: string; capability_description: string; source_name?: string; source_identifier?: string; source_url?: string };
type ServiceOption = { service_id: string; service_name: string; capability_description: string };
type PeptideOption = { id: string; preferred_name: string };
type MethodOption = { id: string; method_name: string };
type LinkReview = { id: string; service_id: string; legal_name: string; service_name: string; relationship_type: string; evidence_scope: string; limitations: string; peptide_id?: string; peptide_name?: string; method_id?: string; method_name?: string; source_name: string; source_identifier: string; source_url: string };

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [serviceReviews, setServiceReviews] = useState<ServiceReview[]>([]);
  const [serviceRationale, setServiceRationale] = useState<Record<string,string>>({});
  const [capabilityOptions, setCapabilityOptions] = useState<ServiceOption[]>([]);
  const [peptideOptions, setPeptideOptions] = useState<PeptideOption[]>([]);
  const [methodOptions, setMethodOptions] = useState<MethodOption[]>([]);
  const [linkReviews, setLinkReviews] = useState<LinkReview[]>([]);
  const [linkRationales, setLinkRationales] = useState<Record<string,string>>({});
  const [linkForm, setLinkForm] = useState({ service_id:"", relationship_type:"peptide_supply", peptide_id:"", method_id:"", evidence_scope:"", limitations:"", source_name:"", source_identifier:"", source_url:"" });
  const [serviceForm, setServiceForm] = useState({ vendor_id: "", service_name: "", capability_description: "", source_name: "", source_identifier: "", source_url: "" });
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

  async function submitService(e: FormEvent) {
    e.preventDefault(); if (!token) return;
    if (!serviceForm.vendor_id) { setError("Load the verified directory and select a vendor first."); return; }
    setBusy(true); setError(""); setMessage("");
    try {
      const { vendor_id, ...payload } = serviceForm;
      const response = await fetch(API + "/api/v1/vendors/" + vendor_id + "/services", {
        method:"POST", headers:{"Content-Type":"application/json",Authorization:"Bearer "+token}, body:JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Service submission failed.");
      setMessage("Service capability submitted for independent review; it will appear only after verification.");
      setServiceForm({vendor_id,service_name:"",capability_description:"",source_name:"",source_identifier:"",source_url:""});
      await loadServiceReviews();
    } catch (e) { setError(e instanceof Error ? e.message : "Service submission failed."); }
    finally { setBusy(false); }
  }

  async function loadServiceReviews() {
    if (!token) return;
    try {
      const response = await fetch(API + "/api/v1/vendors/services/reviews", {headers:{Authorization:"Bearer "+token}});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Service review queue unavailable.");
      setServiceReviews(data.items || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Service queue request failed."); }
  }

  async function decideService(service: ServiceReview, decision: "verified"|"rejected"|"needs_changes") {
    const why = (serviceRationale[service.id] || "").trim();
    if (why.length < 20) { setError("Please provide a service review rationale of at least 20 characters."); return; }
    try {
      const response = await fetch(API + "/api/v1/vendors/services/" + service.id + "/decisions", {
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({decision,rationale:why})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Service decision failed.");
      setMessage("Service review decision recorded: " + decision + ".");
      setServiceRationale(prev=>({...prev,[service.id]:""}));
      await loadServiceReviews();
      if (decision === "verified") await loadDirectory();
    } catch (e) { setError(e instanceof Error ? e.message : "Service decision failed."); }
  }

  async function loadLinkOptions(vendorId: string) {
    if (!token || !vendorId) return;
    try {
      const [capRes, pepRes, methodRes] = await Promise.all([
        fetch(API + "/api/v1/vendors/" + vendorId + "/capabilities", {headers:{Authorization:"Bearer "+token}}),
        fetch(API + "/api/v1/peptides?limit=100&offset=0"),
        fetch(API + "/api/v1/analytical-methods")
      ]);
      const [capData, pepData, methodData] = await Promise.all([capRes.json(),pepRes.json(),methodRes.json()]);
      if (!capRes.ok) throw new Error(capData.detail || "Verified vendor services could not be loaded.");
      if (!pepRes.ok) throw new Error(pepData.detail || "Verified peptide catalogue unavailable.");
      if (!methodRes.ok) throw new Error(methodData.detail || "Verified method catalogue unavailable.");
      setCapabilityOptions(capData.items || []);
      setPeptideOptions(pepData.items || []);
      setMethodOptions(methodData.items || []);
      setLinkForm(prev=>({...prev,service_id:""}));
    } catch(e) { setError(e instanceof Error ? e.message : "Capability link options failed."); }
  }

  async function submitEvidenceLink(e: FormEvent) {
    e.preventDefault(); if (!token || !linkForm.service_id) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const payload = {
        relationship_type: linkForm.relationship_type,
        peptide_id: linkForm.peptide_id || null,
        method_id: linkForm.method_id || null,
        evidence_scope: linkForm.evidence_scope,
        limitations: linkForm.limitations,
        source_name: linkForm.source_name,
        source_identifier: linkForm.source_identifier,
        source_url: linkForm.source_url
      };
      const response = await fetch(API + "/api/v1/vendors/services/" + linkForm.service_id + "/evidence-links", {
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Capability evidence submission failed.");
      setMessage("Source-backed vendor capability relationship submitted for independent review.");
      setLinkForm(prev=>({...prev,peptide_id:"",method_id:"",evidence_scope:"",limitations:"",source_name:"",source_identifier:"",source_url:""}));
      await loadLinkReviews();
    } catch(e) { setError(e instanceof Error ? e.message : "Capability evidence submission failed."); }
    finally { setBusy(false); }
  }

  async function loadLinkReviews() {
    if (!token) return;
    try {
      const response = await fetch(API + "/api/v1/vendors/service-evidence-links/reviews", {headers:{Authorization:"Bearer "+token}});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Capability evidence review queue unavailable.");
      setLinkReviews(data.items || []);
    } catch(e) { setError(e instanceof Error ? e.message : "Capability review queue failed."); }
  }

  async function decideEvidenceLink(item: LinkReview, decision: "verified"|"rejected"|"needs_changes") {
    const why = (linkRationales[item.id] || "").trim();
    if (why.length < 20) { setError("Capability review rationale must contain at least 20 characters."); return; }
    try {
      const response = await fetch(API + "/api/v1/vendors/service-evidence-links/" + item.id + "/decisions", {
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({decision,rationale:why})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Capability evidence decision failed.");
      setMessage("Capability relationship review recorded: " + decision + ".");
      setLinkRationales(prev=>({...prev,[item.id]:""}));
      await loadLinkReviews();
      if (decision === "verified") await loadDirectory();
    } catch(e) { setError(e instanceof Error ? e.message : "Capability evidence decision failed."); }
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
    <section className="mt-7"><div className="flex items-center justify-between"><h2 className="text-2xl font-semibold">Verified directory</h2><button onClick={()=>void loadDirectory()} className="text-sm text-emerald-300">Refresh</button></div>{vendors.length===0?<div className="panel mt-4 p-7 text-sm muted">No verified vendors are currently listed. Submit a source-backed record or refresh the directory.</div>:<div className="mt-4 grid gap-4 md:grid-cols-2">{vendors.map(v=><article key={v.id} className="panel p-5"><div className="flex items-start justify-between gap-3"><div><h3 className="text-lg font-semibold">{v.legal_name}</h3><p className="muted mt-1 text-xs">{v.vendor_type.replaceAll("_"," ")} · {v.country_code}</p></div><span className="rounded-full border border-emerald-400/40 px-3 py-1 text-xs text-emerald-200">Verified</span></div><a className="mt-3 inline-block text-sm text-emerald-300 underline" href={v.website_url} target="_blank" rel="noreferrer">Official website ↗</a><Link className="ml-4 inline-block text-sm text-emerald-300 underline" href={"/vendors/"+v.id+"/capabilities"}>Verified peptide & method capabilities ↗</Link>{v.services.length>0&&<div className="mt-4"><p className="text-xs font-semibold">Reviewed services</p>{v.services.map((s,i)=><p key={i} className="muted mt-2 text-sm">{s.service_name}: {s.capability_description}</p>)}</div>}{v.certifications.length>0&&<div className="mt-4"><p className="text-xs font-semibold">Certification records</p>{v.certifications.map((c,i)=><p key={i} className="muted mt-2 text-sm">{c.certification_name} · {c.issuing_body || "Issuer not specified"} · {c.verification_status}</p>)}</div>}</article>)}</div>}</section>
    {!token?<section className="panel mt-10 max-w-xl p-6"><h2 className="text-xl font-semibold">Sign in to submit a provider</h2><form onSubmit={signIn} className="mt-4 space-y-3"><label className="block"><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="block"><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Sign in</button></form></section>:<><section className="mt-10 grid gap-6 lg:grid-cols-2"><div className="panel p-6"><h2 className="text-xl font-semibold">Submit provider record</h2><p className="muted mt-2 text-xs">Signed in as {role}. Records remain in review until an authorized curator verifies them.</p><form onSubmit={submitVendor} className="mt-5 space-y-3">{([["legal_name","Legal name"],["website_url","Official website URL"],["country_code","Country code (ISO 2-letter)"],["source_name","Evidence source name"],["source_identifier","Source record identifier"],["source_url","Original source URL"],["evidence_scope","What does this source support?"]] as const).map(([key,title])=><label key={key} className="block"><span className={label}>{title}</span><input className={field} required value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/></label>)}<label className="block"><span className={label}>Provider type</span><select className={field} value={form.vendor_type} onChange={e=>setForm(prev=>({...prev,vendor_type:e.target.value}))}><option value="analytical_laboratory">Analytical laboratory</option><option value="peptide_manufacturer">Peptide manufacturer</option><option value="cdmo">CDMO</option><option value="cro">CRO</option><option value="research_reagent_supplier">Research reagent supplier</option><option value="other">Other</option></select></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit for review</button></form></div>
    <div className="panel p-6"><div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Vendor review queue</h2><button onClick={()=>void loadReviews()} className="text-xs text-emerald-300">Refresh</button></div>{reviews.length===0?<p className="muted mt-4 text-sm">Load the queue to inspect records submitted by your organization. Reviewer permissions required.</p>:<div className="mt-4 space-y-4">{reviews.map(v=><article key={v.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{v.legal_name}</h3><p className="muted mt-1 text-xs">{v.vendor_type} · {v.country_code}</p>{v.sources.map((s,i)=><a key={i} className="mt-2 block break-all text-xs text-emerald-300 underline" href={s.source_url} target="_blank" rel="noreferrer">{s.source_name}: {s.source_identifier} ↗</a>)}{["organization_admin","curator","reviewer"].includes(role)&&<><textarea className={field+" mt-3"} rows={2} value={rationale[v.id]||""} onChange={e=>setRationale(prev=>({...prev,[v.id]:e.target.value}))} placeholder="Review rationale (minimum 20 characters)"/><div className="mt-3 flex flex-wrap gap-2">{(["verified","rejected","needs_changes"] as const).map(d=><button key={d} onClick={()=>void decide(v,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs">{d.replace("_"," ")}</button>)}</div></>}</article>)}</div>}</div></section><section className="mt-8 grid gap-6 lg:grid-cols-2">
      <div className="panel p-6">
        <h2 className="text-xl font-semibold">Submit vendor / laboratory service</h2>
        <p className="muted mt-2 text-xs">Only already verified vendors can receive new service claims. Each capability needs its own source and curator review.</p>
        <button type="button" onClick={()=>void loadDirectory()} className="mt-3 text-xs text-emerald-300">Load verified vendors</button>
        <form onSubmit={submitService} className="mt-4 space-y-3">
          <label className="block"><span className={label}>Verified vendor</span><select className={field} required value={serviceForm.vendor_id} onChange={e=>setServiceForm(prev=>({...prev,vendor_id:e.target.value}))}><option value="">Select a verified vendor</option>{vendors.map(v=><option key={v.id} value={v.id}>{v.legal_name}</option>)}</select></label>
          {([["service_name","Service name"],["capability_description","What capability is evidenced?"],["source_name","Evidence source name"],["source_identifier","Source identifier"],["source_url","Original source URL"]] as const).map(([key,title])=><label key={key} className="block"><span className={label}>{title}</span>{key==="capability_description"?<textarea className={field} rows={3} required value={serviceForm[key]} onChange={e=>setServiceForm(prev=>({...prev,[key]:e.target.value}))}/>:<input className={field} required value={serviceForm[key]} onChange={e=>setServiceForm(prev=>({...prev,[key]:e.target.value}))}/>}</label>)}
          <button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit service for review</button>
        </form>
      </div>
      <div className="panel p-6">
        <div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Service capability review queue</h2><button onClick={()=>void loadServiceReviews()} className="text-xs text-emerald-300">Refresh</button></div>
        {serviceReviews.length===0?<p className="muted mt-4 text-sm">Load the queue to inspect source-backed service claims submitted within your organization. Reviewer permissions required.</p>:<div className="mt-4 space-y-4">{serviceReviews.map(s=><article key={s.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{s.service_name}</h3><p className="muted mt-1 text-xs">{s.legal_name}</p><p className="muted mt-2 text-sm">{s.capability_description}</p>{s.source_url&&<a className="mt-2 block break-all text-xs text-emerald-300 underline" href={s.source_url} target="_blank" rel="noreferrer">{s.source_name}: {s.source_identifier} ↗</a>}{["organization_admin","curator","reviewer"].includes(role)&&<><textarea className={field+" mt-3"} rows={2} value={serviceRationale[s.id]||""} onChange={e=>setServiceRationale(prev=>({...prev,[s.id]:e.target.value}))} placeholder="Review rationale (minimum 20 characters)"/><div className="mt-3 flex flex-wrap gap-2">{(["verified","rejected","needs_changes"] as const).map(d=><button key={d} onClick={()=>void decideService(s,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs">{d.replace("_"," ")}</button>)}</div></>}</article>)}</div>}
      </div>
    </section>
    <section className="mt-8 grid gap-6 lg:grid-cols-2">
      <div className="panel p-6">
        <h2 className="text-xl font-semibold">Link a verified service to a peptide or method</h2>
        <p className="muted mt-2 text-xs">Choose a verified vendor, then load its independently reviewed services and the verified peptide/method catalogues. Each relationship needs its own source and limitations.</p>
        <label className="mt-4 block"><span className={label}>Verified vendor</span><select className={field} value={serviceForm.vendor_id} onChange={e=>{setServiceForm(prev=>({...prev,vendor_id:e.target.value}));void loadLinkOptions(e.target.value);}}><option value="">Select vendor</option>{vendors.map(v=><option key={v.id} value={v.id}>{v.legal_name}</option>)}</select></label>
        <form onSubmit={submitEvidenceLink} className="mt-4 space-y-3">
          <label className="block"><span className={label}>Verified service</span><select required className={field} value={linkForm.service_id} onChange={e=>setLinkForm(prev=>({...prev,service_id:e.target.value}))}><option value="">Select reviewed service</option>{capabilityOptions.map(s=><option key={s.service_id} value={s.service_id}>{s.service_name}</option>)}</select></label>
          <label className="block"><span className={label}>Relationship type</span><select className={field} value={linkForm.relationship_type} onChange={e=>setLinkForm(prev=>({...prev,relationship_type:e.target.value}))}>{[["peptide_supply","Peptide supply"],["peptide_manufacturing","Peptide manufacturing"],["peptide_specific_testing","Peptide-specific testing"],["method_service","Analytical method service"],["formulation_development","Formulation development"]].map(([value,labelText])=><option key={value} value={value}>{labelText}</option>)}</select></label>
          <label className="block"><span className={label}>Verified peptide</span><select className={field} value={linkForm.peptide_id} onChange={e=>setLinkForm(prev=>({...prev,peptide_id:e.target.value}))}><option value="">Select peptide (required for supply/manufacturing/testing/formulation)</option>{peptideOptions.map(p=><option key={p.id} value={p.id}>{p.preferred_name}</option>)}</select></label>
          <label className="block"><span className={label}>Verified analytical method</span><select className={field} value={linkForm.method_id} onChange={e=>setLinkForm(prev=>({...prev,method_id:e.target.value}))}><option value="">Select method (required for method service/testing)</option>{methodOptions.map(m=><option key={m.id} value={m.id}>{m.method_name}</option>)}</select></label>
          {([["evidence_scope","What exactly does the source establish?"],["limitations","Limitations and exclusions"],["source_name","Evidence source name"],["source_identifier","Source identifier"],["source_url","Original source URL"]] as const).map(([key,title])=><label key={key} className="block"><span className={label}>{title}</span>{key==="evidence_scope"||key==="limitations"?<textarea required minLength={key==="limitations"?10:5} rows={2} className={field} value={linkForm[key]} onChange={e=>setLinkForm(prev=>({...prev,[key]:e.target.value}))}/>:<input required className={field} value={linkForm[key]} onChange={e=>setLinkForm(prev=>({...prev,[key]:e.target.value}))}/>}</label>)}
          <button disabled={busy || !linkForm.service_id} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit relationship for review</button>
        </form>
      </div>
      <div className="panel p-6">
        <div className="flex items-center justify-between gap-3"><h2 className="text-xl font-semibold">Capability relationship review queue</h2><button onClick={()=>void loadLinkReviews()} className="text-xs text-emerald-300">Refresh</button></div>
        {linkReviews.length===0?<p className="muted mt-4 text-sm">Load the queue to inspect peptide and method relationships submitted within your organization. Reviewer permissions required.</p>:<div className="mt-4 space-y-4">{linkReviews.map(item=><article key={item.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{item.legal_name} · {item.service_name}</h3><p className="muted mt-1 text-xs">{item.relationship_type.replaceAll("_"," ")}</p>{item.peptide_name&&<p className="mt-2 text-sm">Peptide: {item.peptide_name}</p>}{item.method_name&&<p className="mt-1 text-sm">Method: {item.method_name}</p>}<p className="muted mt-2 text-sm">{item.evidence_scope}</p><p className="muted mt-2 text-xs">Limitations: {item.limitations}</p><a href={item.source_url} target="_blank" rel="noreferrer" className="mt-2 block break-all text-xs text-emerald-300 underline">{item.source_name} · {item.source_identifier} ↗</a>{["organization_admin","curator","reviewer"].includes(role)&&<><textarea className={field+" mt-3"} rows={2} value={linkRationales[item.id]||""} onChange={e=>setLinkRationales(prev=>({...prev,[item.id]:e.target.value}))} placeholder="Review rationale (minimum 20 characters)"/><div className="mt-3 flex flex-wrap gap-2">{(["verified","rejected","needs_changes"] as const).map(d=><button key={d} onClick={()=>void decideEvidenceLink(item,d)} className="rounded-full border border-slate-600 px-3 py-2 text-xs">{d.replace("_"," ")}</button>)}</div></>}</article>)}</div>}
      </div>
    </section></>}
    <div className="panel mt-8 p-5"><h2 className="font-semibold">Verification boundary</h2><p className="muted mt-2 text-sm leading-6">A vendor identity review does not certify a facility, service, quality system or regulatory compliance. Certifications require separate evidence of issuing body, site, scope, validity dates and independent verification. This initial directory records vendor-level source evidence only.</p></div>
  </main>;
}

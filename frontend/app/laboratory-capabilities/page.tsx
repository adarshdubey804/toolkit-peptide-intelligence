"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Method = { id:string; method_name:string; method_category:string; validation_status:string };
type Peptide = { id:string; preferred_name:string };
type VendorOption = { id:string; legal_name:string; sites:{id:string;site_name:string;address:string}[] };
type Service = { service_id:string;service_name:string;capability_description:string;site_id:string;site_name:string;site_address:string };
type Capability = {
  id:string;vendor_id:string;laboratory:string;site_id:string;site_name:string;address:string;country_code:string;
  service_id:string;service_name:string;method_id:string;method_name:string;method_category:string;
  peptide_id?:string|null;peptide_name?:string|null;test_purpose:string;material_form?:string|null;sample_matrix:string;
  instrument_platform?:string|null;sample_requirements?:string|null;storage_shipping_requirements?:string|null;
  evidence_scope:string;limitations:string;source_name:string;source_identifier:string;source_url:string;
};
type Review = Capability & { submitted_by:string };
const blank = {
  test_purpose:"",material_form:"",sample_matrix:"",instrument_platform:"",
  sample_requirements:"",storage_shipping_requirements:"",evidence_scope:"",
  limitations:"",source_name:"",source_identifier:"",source_url:""
};

export default function LaboratoryCapabilitiesPage() {
  const [items,setItems]=useState<Capability[]>([]);
  const [methods,setMethods]=useState<Method[]>([]);
  const [peptides,setPeptides]=useState<Peptide[]>([]);
  const [vendors,setVendors]=useState<VendorOption[]>([]);
  const [services,setServices]=useState<Service[]>([]);
  const [reviews,setReviews]=useState<Review[]>([]);
  const [country,setCountry]=useState("");
  const [vendorId,setVendorId]=useState("");
  const [serviceId,setServiceId]=useState("");
  const [methodId,setMethodId]=useState("");
  const [peptideId,setPeptideId]=useState("");
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [token,setToken]=useState("");
  const [role,setRole]=useState("");
  const [form,setForm]=useState({...blank});
  const [rationales,setRationales]=useState<Record<string,string>>({});
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [busy,setBusy]=useState(false);
  const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const label="mb-2 block text-xs text-slate-300";
  const pretty=(v:string)=>v.replaceAll("_"," ");

  async function loadPublic() {
    setBusy(true);setError("");
    try {
      const params=new URLSearchParams();if(country.trim())params.set("country_code",country.trim().toUpperCase());
      const [c,m,p]=await Promise.all([
        fetch(API+"/api/v1/analytical-methods/laboratory-capabilities?"+params.toString()),
        fetch(API+"/api/v1/analytical-methods?limit=100"),
        fetch(API+"/api/v1/peptides?limit=100")
      ]);
      const [cd,md,pd]=await Promise.all([c.json(),m.json(),p.json()]);
      if(!c.ok)throw new Error(cd.detail||"Laboratory capability records unavailable.");
      if(!m.ok)throw new Error(md.detail||"Analytical methods unavailable.");
      if(!p.ok)throw new Error(pd.detail||"Peptide catalogue unavailable.");
      setItems(cd.items||[]);setMethods(md.items||[]);setPeptides(pd.items||[]);
      if(!methodId&&md.items?.length)setMethodId(md.items[0].id);
    }catch(e){setError(e instanceof Error?e.message:"Could not load laboratory intelligence.");}
    finally{setBusy(false);}
  }

  async function loadOptions(accessToken:string) {
    const response=await fetch(API+"/api/v1/vendors/organization-options",{headers:{Authorization:"Bearer "+accessToken}});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||"Verified laboratory options unavailable.");
    const eligible=(data.items||[]).filter((v:VendorOption)=>v.sites?.length);
    setVendors(eligible);if(eligible.length)setVendorId(eligible[0].id);
  }

  async function loadServices(id:string,accessToken=token) {
    if(!id)return;
    const response=await fetch(API+"/api/v1/vendors/"+id+"/services",{headers:accessToken?{Authorization:"Bearer "+accessToken}:{}});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||"Verified services unavailable.");
    setServices(data.items||[]);setServiceId(data.items?.[0]?.service_id||"");
  }

  async function signIn(e:FormEvent) {
    e.preventDefault();setBusy(true);setError("");setNotice("");
    try {
      const response=await fetch(API+"/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Sign in failed.");
      const accessToken=data.access_token;setToken(accessToken);setRole(data.user.role);setPassword("");
      await loadOptions(accessToken);setNotice("Signed in as "+data.user.role+".");
      if(["organization_admin","curator","reviewer"].includes(data.user.role))await loadReviews(accessToken);
    }catch(e){setError(e instanceof Error?e.message:"Sign in failed.");}
    finally{setBusy(false);}
  }

  async function loadReviews(accessToken=token) {
    if(!accessToken)return;
    const response=await fetch(API+"/api/v1/analytical-methods/laboratory-capabilities/reviews",{headers:{Authorization:"Bearer "+accessToken}});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||"Review queue unavailable.");
    setReviews(data.items||[]);
  }

  async function submit(e:FormEvent) {
    e.preventDefault();if(!token)return;setBusy(true);setError("");setNotice("");
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/laboratory-capabilities",{
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},
        body:JSON.stringify({...form,service_id:serviceId,method_id:methodId,peptide_id:peptideId||null})
      });
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Submission failed.");
      setNotice("Laboratory capability claim submitted for independent review; it is not publicly visible yet.");
      setForm({...blank});await loadReviews();
    }catch(e){setError(e instanceof Error?e.message:"Submission failed.");}
    finally{setBusy(false);}
  }

  async function decide(item:Review,decision:"verified"|"rejected"|"needs_changes") {
    const rationale=(rationales[item.id]||"").trim();if(rationale.length<20){setError("Review rationale must contain at least 20 characters.");return;}
    try {
      const response=await fetch(API+"/api/v1/analytical-methods/laboratory-capabilities/"+item.id+"/decisions",{
        method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},
        body:JSON.stringify({decision,rationale})
      });
      const data=await response.json();if(!response.ok)throw new Error(data.detail||"Decision failed.");
      setNotice("Review decision recorded: "+pretty(data.review_status)+".");
      setRationales(prev=>({...prev,[item.id]:""}));await loadReviews();if(decision==="verified")await loadPublic();
    }catch(e){setError(e instanceof Error?e.message:"Review decision failed.");}
  }

  useEffect(()=>{void loadPublic();},[]);
  useEffect(()=>{if(vendorId)void loadServices(vendorId);},[vendorId]);

  return <main className="container min-h-screen py-10">
    <Link href="/analytical-methods" className="text-sm text-emerald-300">← Analytical methods</Link>
    <header className="mt-8 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">LABORATORY & FACILITY INTELLIGENCE</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Peptide testing capabilities</h1>
      <p className="muted mt-4 leading-7">Explore source-reviewed laboratory claims by facility, analytical method, test purpose and sample matrix. Each record is tied to a verified service and method; peptide-specific claims are separately identified.</p>
    </header>
    {error&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {notice&&<div role="status" className="mt-5 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{notice}</div>}
    <section className="panel mt-7 p-5">
      <form onSubmit={e=>{e.preventDefault();void loadPublic();}} className="grid gap-3 sm:grid-cols-[1fr_auto]">
        <label><span className={label}>Filter by country code (optional)</span><input className={field} maxLength={2} value={country} onChange={e=>setCountry(e.target.value)} placeholder="e.g. IN, CH, US"/></label>
        <button disabled={busy} className="self-end rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Search capabilities</button>
      </form>
      <p className="muted mt-3 text-xs">Only independently reviewed claims are displayed. Empty results do not establish that no laboratory offers the service.</p>
    </section>
    <section className="mt-8">
      <div className="flex items-center justify-between gap-3"><h2 className="text-2xl font-semibold">Reviewed laboratory capabilities</h2><button onClick={()=>void loadPublic()} className="text-sm text-emerald-300">Refresh</button></div>
      {items.length===0?<div className="panel mt-4 p-6 text-sm muted">{busy?"Loading capability records…":"No verified laboratory capability claims are recorded for this filter yet."}</div>:<div className="mt-4 grid gap-4 lg:grid-cols-2">{items.map(item=><article key={item.id} className="panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="text-lg font-semibold">{item.laboratory}</h3><p className="muted mt-1 text-xs">{item.site_name} · {item.country_code}</p></div><span className="rounded-full border border-emerald-400/40 px-3 py-1 text-xs text-emerald-200">Reviewed claim</span></div>
        <p className="muted mt-2 text-sm">{item.address}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2"><div><p className="text-xs font-semibold">Service</p><p className="muted mt-1 text-sm">{item.service_name}</p></div><div><p className="text-xs font-semibold">Analytical method</p><p className="muted mt-1 text-sm">{item.method_name} · {pretty(item.method_category)}</p></div><div><p className="text-xs font-semibold">Test purpose</p><p className="muted mt-1 text-sm">{item.test_purpose}</p></div><div><p className="text-xs font-semibold">Material / matrix</p><p className="muted mt-1 text-sm">{item.material_form||"Not specified"} / {item.sample_matrix}</p></div></div>
        {item.peptide_name&&<p className="mt-3 text-sm"><b>Peptide-specific scope:</b> {item.peptide_name}</p>}
        {item.instrument_platform&&<p className="muted mt-3 text-sm"><b className="text-slate-200">Platform:</b> {item.instrument_platform}</p>}
        {item.sample_requirements&&<p className="muted mt-2 text-sm"><b className="text-slate-200">Sample requirements:</b> {item.sample_requirements}</p>}
        {item.storage_shipping_requirements&&<p className="muted mt-2 text-sm"><b className="text-slate-200">Storage / shipping:</b> {item.storage_shipping_requirements}</p>}
        <div className="mt-4 rounded-lg border border-amber-400/20 p-3"><p className="text-xs font-semibold text-amber-200">Evidence scope and limitations</p><p className="muted mt-1 text-sm">{item.evidence_scope}</p><p className="muted mt-2 text-sm">{item.limitations}</p></div>
        <a className="mt-4 block break-all text-xs text-emerald-300 underline" href={item.source_url} target="_blank" rel="noreferrer">{item.source_name} · {item.source_identifier} ↗</a>
      </article>)}</div>}
    </section>
    {!token?<section className="panel mt-10 max-w-xl p-6"><h2 className="text-xl font-semibold">Researcher / curator sign in</h2><form onSubmit={signIn} className="mt-4 space-y-3"><label><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Sign in</button></form></section>:<section className="mt-10 grid gap-6 lg:grid-cols-2">
      <div className="panel p-6"><h2 className="text-xl font-semibold">Submit a laboratory capability claim</h2><p className="muted mt-2 text-xs">Signed in as {role}. Claims require a verified vendor service, verified facility and verified analytical method. Peptide identity is optional but must be verified if selected.</p>
        <form onSubmit={submit} className="mt-5 space-y-3">
          <label><span className={label}>Verified laboratory</span><select className={field} value={vendorId} onChange={e=>setVendorId(e.target.value)} required><option value="">Select laboratory</option>{vendors.map(v=><option key={v.id} value={v.id}>{v.legal_name} · {v.sites.length} verified site(s)</option>)}</select></label>
          <label><span className={label}>Verified facility service</span><select className={field} value={serviceId} onChange={e=>setServiceId(e.target.value)} required><option value="">Select service</option>{services.map(s=><option key={s.service_id} value={s.service_id}>{s.service_name} · {s.site_name}</option>)}</select></label>
          <label><span className={label}>Verified analytical method</span><select className={field} value={methodId} onChange={e=>setMethodId(e.target.value)} required><option value="">Select method</option>{methods.map(m=><option key={m.id} value={m.id}>{m.method_name} · {pretty(m.validation_status)}</option>)}</select></label>
          <label><span className={label}>Verified peptide (optional)</span><select className={field} value={peptideId} onChange={e=>setPeptideId(e.target.value)}><option value="">General method/service capability only</option>{peptides.map(p=><option key={p.id} value={p.id}>{p.preferred_name}</option>)}</select></label>
          {([
            ["test_purpose","Test purpose"],["material_form","Material form (optional)"],["sample_matrix","Sample matrix"],
            ["instrument_platform","Instrument/platform (optional)"],["sample_requirements","Sample requirements (only if sourced)"],
            ["storage_shipping_requirements","Storage/shipping requirements (only if sourced)"],["evidence_scope","Evidence scope"],
            ["limitations","Limitations"],["source_name","Source name"],["source_identifier","Source identifier"],["source_url","HTTPS source URL"]
          ] as const).map(([key,title])=><label key={key}><span className={label}>{title}</span><textarea className={field} rows={key==="limitations"||key==="evidence_scope"?3:2} required={!["material_form","instrument_platform","sample_requirements","storage_shipping_requirements"].includes(key)} value={form[key]} onChange={e=>setForm(prev=>({...prev,[key]:e.target.value}))}/></label>)}
          <button disabled={busy||!serviceId||!methodId} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit for independent review</button>
        </form>
      </div>
      {["organization_admin","curator","reviewer"].includes(role)&&<div className="panel p-6"><div className="flex items-center justify-between gap-2"><h2 className="text-xl font-semibold">Capability review queue</h2><button onClick={()=>void loadReviews()} className="text-xs text-emerald-300">Refresh</button></div>
        {reviews.length===0?<p className="muted mt-4 text-sm">No pending laboratory capability claims in this organization.</p>:<div className="mt-4 space-y-4">{reviews.map(item=><article key={item.id} className="rounded-xl border border-slate-700 p-4"><h3 className="font-semibold">{item.laboratory} · {item.site_name}</h3><p className="muted mt-1 text-sm">{item.service_name} · {item.method_name}{item.peptide_name?" · "+item.peptide_name:""}</p><p className="mt-3 text-sm">{item.test_purpose} · {item.sample_matrix}</p><a className="mt-2 block break-all text-xs text-emerald-300 underline" href={item.source_url} target="_blank" rel="noreferrer">{item.source_name} · {item.source_identifier}</a><textarea className={field+" mt-3"} rows={3} placeholder="Independent review rationale (minimum 20 characters)" value={rationales[item.id]||""} onChange={e=>setRationales(prev=>({...prev,[item.id]:e.target.value}))}/><div className="mt-3 flex flex-wrap gap-2">{(["verified","needs_changes","rejected"] as const).map(decision=><button key={decision} onClick={()=>void decide(item,decision)} className="rounded-full border border-slate-600 px-3 py-2 text-xs hover:border-emerald-400">{pretty(decision)}</button>)}</div></article>)}</div>}
      </div>}
    </section>}
    <div className="panel mt-8 p-5"><h2 className="font-semibold">Scientific interpretation boundary</h2><p className="muted mt-2 text-sm leading-6">A reviewed claim records that a cited source supports the stated capability and scope. It does not establish present capacity, available slots, accreditation scope, validated methods, sample acceptance, turnaround time or guaranteed performance. Do not infer missing sample or shipping requirements.</p></div>
  </main>;
}

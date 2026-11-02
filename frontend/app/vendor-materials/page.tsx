"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { getPreferredOrganizationId, setPreferredOrganizationId } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Option = { id: string; [key: string]: any };
type Offering = { id:string;vendor_id:string;vendor_name:string;peptide_id:string;peptide_name:string;chemical_form_id:string;form_name:string;product_name:string;review_status:string;visibility_scope:string };
type Batch = { id:string;offering_id:string;lot_identifier:string;availability_statement:string;review_status:string;expires_on?:string|null };
type Review = { id:string;record_type:"offering"|"batch"|"test_result";label:string;submitted_by:string;review_status:string;source_name:string;source_identifier:string;source_url:string };

export default function VendorMaterialsPage() {
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [token,setToken]=useState("");
  const [role,setRole]=useState("");
  const [vendors,setVendors]=useState<Option[]>([]);
  const [peptides,setPeptides]=useState<Option[]>([]);
  const [forms,setForms]=useState<Option[]>([]);
  const [methods,setMethods]=useState<Option[]>([]);
  const [tests,setTests]=useState<Option[]>([]);
  const [offerings,setOfferings]=useState<Offering[]>([]);
  const [batches,setBatches]=useState<Batch[]>([]);
  const [selectedPeptide,setSelectedPeptide]=useState("");
  const [selectedOffering,setSelectedOffering]=useState("");
  const [selectedBatch,setSelectedBatch]=useState("");
  const [reviews,setReviews]=useState<Review[]>([]);
  const [rationales,setRationales]=useState<Record<string,string>>({});
  const [visibility,setVisibility]=useState<Record<string,string>>({});
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [offeringForm,setOfferingForm]=useState({vendor_id:"",chemical_form_id:"",product_name:"",catalogue_reference:"",material_description:"",source_name:"",source_identifier:"",source_url:"",evidence_scope:""});
  const [batchForm,setBatchForm]=useState({lot_identifier:"",manufacturer_batch_identifier:"",manufactured_on:"",retest_on:"",expires_on:"",quantity:"",quantity_unit:"",availability_statement:"unknown",source_name:"",source_identifier:"",source_url:"",evidence_scope:""});
  const [resultForm,setResultForm]=useState({test_id:"",method_id:"",tested_at:"",sample_identifier:"",sample_matrix:"",method_version:"",instrument_platform:"",reference_standard:"",observed_value:"",observed_text:"",result_unit:"",result_status:"not_reported",source_name:"",source_identifier:"",source_url:"",evidence_scope:""});
  const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-100";
  const label="mb-2 block text-xs text-slate-300";
  const canSubmit=["organization_admin","curator","researcher"].includes(role);
  const canReview=["organization_admin","curator","reviewer"].includes(role);

  async function request(path:string, method="GET", body?:unknown, accessToken=token) {
    const response=await fetch(API+path,{method,headers:{...(body?{"Content-Type":"application/json"}:{}),...(accessToken?{Authorization:"Bearer "+accessToken}:{})},...(body?{body:JSON.stringify(body)}:{})});
    const data=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(data.detail||"Request failed.");
    return data;
  }

  async function loadOptions(accessToken:string) {
    const [v,p,m,t,o]=await Promise.all([
      request("/api/v1/vendors?limit=100","GET",undefined,""),
      request("/api/v1/peptides?limit=100","GET",undefined,""),
      request("/api/v1/analytical-methods?limit=100","GET",undefined,""),
      request("/api/v1/analytical-methods/test-catalogue?limit=200","GET",undefined,""),
      request("/api/v1/vendor-materials/mine/offerings?limit=200","GET",undefined,accessToken),
    ]);
    setVendors(v.items||[]);setPeptides(p.items||[]);setMethods(m.items||[]);
    setTests((t.items||[]).filter((x:Option)=>x.review_status==="verified"));setOfferings(o.items||[]);
    if(canReview) await loadReviews(accessToken);
  }

  async function loadMyOfferings(accessToken=token) {
    const data=await request("/api/v1/vendor-materials/mine/offerings?limit=200","GET",undefined,accessToken);
    setOfferings(data.items||[]);
  }

  async function loadReviews(accessToken=token) {
    const data=await request("/api/v1/vendor-materials/reviews?limit=100","GET",undefined,accessToken);
    setReviews(data.items||[]);
  }

  async function loadChemicalForms(peptideId:string) {
    setSelectedPeptide(peptideId);setOfferingForm(x=>({...x,chemical_form_id:""}));setForms([]);
    if(!peptideId)return;
    const data=await request("/api/v1/peptides/"+peptideId,"GET",undefined,"");
    setForms(data.chemical_forms||[]);
  }

  async function loadBatches(offeringId:string) {
    setSelectedOffering(offeringId);setSelectedBatch("");setBatches([]);
    if(!offeringId)return;
    const data=await request("/api/v1/vendor-materials/offerings/"+offeringId+"/batches","GET");
    setBatches(data.items||[]);
  }

  async function signIn(e:FormEvent) {
    e.preventDefault();setBusy(true);setError("");setMessage("");
    try {
      const data=await request("/api/v1/auth/login","POST",{email,password,organization_id:getPreferredOrganizationId()},"");
      setPreferredOrganizationId(data.user.organization_id);setToken(data.access_token);setRole(data.user.role);setPassword("");
      await loadOptions(data.access_token);
      if(["organization_admin","curator","reviewer"].includes(data.user.role)) await loadReviews(data.access_token);
      setMessage("Signed in. Organization-scoped material records are loaded.");
    } catch(err) {setError(err instanceof Error?err.message:"Sign in failed.");}
    finally {setBusy(false);}
  }

  async function submitOffering(e:FormEvent) {
    e.preventDefault();setBusy(true);setError("");setMessage("");
    try {
      const data=await request("/api/v1/vendor-materials/offerings","POST",{...offeringForm,peptide_id:selectedPeptide});
      setMessage("Offering submitted. ID: "+data.id+" · status: "+data.review_status);
      setOfferingForm({vendor_id:"",chemical_form_id:"",product_name:"",catalogue_reference:"",material_description:"",source_name:"",source_identifier:"",source_url:"",evidence_scope:""});
      setSelectedPeptide("");setForms([]);await loadMyOfferings();
    } catch(err){setError(err instanceof Error?err.message:"Offering submission failed.");}
    finally{setBusy(false);}
  }

  async function submitBatch(e:FormEvent) {
    e.preventDefault();if(!selectedOffering)return;
    setBusy(true);setError("");setMessage("");
    try {
      const body={...batchForm,manufactured_on:batchForm.manufactured_on||null,retest_on:batchForm.retest_on||null,expires_on:batchForm.expires_on||null,quantity:batchForm.quantity||null};
      const data=await request("/api/v1/vendor-materials/offerings/"+selectedOffering+"/batches","POST",body);
      setMessage("Physical lot submitted. ID: "+data.id+" · status: "+data.review_status);
      setBatchForm({lot_identifier:"",manufacturer_batch_identifier:"",manufactured_on:"",retest_on:"",expires_on:"",quantity:"",quantity_unit:"",availability_statement:"unknown",source_name:"",source_identifier:"",source_url:"",evidence_scope:""});
      await loadBatches(selectedOffering);
    }catch(err){setError(err instanceof Error?err.message:"Batch submission failed.");}
    finally{setBusy(false);}
  }

  async function submitResult(e:FormEvent) {
    e.preventDefault();if(!selectedBatch)return;
    setBusy(true);setError("");setMessage("");
    try {
      const body:any={...resultForm,tested_at:resultForm.tested_at||null,observed_value:resultForm.observed_value===""?null:Number(resultForm.observed_value),observed_text:resultForm.observed_text||null};
      const data=await request("/api/v1/vendor-materials/batches/"+selectedBatch+"/test-results","POST",body);
      setMessage("Analytical report submitted. ID: "+data.id+" · status: "+data.review_status);
      setResultForm({test_id:"",method_id:"",tested_at:"",sample_identifier:"",sample_matrix:"",method_version:"",instrument_platform:"",reference_standard:"",observed_value:"",observed_text:"",result_unit:"",result_status:"not_reported",source_name:"",source_identifier:"",source_url:"",evidence_scope:""});
    }catch(err){setError(err instanceof Error?err.message:"Analytical result submission failed.");}
    finally{setBusy(false);}
  }

  async function decide(item:Review,decision:"verified"|"rejected"|"needs_changes") {
    setBusy(true);setError("");setMessage("");
    try {
      const body={decision,rationale:rationales[item.id]||"",visibility_scope:visibility[item.id]||"restricted"};
      const data=await request("/api/v1/vendor-materials/reviews/"+item.record_type+"/"+item.id+"/decisions","POST",body);
      setMessage(item.record_type+" review saved as "+data.review_status+".");
      await loadReviews();await loadMyOfferings();
      if(selectedOffering)await loadBatches(selectedOffering);
    }catch(err){setError(err instanceof Error?err.message:"Review decision failed.");}
    finally{setBusy(false);}
  }

  useEffect(()=>{void request("/api/v1/vendors?limit=100","GET",undefined,"").then(d=>setVendors(d.items||[])).catch(()=>{});},[]);

  return <main className="container min-h-screen py-10">
    <Link href="/vendors" className="text-sm text-emerald-300">← Vendor directory</Link>
    <header className="mt-8 max-w-4xl">
      <p className="accent text-xs tracking-[.2em]">MATERIAL PROVENANCE · LOT TRACEABILITY · ANALYTICAL EVIDENCE</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Vendor materials & batch records</h1>
      <p className="muted mt-4 leading-7">Record a vendor's catalogue offering against an exact reviewed chemical form, register physical supplier lots, and attach source-backed analytical reports. These records are not a purchasing system or a live inventory feed.</p>
    </header>
    {error&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {message&&<div role="status" className="mt-5 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{message}</div>}
    {!token?<section className="panel mt-7 max-w-xl p-5"><h2 className="text-xl font-semibold">Organization sign in</h2><form onSubmit={signIn} className="mt-4 grid gap-3"><label className={label}>Email<input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label className={label}>Password<input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">{busy?"Signing in…":"Sign in"}</button></form></section>:<>
      <div className="panel mt-7 flex flex-wrap items-center justify-between gap-3 p-4"><p className="text-sm">Signed in · <span className="text-emerald-300">{role.replaceAll("_"," ")}</span></p><button onClick={()=>{setToken("");setRole("");setReviews([]);}} className="text-sm text-slate-300 underline">Sign out</button></div>
      {canSubmit&&<section className="mt-7 grid gap-5 xl:grid-cols-2">
        <article className="panel p-5"><h2 className="text-xl font-semibold">1. Submit vendor offering</h2><p className="muted mt-2 text-sm">Only verified vendors and reviewed peptide chemical forms can be linked. New submissions are restricted and in review.</p>
          <form onSubmit={submitOffering} className="mt-4 grid gap-3">
            <label className={label}>Verified vendor<select required className={field} value={offeringForm.vendor_id} onChange={e=>setOfferingForm(x=>({...x,vendor_id:e.target.value}))}><option value="">Select vendor</option>{vendors.map(v=><option key={v.id} value={v.id}>{v.legal_name}</option>)}</select></label>
            <label className={label}>Verified peptide<select required className={field} value={selectedPeptide} onChange={e=>void loadChemicalForms(e.target.value)}><option value="">Select peptide</option>{peptides.map(p=><option key={p.id} value={p.id}>{p.preferred_name}</option>)}</select></label>
            <label className={label}>Reviewed chemical form<select required className={field} value={offeringForm.chemical_form_id} onChange={e=>setOfferingForm(x=>({...x,chemical_form_id:e.target.value}))}><option value="">Select exact form</option>{forms.map(f=><option key={f.id} value={f.id}>{f.form_name} · {f.form_type}</option>)}</select></label>
            <label className={label}>Product / catalogue name<input required className={field} value={offeringForm.product_name} onChange={e=>setOfferingForm(x=>({...x,product_name:e.target.value}))}/></label>
            <label className={label}>Catalogue reference<input className={field} value={offeringForm.catalogue_reference} onChange={e=>setOfferingForm(x=>({...x,catalogue_reference:e.target.value}))}/></label>
            <label className={label}>Material description<textarea className={field} rows={2} value={offeringForm.material_description} onChange={e=>setOfferingForm(x=>({...x,material_description:e.target.value}))}/></label>
            <SourceFields field={field} label={label} value={offeringForm} onChange={setOfferingForm}/>
            <button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Submit offering</button>
          </form>
        </article>
        <article className="panel p-5"><h2 className="text-xl font-semibold">2. Register physical lot</h2><p className="muted mt-2 text-sm">Lot records are visible only to your organization. Availability is recorded as a supplier statement, not live stock.</p>
          <form onSubmit={submitBatch} className="mt-4 grid gap-3">
            <label className={label}>Your material offering<select required className={field} value={selectedOffering} onChange={e=>void loadBatches(e.target.value)}><option value="">Select offering</option>{offerings.map(o=><option key={o.id} value={o.id}>{o.vendor_name} · {o.product_name} · {o.review_status}</option>)}</select></label>
            <div className="grid gap-3 md:grid-cols-2"><label className={label}>Lot identifier<input required className={field} value={batchForm.lot_identifier} onChange={e=>setBatchForm(x=>({...x,lot_identifier:e.target.value}))}/></label><label className={label}>Manufacturer batch ID<input className={field} value={batchForm.manufacturer_batch_identifier} onChange={e=>setBatchForm(x=>({...x,manufacturer_batch_identifier:e.target.value}))}/></label></div>
            <div className="grid gap-3 md:grid-cols-3">{(["manufactured_on","retest_on","expires_on"] as const).map(k=><label key={k} className={label}>{k.replaceAll("_"," ")}<input type="date" className={field} value={batchForm[k]} onChange={e=>setBatchForm(x=>({...x,[k]:e.target.value}))}/></label>)}</div>
            <div className="grid gap-3 md:grid-cols-3"><label className={label}>Quantity<input type="number" min="0" step="0.000001" className={field} value={batchForm.quantity} onChange={e=>setBatchForm(x=>({...x,quantity:e.target.value}))}/></label><label className={label}>Unit<input className={field} value={batchForm.quantity_unit} onChange={e=>setBatchForm(x=>({...x,quantity_unit:e.target.value}))}/></label><label className={label}>Availability statement<select className={field} value={batchForm.availability_statement} onChange={e=>setBatchForm(x=>({...x,availability_statement:e.target.value}))}>{["unknown","stated_available","stated_unavailable","discontinued","quarantined","recalled","depleted"].map(x=><option key={x} value={x}>{x.replaceAll("_"," ")}</option>)}</select></label></div>
            <SourceFields field={field} label={label} value={batchForm} onChange={setBatchForm}/>
            <button disabled={busy||!selectedOffering} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950">Register lot</button>
          </form>
          {selectedOffering&&<div className="mt-5 border-t border-slate-700 pt-4"><h3 className="text-sm font-semibold">Lots for selected offering</h3>{batches.length===0?<p className="muted mt-2 text-xs">No lots registered yet.</p>:<div className="mt-2 space-y-2">{batches.map(b=><button key={b.id} onClick={()=>setSelectedBatch(b.id)} className={"w-full rounded-lg border p-3 text-left text-sm "+(selectedBatch===b.id?"border-emerald-400":"border-slate-700")}><span className="font-medium">{b.lot_identifier}</span><span className="muted ml-2 text-xs">{b.review_status} · {b.availability_statement.replaceAll("_"," ")}</span></button>)}</div>}</div>}
        </article>
        <article className="panel p-5 xl:col-span-2"><h2 className="text-xl font-semibold">3. Attach batch analytical report</h2><p className="muted mt-2 text-sm">Only reviewed analytical test and method catalogue entries are selectable. A reported pass is not proof of method validation or product suitability.</p>
          <form onSubmit={submitResult} className="mt-4 grid gap-3 md:grid-cols-2">
            <label className={label}>Selected physical lot<select required className={field} value={selectedBatch} onChange={e=>setSelectedBatch(e.target.value)}><option value="">Select a lot above</option>{batches.map(b=><option key={b.id} value={b.id}>{b.lot_identifier} · {b.review_status}</option>)}</select></label>
            <label className={label}>Analytical test<select required className={field} value={resultForm.test_id} onChange={e=>setResultForm(x=>({...x,test_id:e.target.value}))}><option value="">Select reviewed test</option>{tests.map(t=><option key={t.id} value={t.id}>{t.catalogue_code} · {t.test_name}</option>)}</select></label>
            <label className={label}>Analytical method<select required className={field} value={resultForm.method_id} onChange={e=>setResultForm(x=>({...x,method_id:e.target.value}))}><option value="">Select reviewed method</option>{methods.map(m=><option key={m.id} value={m.id}>{m.method_name} · {m.method_category}</option>)}</select></label>
            <label className={label}>Tested at<input type="datetime-local" className={field} value={resultForm.tested_at} onChange={e=>setResultForm(x=>({...x,tested_at:e.target.value}))}/></label>
            <label className={label}>Sample identifier<input className={field} value={resultForm.sample_identifier} onChange={e=>setResultForm(x=>({...x,sample_identifier:e.target.value}))}/></label>
            <label className={label}>Sample matrix<input className={field} value={resultForm.sample_matrix} onChange={e=>setResultForm(x=>({...x,sample_matrix:e.target.value}))}/></label>
            <label className={label}>Method version<input className={field} value={resultForm.method_version} onChange={e=>setResultForm(x=>({...x,method_version:e.target.value}))}/></label>
            <label className={label}>Instrument platform<input className={field} value={resultForm.instrument_platform} onChange={e=>setResultForm(x=>({...x,instrument_platform:e.target.value}))}/></label>
            <label className={label}>Reference standard<input className={field} value={resultForm.reference_standard} onChange={e=>setResultForm(x=>({...x,reference_standard:e.target.value}))}/></label>
            <div className="grid grid-cols-2 gap-3"><label className={label}>Observed numeric value<input type="number" step="any" className={field} value={resultForm.observed_value} onChange={e=>setResultForm(x=>({...x,observed_value:e.target.value,observed_text:""}))}/></label><label className={label}>Unit<input className={field} value={resultForm.result_unit} onChange={e=>setResultForm(x=>({...x,result_unit:e.target.value}))}/></label></div>
            <label className={label}>Observed text result<input className={field} value={resultForm.observed_text} onChange={e=>setResultForm(x=>({...x,observed_text:e.target.value,observed_value:""}))}/></label>
            <label className={label}>Reported status<select className={field} value={resultForm.result_status} onChange={e=>setResultForm(x=>({...x,result_status:e.target.value}))}>{["not_reported","pass","fail","inconclusive"].map(x=><option key={x}>{x}</option>)}</select></label>
            <SourceFields field={field} label={label} value={resultForm} onChange={setResultForm}/>
            <button disabled={busy||!selectedBatch} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 md:col-span-2">Submit analytical report</button>
          </form>
        </article>
      </section>}
      {canReview&&<section className="mt-8"><div className="flex items-center justify-between"><h2 className="text-2xl font-semibold">Independent review queue</h2><button onClick={()=>void loadReviews()} className="text-sm text-emerald-300 underline">Refresh</button></div>
        {reviews.length===0?<div className="panel mt-4 p-5 text-sm muted">No pending material records in this organization.</div>:<div className="mt-4 grid gap-4 lg:grid-cols-2">{reviews.map(item=><article key={item.record_type+item.id} className="panel p-5"><div className="flex items-start justify-between gap-3"><div><p className="accent text-xs uppercase">{item.record_type.replaceAll("_"," ")}</p><h3 className="mt-1 font-semibold">{item.label}</h3><p className="muted mt-1 text-xs">Submitted by {item.submitted_by}</p></div><span className="rounded-full border border-amber-400/40 px-3 py-1 text-xs text-amber-200">In review</span></div><a href={item.source_url} target="_blank" rel="noreferrer" className="mt-3 block break-all text-xs text-emerald-300 underline">{item.source_name} · {item.source_identifier}</a><label className={label+" mt-4"}>Review rationale<textarea className={field} rows={3} minLength={20} value={rationales[item.id]||""} onChange={e=>setRationales(x=>({...x,[item.id]:e.target.value}))} placeholder="Explain the evidence checked and review outcome."/></label>{item.record_type==="offering"&&<label className={label}>Publication scope on verification<select className={field} value={visibility[item.id]||"restricted"} onChange={e=>setVisibility(x=>({...x,[item.id]:e.target.value}))}><option value="restricted">Restricted</option><option value="organization">Organization</option><option value="public">Public directory</option></select></label>}<div className="mt-3 flex flex-wrap gap-2"><button disabled={busy||(rationales[item.id]||"").trim().length<20} onClick={()=>void decide(item,"verified")} className="rounded-full bg-emerald-400 px-4 py-2 text-xs font-semibold text-slate-950">Verify</button><button disabled={busy||(rationales[item.id]||"").trim().length<20} onClick={()=>void decide(item,"needs_changes")} className="rounded-full border border-amber-400/50 px-4 py-2 text-xs text-amber-200">Needs changes</button><button disabled={busy||(rationales[item.id]||"").trim().length<20} onClick={()=>void decide(item,"rejected")} className="rounded-full border border-rose-400/50 px-4 py-2 text-xs text-rose-200">Reject</button></div></article>)}</div>}
      </section>}
      <section className="panel mt-8 p-5"><h2 className="font-semibold">Evidence and interpretation safeguards</h2><ul className="muted mt-3 list-disc space-y-2 pl-5 text-sm leading-6"><li>Every offering is linked to an exact reviewed chemical form, not merely a peptide name or sequence.</li><li>New records remain in review. A submitter cannot review their own record.</li><li>Supplier stock statements are not live inventory. Batch records and reports remain organization-scoped.</li><li>Analytical reports preserve the source statement. A reported pass does not establish validation, specification compliance, release suitability or clinical safety.</li><li>Source evidence is immutable; corrections require superseding records.</li></ul></section>
    </>}
  </main>;
}

function SourceFields({field,label,value,onChange}:{field:string;label:string;value:any;onChange:(next:any)=>void}) {
  const keys=["source_name","source_identifier","source_url","evidence_scope"] as const;
  const names=["Source name","Source identifier","HTTPS source URL","Evidence scope"];
  return <div className="grid gap-3 md:grid-cols-2">{keys.map((key,i)=><label key={key} className={label}>{names[i]}{key==="evidence_scope"?<textarea required minLength={5} rows={2} className={field} value={value[key]} onChange={e=>onChange((x:any)=>({...x,[key]:e.target.value}))}/>:<input required minLength={key==="source_url"?undefined:1} type={key==="source_url"?"url":"text"} className={field} value={value[key]} onChange={e=>onChange((x:any)=>({...x,[key]:e.target.value}))}/>}</label>)}</div>;
}

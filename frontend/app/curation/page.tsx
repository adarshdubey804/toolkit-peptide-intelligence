"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Review = { id:string; entity_type:string; entity_id:string; source_record_id?:string; review_status:string; priority:string; assigned_to?:string; created_at:string; record_label?:string; source_name?:string; source_identifier?:string; source_url?:string };
type User = { id:string; display_name:string; role:string; organization_name:string };

export default function CurationDashboardPage() {
 const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [token,setToken]=useState(""); const [user,setUser]=useState<User|null>(null);
 const [reviews,setReviews]=useState<Review[]>([]); const [status,setStatus]=useState("in_review"); const [loading,setLoading]=useState(false); const [busyId,setBusyId]=useState("");
 const [rationales,setRationales]=useState<Record<string,string>>({}); const [errors,setErrors]=useState(""); const [notice,setNotice]=useState("");
 const loadQueue=useCallback(async()=>{ if(!token)return; setLoading(true);setErrors("");try{
  const params=new URLSearchParams({limit:"100"});if(status!=="all")params.set("review_status",status);
  const response=await fetch(API_BASE+"/api/v1/curation/reviews?"+params.toString(),{headers:{Authorization:"Bearer "+token}});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Could not load review queue.");setReviews(data.reviews||[]);
 }catch(err){setErrors(err instanceof Error?err.message:"Queue request failed.");}finally{setLoading(false);}},[token,status]);
 useEffect(()=>{if(token)void loadQueue();},[token,loadQueue]);
 async function signIn(event:FormEvent){event.preventDefault();setLoading(true);setErrors("");try{
  const response=await fetch(API_BASE+"/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Sign in failed.");
  if(!["organization_admin","curator","reviewer"].includes(data.user.role))throw new Error("Your account does not have curator or reviewer permissions.");
  setToken(data.access_token);setUser(data.user);setPassword("");
 }catch(err){setErrors(err instanceof Error?err.message:"Unable to sign in.");}finally{setLoading(false);}}
 async function assignToMe(review:Review){setBusyId(review.id);setErrors("");try{
  const response=await fetch(API_BASE+"/api/v1/curation/reviews/"+review.id+"/assignment",{method:"PATCH",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({assigned_to:user?.id})});
  const data=await response.json();if(!response.ok)throw new Error(data.detail||"Assignment failed.");setNotice("Review assignment updated.");await loadQueue();
 }catch(err){setErrors(err instanceof Error?err.message:"Assignment failed.");}finally{setBusyId("");}}
 async function decide(event:FormEvent,review:Review,decision:"verified"|"rejected"|"needs_changes"){event.preventDefault();const rationale=(rationales[review.id]||"").trim();if(rationale.length<20){setErrors("Please provide a rationale of at least 20 characters.");return;}
  setBusyId(review.id);setErrors("");try{const response=await fetch(API_BASE+"/api/v1/curation/reviews/"+review.id+"/decisions",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify({decision,rationale})});
   const data=await response.json();if(!response.ok)throw new Error(data.detail||"Decision could not be recorded.");setNotice("Decision recorded: "+decision.replace("_"," ")+".");setRationales(prev=>({...prev,[review.id]:""}));await loadQueue();
  }catch(err){setErrors(err instanceof Error?err.message:"Decision failed.");}finally{setBusyId("");}}
 const field="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-emerald-400";
 const label="mb-2 block text-xs font-medium text-slate-300";
 return <main className="container min-h-screen py-10">
  <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
  <header className="mt-9 max-w-3xl"><p className="accent text-xs tracking-[.2em]">SCIENTIFIC QUALITY CONTROL</p><h1 className="mt-3 text-4xl font-semibold md:text-5xl">Curator review dashboard</h1><p className="muted mt-4 leading-7">Inspect source-linked submissions, assign reviews and record traceable editorial decisions. Verification is an editorial action, not clinical or regulatory endorsement.</p></header>
  {!token?<section className="panel mt-8 max-w-xl p-6"><h2 className="text-xl font-semibold">Reviewer sign in</h2><form onSubmit={signIn} className="mt-5 space-y-4">
   <label className="block"><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label>
   <label className="block"><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label>
   <button disabled={loading} className="rounded-full bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{loading?"Signing in…":"Sign in as reviewer"}</button>
  </form></section>:<>
   <div className="panel mt-7 flex flex-wrap items-center justify-between gap-4 p-4"><div><p className="text-sm font-semibold">{user?.display_name}</p><p className="muted mt-1 text-xs">{user?.organization_name} · {user?.role}</p></div><div className="flex gap-3"><button onClick={()=>void loadQueue()} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Refresh queue</button><button onClick={()=>{setToken("");setUser(null);setReviews([]);}} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Sign out</button></div></div>
   <div className="mt-6 flex flex-wrap items-end justify-between gap-4"><div><h2 className="text-2xl font-semibold">Review queue</h2><p className="muted mt-1 text-sm">{reviews.length} records returned · organization-scoped</p></div><label className="block min-w-48"><span className={label}>Review status</span><select className={field} value={status} onChange={e=>setStatus(e.target.value)}><option value="in_review">Awaiting review</option><option value="draft">Needs changes / draft</option><option value="verified">Verified</option><option value="rejected">Rejected</option><option value="archived">Archived</option><option value="all">All statuses</option></select></label></div>
   {loading&&<div className="panel mt-4 p-6 text-sm muted">Loading review queue…</div>}
   {!loading&&reviews.length===0&&<div className="panel mt-4 p-8 text-center"><h3 className="font-semibold">No records in this queue</h3><p className="muted mt-2 text-sm">New researcher submissions will appear here after they enter review.</p></div>}
   <div className="mt-4 space-y-4">{reviews.map(review=><article key={review.id} className="panel p-5">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wider"><span className="text-emerald-300">{review.entity_type.replace("_"," ")}</span><span className="muted">· {review.priority} priority</span><span className="rounded-full border border-slate-700 px-2 py-1">{review.review_status}</span></div><h3 className="mt-3 text-lg font-semibold">{review.record_label||"Scientific record"}</h3><p className="muted mt-1 text-xs">Submitted {new Date(review.created_at).toLocaleString()}</p></div><span className="muted max-w-48 break-all text-[10px]">Review ID: {review.id}</span></div>
    <div className="mt-4 rounded-xl border border-slate-700 bg-slate-950/60 p-4"><p className="text-xs font-semibold text-slate-300">Source provenance</p>{review.source_name?<><p className="mt-2 text-sm">{review.source_name}{review.source_identifier?" · "+review.source_identifier:""}</p>{review.source_url?<a href={review.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-block break-all text-xs text-emerald-300 underline">Open original source ↗</a>:<p className="muted mt-2 text-xs">No source URL attached.</p>}</>:<p className="muted mt-2 text-xs">No source details returned.</p>}</div>
    {["in_review","draft"].includes(review.review_status)&&<><div className="mt-4 flex flex-wrap items-center gap-3"><button disabled={busyId===review.id} onClick={()=>void assignToMe(review)} className="rounded-full border border-slate-600 px-4 py-2 text-xs disabled:opacity-50">Assign to me</button><span className="muted text-xs">{review.assigned_to?"Assigned reviewer: "+review.assigned_to:"Unassigned"}</span></div>
     <form onSubmit={event=>void decide(event,review,"verified")} className="mt-4 border-t border-slate-800 pt-4"><label className="block"><span className={label}>Review rationale (minimum 20 characters)</span><textarea className={field} rows={3} minLength={20} value={rationales[review.id]||""} onChange={e=>setRationales(prev=>({...prev,[review.id]:e.target.value}))} placeholder="Document source quality, identity checks, evidence context and limitations."/></label>
      <div className="mt-3 flex flex-wrap gap-2"><button disabled={busyId===review.id} className="rounded-full bg-emerald-400 px-5 py-2.5 text-xs font-semibold text-slate-950 disabled:opacity-50">Verify record</button><button type="button" disabled={busyId===review.id} onClick={()=>{const fake={preventDefault:()=>{}} as FormEvent;void decide(fake,review,"needs_changes");}} className="rounded-full border border-amber-400/50 px-4 py-2.5 text-xs text-amber-200">Request changes</button><button type="button" disabled={busyId===review.id} onClick={()=>{const fake={preventDefault:()=>{}} as FormEvent;void decide(fake,review,"rejected");}} className="rounded-full border border-rose-400/50 px-4 py-2.5 text-xs text-rose-200">Reject</button></div>
     </form></>}
   </article>)}</div>
  </>}
  {errors&&<div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{errors}</div>}
  {notice&&<div role="status" className="mt-5 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4 text-sm text-emerald-200">{notice}</div>}
  <p className="muted mt-12 border-t border-slate-800 pt-5 text-xs">A verification decision confirms completion of editorial review only. It does not establish efficacy, safety, quality release or regulatory approval.</p>
 </main>;
}

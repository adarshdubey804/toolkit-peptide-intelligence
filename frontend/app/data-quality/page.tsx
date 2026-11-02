"use client";

import { getPreferredOrganizationId, setPreferredOrganizationId } from "@/lib/auth";
import Link from "next/link";
import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Metric = { total:number; verified?:number; with_primary_source?:number; source_coverage_percent?:number|null; with_source?:number; with_source_record?:number; versioned_identity?:number; standard_sequence_candidates?:number; standard_sequence_fingerprinted?:number; standard_sequence_fingerprint_coverage_percent?:number|null; with_revision?:number; revision_coverage_percent?:number|null; with_source_version?:number; source_version_coverage_percent?:number|null; open_reviews?:number; total_reviews?:number; decisions?:number; claim_revision_bound_decisions?:number; claim_revision_binding_percent?:number|null };
type Report = {
 generated_at:string; scope:{organization:string;notice:string};
 shared_catalogue:{peptides:Metric;sequences:Metric;chemical_forms:Metric};
 organization_evidence:{claims:Metric;extractions:Metric;curation:Metric};
 shared_provenance:{source_records:number;source_records_with_versions:number;version_coverage_percent:number|null};
};

function Card({title,value,detail}:{title:string;value:string|number;detail:string}) {
 return <div className="panel p-5"><p className="muted text-xs">{title}</p><p className="mt-2 text-3xl font-semibold">{value}</p><p className="muted mt-2 text-xs">{detail}</p></div>;
}
function percent(value:number|null|undefined) { return value===null||value===undefined?"Not available":value.toFixed(1)+"%"; }

export default function DataQualityPage() {
 const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [token,setToken]=useState("");
 const [report,setReport]=useState<Report|null>(null); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
 async function load(accessToken:string) {
  setBusy(true);setError("");
  try { const response=await fetch(API+"/api/v1/data-quality/completeness",{headers:{Authorization:"Bearer "+accessToken}}); const data=await response.json(); if(!response.ok)throw new Error(data.detail||"Could not load report."); setReport(data as Report); }
  catch(err) { setError(err instanceof Error?err.message:"Report request failed."); }
  finally { setBusy(false); }
 }
 async function signIn(event:FormEvent) {
  event.preventDefault();setBusy(true);setError("");
  try {
   const response=await fetch(API+"/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password,organization_id:getPreferredOrganizationId()})});
   const data=await response.json();if(!response.ok)throw new Error(data.detail||"Sign in failed.");
   if(!["organization_admin","curator","reviewer"].includes(data.user.role))throw new Error("Curator or reviewer permissions are required.");
   setPreferredOrganizationId(data.user.organization_id);setToken(data.access_token);setPassword("");await load(data.access_token);
  } catch(err) { setError(err instanceof Error?err.message:"Sign in failed.");setBusy(false); }
 }
 return <main className="container min-h-screen py-10">
  <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
  <header className="mt-8 max-w-3xl"><p className="accent text-xs tracking-[.2em]">SCIENTIFIC DATA GOVERNANCE</p><h1 className="mt-3 text-4xl font-semibold md:text-5xl">Data completeness dashboard</h1><p className="muted mt-4 leading-7">Inspect source coverage, revision traceability, sequence identity metadata and curation workload. Completeness metrics do not measure scientific truth or evidence quality.</p></header>
  {!token?<form onSubmit={signIn} className="panel mt-8 max-w-xl space-y-4 p-6"><h2 className="text-xl font-semibold">Curator sign in</h2><label className="block text-sm">Email<input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label className="block text-sm">Password<input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm" type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label><button disabled={busy} className="rounded-full bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{busy?"Loading…":"Sign in and load report"}</button></form>:<>
   <div className="panel mt-7 flex flex-wrap items-center justify-between gap-4 p-4"><div><p className="text-sm font-semibold">Organization-scoped view</p><p className="muted mt-1 text-xs">Organization ID: {report?.scope.organization||"Loading"}</p></div><div className="flex gap-3"><button onClick={()=>void load(token)} disabled={busy} className="rounded-full border border-slate-600 px-4 py-2 text-xs disabled:opacity-50">Refresh</button><button onClick={()=>{setToken("");setReport(null);}} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Sign out</button></div></div>
   {report&&<>
    <div className="mt-5 rounded-xl border border-slate-700 p-4 text-xs leading-6"><p>{report.scope.notice}</p><p className="muted mt-1">Generated {new Date(report.generated_at).toLocaleString()}</p></div>
    <section className="mt-8"><h2 className="text-2xl font-semibold">Shared peptide catalogue</h2><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
     <Card title="Peptide records" value={report.shared_catalogue.peptides.total} detail={(report.shared_catalogue.peptides.verified||0)+" marked verified"}/>
     <Card title="Peptide source coverage" value={percent(report.shared_catalogue.peptides.source_coverage_percent)} detail={(report.shared_catalogue.peptides.with_primary_source||0)+" have a primary source"}/>
     <Card title="Standard sequence fingerprint coverage" value={percent(report.shared_catalogue.sequences.standard_sequence_fingerprint_coverage_percent)} detail={report.shared_catalogue.sequences.standard_sequence_fingerprinted+" / "+report.shared_catalogue.sequences.standard_sequence_candidates+" standard candidates"}/>
     <Card title="Chemical forms" value={report.shared_catalogue.chemical_forms.total} detail={(report.shared_catalogue.chemical_forms.verified||0)+" marked verified"}/>
     <Card title="Chemical-form source coverage" value={percent(report.shared_catalogue.chemical_forms.source_coverage_percent)} detail={(report.shared_catalogue.chemical_forms.with_source||0)+" forms have a source"}/>
     <Card title="Versioned chemical identities" value={report.shared_catalogue.chemical_forms.versioned_identity||0} detail="Fingerprint and canonicalization version present"/>
    </div></section>
    <section className="mt-8"><h2 className="text-2xl font-semibold">Organization evidence and curation</h2><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
     <Card title="Evidence claims" value={report.organization_evidence.claims.total} detail={(report.organization_evidence.claims.verified||0)+" marked verified"}/>
     <Card title="Claim source coverage" value={percent(report.organization_evidence.claims.source_coverage_percent)} detail={(report.organization_evidence.claims.with_source||0)+" claims have a linked source"}/>
     <Card title="Claim revision coverage" value={percent(report.organization_evidence.claims.revision_coverage_percent)} detail={(report.organization_evidence.claims.with_revision||0)+" claims have immutable revisions"}/>
     <Card title="Open curation reviews" value={report.organization_evidence.curation.open_reviews||0} detail={report.organization_evidence.curation.total_reviews+" reviews total"}/>
     <Card title="Curation decisions" value={report.organization_evidence.curation.decisions||0} detail={(report.organization_evidence.curation.claim_revision_bound_decisions||0)+" claim decisions bound to revisions"}/>
     <Card title="Claim decision revision binding" value={percent(report.organization_evidence.curation.claim_revision_binding_percent)} detail="Not a scientific-quality score"/>
    </div></section>
    <section className="mt-8"><h2 className="text-2xl font-semibold">Source provenance</h2><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
     <Card title="Shared source records" value={report.shared_provenance.source_records} detail="Unique source registry identities"/>
     <Card title="Source records with versions" value={report.shared_provenance.source_records_with_versions} detail="At least one captured source version"/>
     <Card title="Source version coverage" value={percent(report.shared_provenance.version_coverage_percent)} detail="Shared source registry"/>
     <Card title="Extraction records" value={report.organization_evidence.extractions.total} detail={(report.organization_evidence.extractions.with_source_record||0)+" linked to source identity"}/>
     <Card title="Extraction source-version coverage" value={percent(report.organization_evidence.extractions.source_version_coverage_percent)} detail={(report.organization_evidence.extractions.with_source_version||0)+" have a captured version"}/>
    </div></section>
   </>}
  </>}
  {error&&<p role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</p>}
  <p className="muted mt-12 border-t border-slate-800 pt-5 text-xs">No composite completeness score is calculated. Missing metadata, unreviewed records and weak scientific evidence are different problems.</p>
 </main>;
}

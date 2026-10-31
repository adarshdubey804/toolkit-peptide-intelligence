"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function SubmitPeptidePage() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [category, setCategory] = useState("research peptide");
  const [description, setDescription] = useState("");
  const [intendedUse, setIntendedUse] = useState("research_only");
  const [aliases, setAliases] = useState("");
  const [sequence, setSequence] = useState("");
  const [modifications, setModifications] = useState("");
  const [formula, setFormula] = useState("");
  const [mass, setMass] = useState("");
  const [propertyOrigin, setPropertyOrigin] = useState("unknown");
  const [claim, setClaim] = useState("");
  const [claimDomain, setClaimDomain] = useState("mechanism");
  const [evidenceType, setEvidenceType] = useState("unknown");
  const [limitations, setLimitations] = useState("");
  const [sourceName, setSourceName] = useState("PubMed");
  const [sourceIdentifier, setSourceIdentifier] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [licenseNotes, setLicenseNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function login(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Login failed.");
      setToken(data.access_token);
      setMessage(`Signed in as ${data.user.display_name} · ${data.user.role}`);
      setPassword("");
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to sign in."); }
    finally { setBusy(false); }
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const parsedMods = modifications.trim() ? modifications.split(",").map((value) => ({ name: value.trim() })).filter((value) => value.name) : [];
      const payload = {
        preferred_name: name, peptide_category: category || null, description: description || null,
        intended_use_class: intendedUse,
        aliases: aliases.split(",").map((value) => value.trim()).filter(Boolean),
        sequences: sequence.trim() ? [{ sequence: sequence.trim(), sequence_type: "amino_acid", modifications: parsedMods }] : [],
        chemical_properties: formula || mass ? [{
          molecular_formula: formula || null, average_molecular_mass: mass ? Number(mass) : null,
          property_origin: propertyOrigin,
        }] : [],
        claims: claim.trim() ? [{ claim_text: claim.trim(), claim_domain: claimDomain, evidence_type: evidenceType, limitations: limitations || null }] : [],
        source_name: sourceName, source_identifier: sourceIdentifier || null, source_url: sourceUrl,
        source_license_notes: licenseNotes || null,
      };
      const response = await fetch(`${API_BASE}/api/v1/dossiers`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Dossier submission failed.");
      setMessage(`Dossier submitted for review. Peptide ID: ${data.peptide_id} · Review ID: ${data.review_id}`);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to submit dossier."); }
    finally { setBusy(false); }
  }

  const field = "w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-emerald-400";
  const label = "mb-2 block text-xs font-medium text-slate-300";
  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-9 max-w-3xl"><p className="accent text-xs tracking-[.2em]">SCIENTIFIC DATA CONTRIBUTION</p><h1 className="mt-3 text-4xl font-semibold md:text-5xl">Peptide dossier submission</h1><p className="muted mt-4 leading-7">Submit source-linked scientific information for editorial review. Draft records are not public and are not automatically verified.</p></header>

    {!token ? <section className="panel mt-8 max-w-xl p-6"><h2 className="text-xl font-semibold">Researcher sign in</h2><p className="muted mt-2 text-sm">Use your Toolkit organization account to submit a dossier.</p><form onSubmit={login} className="mt-5 space-y-4">
      <label className="block"><span className={label}>Email</span><input className={field} type="email" required value={email} onChange={(e)=>setEmail(e.target.value)} /></label>
      <label className="block"><span className={label}>Password</span><input className={field} type="password" required value={password} onChange={(e)=>setPassword(e.target.value)} /></label>
      <button disabled={busy} className="rounded-full bg-emerald-400 px-6 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{busy ? "Signing in…" : "Sign in"}</button>
    </form><p className="muted mt-4 text-xs">Accounts are created through the API registration endpoint; public self-registration is not exposed on this page.</p></section> : <>
      <div className="mt-7 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4"><p className="text-sm text-emerald-200">Authenticated session active</p><button onClick={()=>{setToken("");setMessage("Signed out.");}} className="text-xs text-slate-300 underline">Sign out</button></div>
      <form onSubmit={submit} className="mt-6 space-y-5">
        <section className="panel p-6"><h2 className="text-xl font-semibold">01 · Identity</h2><div className="mt-5 grid gap-4 md:grid-cols-2">
          <label><span className={label}>Preferred peptide name *</span><input className={field} required minLength={2} value={name} onChange={(e)=>setName(e.target.value)} /></label>
          <label><span className={label}>Category</span><input className={field} value={category} onChange={(e)=>setCategory(e.target.value)} /></label>
          <label><span className={label}>Intended use classification</span><select className={field} value={intendedUse} onChange={(e)=>setIntendedUse(e.target.value)}><option value="research_only">Research only</option><option value="investigational">Investigational</option><option value="approved_medicine">Approved medicine</option><option value="endogenous_reference">Endogenous reference</option><option value="unspecified">Unspecified</option></select></label>
          <label><span className={label}>Aliases (comma-separated)</span><input className={field} value={aliases} onChange={(e)=>setAliases(e.target.value)} placeholder="Alternative names" /></label>
          <label className="md:col-span-2"><span className={label}>Description</span><textarea className={field} rows={3} value={description} onChange={(e)=>setDescription(e.target.value)} /></label>
        </div></section>
        <section className="panel p-6"><h2 className="text-xl font-semibold">02 · Sequence and modifications</h2><p className="muted mt-2 text-xs">Enter the reported sequence only. Do not infer residues or modifications from a product name.</p><div className="mt-4 space-y-4"><label className="block"><span className={label}>Amino-acid sequence</span><textarea className={field+" font-mono"} rows={3} value={sequence} onChange={(e)=>setSequence(e.target.value)} placeholder="e.g. ACDEFG…" /></label><label className="block"><span className={label}>Modifications (comma-separated labels)</span><input className={field} value={modifications} onChange={(e)=>setModifications(e.target.value)} placeholder="e.g. N-terminal acetylation, C-terminal amidation" /></label></div></section>
        <section className="panel p-6"><h2 className="text-xl font-semibold">03 · Chemical properties</h2><div className="mt-4 grid gap-4 md:grid-cols-3"><label><span className={label}>Molecular formula</span><input className={field} value={formula} onChange={(e)=>setFormula(e.target.value)} /></label><label><span className={label}>Average molecular mass (Da)</span><input className={field} type="number" min="0.000001" step="any" value={mass} onChange={(e)=>setMass(e.target.value)} /></label><label><span className={label}>Property origin</span><select className={field} value={propertyOrigin} onChange={(e)=>setPropertyOrigin(e.target.value)}><option value="unknown">Unknown</option><option value="measured">Measured</option><option value="calculated">Calculated</option><option value="predicted">Predicted</option><option value="imported">Imported</option></select></label></div></section>
        <section className="panel p-6"><h2 className="text-xl font-semibold">04 · Evidence claim (optional)</h2><div className="mt-4 grid gap-4 md:grid-cols-2"><label><span className={label}>Claim domain</span><select className={field} value={claimDomain} onChange={(e)=>setClaimDomain(e.target.value)}>{["identity","chemistry","mechanism","target","pathway","safety","clinical","formulation","analytical","other"].map(v=><option key={v}>{v}</option>)}</select></label><label><span className={label}>Evidence classification</span><select className={field} value={evidenceType} onChange={(e)=>setEvidenceType(e.target.value)}>{["unknown","regulatory","clinical","preclinical_animal","in_vitro","computational","review"].map(v=><option key={v}>{v}</option>)}</select></label><label className="md:col-span-2"><span className={label}>Scientific claim</span><textarea className={field} rows={3} minLength={10} value={claim} onChange={(e)=>setClaim(e.target.value)} placeholder="State one bounded claim, not a clinical recommendation." /></label><label className="md:col-span-2"><span className={label}>Limitations / context</span><textarea className={field} rows={2} value={limitations} onChange={(e)=>setLimitations(e.target.value)} /></label></div></section>
        <section className="panel p-6"><h2 className="text-xl font-semibold">05 · Source provenance</h2><p className="muted mt-2 text-xs">A resolvable original source URL is required. The source must support the information submitted.</p><div className="mt-4 grid gap-4 md:grid-cols-2"><label><span className={label}>Source name *</span><input className={field} required value={sourceName} onChange={(e)=>setSourceName(e.target.value)} /></label><label><span className={label}>Source identifier</span><input className={field} value={sourceIdentifier} onChange={(e)=>setSourceIdentifier(e.target.value)} /></label><label className="md:col-span-2"><span className={label}>Original source URL *</span><input className={field} type="url" required value={sourceUrl} onChange={(e)=>setSourceUrl(e.target.value)} placeholder="https://…" /></label><label className="md:col-span-2"><span className={label}>Licence / reuse notes</span><input className={field} value={licenseNotes} onChange={(e)=>setLicenseNotes(e.target.value)} /></label></div></section>
        <div className="flex flex-wrap items-center gap-4"><button disabled={busy} className="rounded-full bg-emerald-400 px-7 py-3 font-semibold text-slate-950 disabled:opacity-50">{busy ? "Submitting…" : "Submit dossier for review"}</button><span className="muted text-xs">Submission is not public until approved by a reviewer.</span></div>
      </form>
    </>}
    {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {message && <div role="status" className="mt-5 rounded-xl border border-emerald-400/30 bg-emerald-400/5 p-4 text-sm text-emerald-200">{message}</div>}
    <p className="muted mt-12 border-t border-slate-800 pt-5 text-xs">This form records scientific research information. It does not validate clinical efficacy, product quality, regulatory status or manufacturing suitability.</p>
  </main>;
}

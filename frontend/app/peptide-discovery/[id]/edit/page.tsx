"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getAccessToken } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type Section = { id: string; section_key: string; content: Record<string, unknown>; citations: Record<string, unknown>[]; media: Record<string, unknown>[]; revision: number };
const starter = {
  identity: "Identity and nomenclature",
  sequence: "Amino-acid sequence and modifications",
  chemistry: "Chemical identity and properties",
  mechanism: "Mechanism of action and targets",
  pharmacology: "Pharmacodynamics and pharmacokinetics",
  clinical: "Clinical development and trial results",
  preclinical: "Preclinical evidence",
  regulatory: "Regulatory status by product and jurisdiction",
  safety: "Safety, adverse events and interactions",
  formulation: "Formulation, stability and storage",
  manufacturing: "Manufacturing, purification and impurities",
  analytical: "Analytical characterization and quality",
  pathways: "Pathways and bioinformatics",
  patents: "Patents and intellectual property",
  literature: "Literature and evidence appraisal",
  gaps: "Conflicts, limitations and knowledge gaps",
};

export default function EditPeptideDossierPage() {
  const params = useParams<{ id: string }>();
  const [token, setToken] = useState("");
  const [sections, setSections] = useState<Section[]>([]);
  const [sectionKey, setSectionKey] = useState("identity");
  const [contentText, setContentText] = useState("{}");
  const [citationsText, setCitationsText] = useState("[]");
  const [mediaText, setMediaText] = useState("[]");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const stored = getAccessToken();
    if (!stored) { setError("Sign in to edit this dossier."); return; }
    setToken(stored);
    fetch(API + "/api/v1/dossiers/candidates/" + encodeURIComponent(params.id) + "/sections", { headers: { Authorization: "Bearer " + stored } })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || "Could not load dossier sections."); return d; })
      .then(d => { setSections(d.items || []); if (d.items?.length) setSectionKey(d.items[0].section_key); })
      .catch(e => setError(e instanceof Error ? e.message : "Unable to load sections."));
  }, [params.id]);

  useEffect(() => {
    const selected = sections.find(s => s.section_key === sectionKey);
    setContentText(JSON.stringify(selected?.content || {}, null, 2));
    setCitationsText(JSON.stringify(selected?.citations || [], null, 2));
    setMediaText(JSON.stringify(selected?.media || [], null, 2));
  }, [sectionKey, sections]);

  async function save(event: FormEvent) {
    event.preventDefault(); if (!token) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const content = JSON.parse(contentText);
      const references = JSON.parse(citationsText);
      const media = JSON.parse(mediaText);
      if (!content || typeof content !== "object" || Array.isArray(content)) throw new Error("Section content must be a JSON object.");
      if (!Array.isArray(references) || !Array.isArray(media)) throw new Error("Citations and media must be JSON arrays.");
      const response = await fetch(API + "/api/v1/dossiers/candidates/" + encodeURIComponent(params.id) + "/sections/" + encodeURIComponent(sectionKey), {
        method: "PUT", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify({ content, references, media }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Section could not be saved.");
      setNotice(result.notice || "Section saved.");
      const reload = await fetch(API + "/api/v1/dossiers/candidates/" + encodeURIComponent(params.id) + "/sections", { headers: { Authorization: "Bearer " + token } });
      const data = await reload.json(); setSections(data.items || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Save failed."); }
    finally { setBusy(false); }
  }

  const field = "w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs leading-6 text-slate-100 outline-none focus:border-emerald-400";
  const current = sections.find(s => s.section_key === sectionKey);
  return <main className="container min-h-screen py-10">
    <Link href={"/peptide-discovery/" + params.id} className="text-sm text-emerald-300">← Back to peptide dossier</Link>
    <header className="mt-8 max-w-3xl"><p className="accent text-xs tracking-widest">INDEPENDENT DOSSIER EDITOR</p><h1 className="mt-3 text-4xl font-semibold">Edit scientific sections</h1><p className="muted mt-3 leading-7">Each section has its own content, claim-level citations and image/structure assets. Saving creates an immutable revision. Use the source URL and exact locator for every factual claim.</p></header>
    {!token && <p className="panel mt-6 p-5 text-sm">Please sign in through the peptide discovery workspace, then reopen this editor.</p>}
    {token && <form onSubmit={save} className="mt-8 space-y-5">
      <section className="panel p-5">
        <label className="block text-sm font-medium">Dossier section</label>
        <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm" value={sectionKey} onChange={e=>setSectionKey(e.target.value)}>
          {Object.entries(starter).map(([key,label])=><option key={key} value={key}>{label}</option>)}
          {sections.filter(s=>!(s.section_key in starter)).map(s=><option key={s.section_key} value={s.section_key}>{s.section_key}</option>)}
        </select>
        <p className="muted mt-2 text-xs">Current revision: {current?.revision ?? "Not created yet"}</p>
      </section>
      <section className="panel p-5">
        <h2 className="font-semibold">Scientific information</h2><p className="muted mt-1 text-xs">JSON object. Add only facts supported by the citations below.</p>
        <textarea className={field + " mt-3 min-h-56"} spellCheck={false} value={contentText} onChange={e=>setContentText(e.target.value)} />
      </section>
      <section className="panel p-5">
        <h2 className="font-semibold">References and claim sources</h2><p className="muted mt-1 text-xs">Array of objects: title, source_name, url, DOI, PMID, registry_id, locator, evidence_type, notes.</p>
        <textarea className={field + " mt-3 min-h-48"} spellCheck={false} value={citationsText} onChange={e=>setCitationsText(e.target.value)} />
      </section>
      <section className="panel p-5">
        <h2 className="font-semibold">Images and structure assets</h2><p className="muted mt-1 text-xs">Array of objects: title, image_url, asset_type, caption, alt_text, source_name, source_identifier, attribution, license_or_reuse_terms, is_prediction.</p>
        <textarea className={field + " mt-3 min-h-48"} spellCheck={false} value={mediaText} onChange={e=>setMediaText(e.target.value)} />
      </section>
      <div className="flex flex-wrap items-center gap-3"><button disabled={busy} className="rounded-full bg-emerald-400 px-6 py-3 font-semibold text-slate-950 disabled:opacity-50">{busy ? "Saving…" : "Save section and create revision"}</button>{notice && <span role="status" className="text-sm text-emerald-300">{notice}</span>}</div>
      {error && <p role="alert" className="rounded-xl border border-rose-800 bg-rose-950/30 p-4 text-sm text-rose-200">{error}</p>}
    </form>}
  </main>;
}

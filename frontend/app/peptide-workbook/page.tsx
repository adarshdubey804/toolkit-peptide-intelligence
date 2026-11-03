"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { getAccessToken, getPreferredOrganizationId, setAccessToken, setPreferredOrganizationId } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
type ImportedItem = { candidate_id: string; name: string; worksheet_row: number };

export default function PeptideWorkbookImportPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [items, setItems] = useState<ImportedItem[]>([]);
  const [workbookMetadata, setWorkbookMetadata] = useState<Record<string, unknown>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { const saved = getAccessToken(); if (saved) setToken(saved); }, []);

  async function signIn(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch(API + "/api/v1/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, organization_id: getPreferredOrganizationId() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Sign in failed.");
      if (!["organization_admin", "curator", "researcher"].includes(data.user.role)) throw new Error("A researcher, curator or organization administrator role is required.");
      setPreferredOrganizationId(data.user.organization_id); setAccessToken(data.access_token); setToken(data.access_token); setPassword("");
    } catch (e) { setError(e instanceof Error ? e.message : "Sign in failed."); }
    finally { setBusy(false); }
  }

  async function upload(event: FormEvent) {
    event.preventDefault(); if (!token || !file) return;
    setBusy(true); setError(""); setNotice(""); setItems([]);
    try {
      const body = new FormData(); body.append("file", file);
      const response = await fetch(API + "/api/v1/dossiers/import-workbook", {
        method: "POST", headers: { Authorization: "Bearer " + token }, body,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Workbook import failed.");
      setItems(data.items || []);
      setWorkbookMetadata(data.workbook_metadata || {});
      setNotice(`Imported ${data.imported_count} independent peptide discovery folders. Batch: ${data.batch_id}`);
    } catch (e) { setError(e instanceof Error ? e.message : "Workbook import failed."); }
    finally { setBusy(false); }
  }

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-8 max-w-3xl"><p className="accent text-xs tracking-widest">CATALOGUE INGESTION</p><h1 className="mt-3 text-4xl font-semibold">Import peptide workbook</h1><p className="muted mt-4 leading-7">Upload the peptide catalogue workbook. Each populated row is preserved as its own source-linked, editable discovery folder, ready for identity resolution and scientific curation.</p></header>
    {!token ? <form onSubmit={signIn} className="panel mt-8 max-w-xl space-y-4 p-6">
      <h2 className="text-lg font-semibold">Research workspace sign in</h2>
      <label className="block text-sm">Email<input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-3" type="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>
      <label className="block text-sm">Password<input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-3" type="password" required value={password} onChange={e=>setPassword(e.target.value)} /></label>
      <button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50">{busy ? "Signing in…" : "Sign in"}</button>
    </form> : <form onSubmit={upload} className="panel mt-8 max-w-3xl space-y-5 p-6">
      <div><h2 className="text-lg font-semibold">Choose .xlsx file</h2><p className="muted mt-1 text-sm">Expected worksheet: Peptides. Maximum file size: 15 MB.</p></div>
      <input type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required onChange={e=>setFile(e.target.files?.[0] || null)} className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-slate-700 file:px-4 file:py-2 file:text-white" />
      <button disabled={busy || !file} className="rounded-full bg-emerald-400 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50">{busy ? "Importing rows…" : "Import and create peptide folders"}</button>
    </form>}
    {error && <p role="alert" className="mt-5 rounded-xl border border-rose-800 bg-rose-950/30 p-4 text-sm text-rose-200">{error}</p>}
    {notice && <p role="status" className="mt-5 rounded-xl border border-emerald-800 bg-emerald-950/30 p-4 text-sm text-emerald-200">{notice}</p>}
    {Object.keys(workbookMetadata).length > 0 && <section className="panel mt-8 max-w-4xl p-5">
      <h2 className="font-semibold">Preserved summary and source worksheets</h2>
      <p className="muted mt-1 text-xs">These companion sheets are retained exactly as workbook observations. Their citations still require claim-level matching and verification.</p>
      {Object.entries(workbookMetadata).map(([sheet, rows])=><details key={sheet} className="mt-4 rounded-xl border border-slate-700 p-4">
        <summary className="cursor-pointer text-sm font-medium">{sheet}</summary>
        <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs text-slate-300">{JSON.stringify(rows, null, 2)}</pre>
      </details>)}
    </section>}
    {items.length > 0 && <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">Created discovery folders</h2><Link href="/peptide-discovery" className="text-sm text-emerald-300">Open discovery workspace →</Link></div><div className="grid gap-3 sm:grid-cols-2">{items.map(item=><article key={item.candidate_id} className="panel flex items-center justify-between gap-4 p-4"><div><h3 className="font-medium">{item.name}</h3><p className="muted mt-1 text-xs">Workbook row {item.worksheet_row} · Awaiting scientific review</p></div><Link className="shrink-0 text-sm text-emerald-300" href={`/peptide-discovery/${item.candidate_id}`}>Open folder →</Link></article>)}</div></section>}
    <aside className="panel mt-8 max-w-3xl p-5"><h2 className="font-semibold">Scientific integrity</h2><p className="muted mt-2 text-sm leading-6">Workbook values are preserved as user-supplied source observations. They are not treated as verified FDA status, clinical evidence, sequence, mechanism of action or safety findings. Missing information remains explicitly uncurated until supported by references.</p></aside>
  </main>;
}

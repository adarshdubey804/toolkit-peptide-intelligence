"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type Capability = {
  service_id: string;
  service_name: string;
  capability_description: string;
  site_id?: string | null;
  site_name?: string | null;
  site_address?: string | null;
  link_id: string;
  relationship_type: string;
  evidence_scope: string;
  limitations: string;
  peptide_id?: string | null;
  peptide_name?: string | null;
  method_id?: string | null;
  method_name?: string | null;
  source_name: string;
  source_identifier: string;
  source_url: string;
};

export default function VendorCapabilitiesPage() {
  const params = useParams<{ vendor_id: string }>();
  const vendorId = params.vendor_id;
  const [vendorName, setVendorName] = useState("");
  const [items, setItems] = useState<Capability[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true); setError("");
      try {
        const response = await fetch(API + "/api/v1/vendors/" + encodeURIComponent(vendorId) + "/capabilities");
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Verified capability records could not be loaded.");
        if (active) { setVendorName(data.vendor?.legal_name || "Verified vendor"); setItems(data.items || []); }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Capability request failed.");
      } finally { if (active) setLoading(false); }
    }
    if (vendorId) void load();
    return () => { active = false; };
  }, [vendorId]);

  return <main className="container min-h-screen py-10">
    <Link href="/vendors" className="text-sm text-emerald-300">← Vendor directory</Link>
    <header className="mt-8 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">SOURCE-VERIFIED PROVIDER CAPABILITIES</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">{vendorName || "Vendor capabilities"}</h1>
      <p className="muted mt-4 leading-7">This page lists only service-to-peptide and service-to-method relationships that have passed independent curation. Each relationship retains its own source and limitations.</p>
    </header>
    {loading && <p className="muted mt-8 text-sm">Loading verified capability evidence…</p>}
    {error && <div role="alert" className="mt-6 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</div>}
    {!loading && !error && items.length===0 && <div className="panel mt-8 p-7"><h2 className="font-semibold">No verified capability links yet</h2><p className="muted mt-2 text-sm">The vendor may have verified services, but no source-backed peptide or analytical-method relationships have been independently approved.</p></div>}
    <section className="mt-8 grid gap-4 md:grid-cols-2">
      {items.map(item=><article key={item.link_id} className="panel p-5">
        <div className="flex items-start justify-between gap-3"><h2 className="text-lg font-semibold">{item.service_name}</h2><span className="rounded-full border border-emerald-400/40 px-3 py-1 text-xs text-emerald-200">Verified link</span></div>
        <p className="muted mt-2 text-sm">{item.capability_description}</p>
        <div className="mt-3 rounded-lg border border-slate-700 p-3"><p className="text-xs font-semibold">Verified facility</p><p className="mt-1 text-sm">{item.site_name || "Facility not recorded"}</p><p className="muted mt-1 text-xs">{item.site_address || "Facility address not established"}</p></div>
        <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-300">{item.relationship_type.replaceAll("_"," ")}</p>
        {(item.peptide_name || item.method_name) && <div className="mt-3 space-y-2 text-sm">
          {item.peptide_name && <p><span className="muted">Peptide: </span>{item.peptide_name}</p>}
          {item.method_name && <p><span className="muted">Analytical method: </span>{item.method_name}</p>}
        </div>}
        <div className="mt-4 border-t border-slate-700 pt-3"><p className="text-xs font-semibold">Evidence scope</p><p className="muted mt-1 text-sm">{item.evidence_scope}</p><p className="mt-3 text-xs font-semibold">Limitations</p><p className="muted mt-1 text-sm">{item.limitations}</p></div>
        <a className="mt-4 inline-block break-all text-xs text-emerald-300 underline" href={item.source_url} target="_blank" rel="noreferrer">Source: {item.source_name} · {item.source_identifier} ↗</a>
      </article>)}
    </section>
    <div className="panel mt-8 p-5"><h2 className="font-semibold">Interpretation boundary</h2><p className="muted mt-2 text-sm leading-6">A verified relationship means the submitted source was reviewed for the stated scope. It does not guarantee current inventory, supply availability, manufacturing quality, test performance, method validation, regulatory approval or suitability for all peptide modifications and sample matrices.</p></div>
  </main>;
}

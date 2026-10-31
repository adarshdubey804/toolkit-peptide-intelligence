"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type Profile = {
  peptide: { id: string; preferred_name: string; peptide_category?: string | null; description?: string | null; development_status?: string | null; intended_use_class: string };
  aliases: { alias: string }[];
  sequences: { sequence: string; sequence_type: string; modifications: unknown[] }[];
  chemical_properties: { chemical_form?: string; molecular_formula?: string; average_molecular_mass?: number; monoisotopic_mass?: number; property_origin: string; method_or_tool?: string }[];
  structures: { structure_type: string; external_identifier?: string; method_or_prediction_tool?: string }[];
  evidence_claims: { id: string; claim_text: string; claim_domain: string; evidence_type: string; confidence_label: string; limitations?: string; doi?: string; pmid?: string; publication_title?: string; publication_url?: string }[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="panel p-5"><h2 className="text-lg font-semibold">{title}</h2><div className="mt-4">{children}</div></section>;
}

export default function PeptideProfilePage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${API_BASE}/api/v1/peptides/${encodeURIComponent(params.id)}`, { signal: controller.signal });
        if (response.status === 404) throw new Error("This peptide profile is not available as a verified public record.");
        if (!response.ok) throw new Error("Unable to retrieve the peptide profile.");
        setProfile(await response.json());
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Unexpected profile error.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, [params.id]);

  if (loading) return <main className="container py-12"><p className="muted">Loading scientific profile…</p></main>;
  if (error || !profile) return <main className="container py-12"><Link href="/peptides" className="text-sm text-emerald-300">← Back to peptide database</Link><div role="alert" className="panel mt-8 p-6 text-sm text-rose-200">{error || "Profile not found."}</div></main>;

  const peptide = profile.peptide;
  return <main className="container min-h-screen py-10">
    <Link href="/peptides" className="text-sm text-emerald-300 hover:text-emerald-200">← Peptide database</Link>
    <header className="mt-9 max-w-4xl"><span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">Curator verified</span><h1 className="mt-4 text-4xl font-semibold md:text-5xl">{peptide.preferred_name}</h1><p className="muted mt-4 leading-7">{peptide.description || "No curated description available."}</p><div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-400">{peptide.peptide_category && <span className="rounded-full border border-slate-700 px-3 py-1">{peptide.peptide_category}</span>}<span className="rounded-full border border-slate-700 px-3 py-1">{peptide.intended_use_class}</span>{peptide.development_status && <span className="rounded-full border border-slate-700 px-3 py-1">{peptide.development_status}</span>}</div></header>
    <div className="mt-8 grid gap-4 lg:grid-cols-2">
      <Section title="Aliases">{profile.aliases.length ? <ul className="flex flex-wrap gap-2">{profile.aliases.map((item) => <li key={item.alias} className="rounded-full border border-slate-700 px-3 py-1 text-sm">{item.alias}</li>)}</ul> : <p className="muted text-sm">No reviewed aliases recorded.</p>}</Section>
      <Section title="Sequence and modifications">{profile.sequences.length ? profile.sequences.map((item,index)=><div key={index} className="mb-3"><p className="text-xs text-slate-400">{item.sequence_type}</p><p className="mt-1 break-all font-mono text-sm">{item.sequence}</p><p className="muted mt-1 text-xs">Modifications: {item.modifications?.length ? JSON.stringify(item.modifications) : "None recorded"}</p></div>) : <p className="muted text-sm">No reviewed sequence data.</p>}</Section>
      <Section title="Chemical properties">{profile.chemical_properties.length ? profile.chemical_properties.map((item,index)=><dl key={index} className="grid grid-cols-2 gap-3 text-sm"><dt className="muted">Chemical form</dt><dd>{item.chemical_form || "Not reported"}</dd><dt className="muted">Formula</dt><dd>{item.molecular_formula || "Not reported"}</dd><dt className="muted">Average mass</dt><dd>{item.average_molecular_mass ?? "Not reported"}</dd><dt className="muted">Monoisotopic mass</dt><dd>{item.monoisotopic_mass ?? "Not reported"}</dd><dt className="muted">Origin</dt><dd>{item.property_origin}</dd><dt className="muted">Method/tool</dt><dd>{item.method_or_tool || "Not reported"}</dd></dl>) : <p className="muted text-sm">No reviewed chemical properties.</p>}</Section>
      <Section title="Structure references">{profile.structures.length ? profile.structures.map((item,index)=><div key={index} className="mb-2 text-sm"><p>{item.structure_type}</p><p className="muted text-xs">{item.external_identifier || "No external identifier"} · {item.method_or_prediction_tool || "Method not reported"}</p></div>) : <p className="muted text-sm">No reviewed structure records.</p>}</Section>
    </div>
    <Section title="Evidence claims">
      {profile.evidence_claims.length ? <div className="space-y-4">{profile.evidence_claims.map((claim)=><article key={claim.id} className="border-b border-slate-800 pb-4 last:border-0"><div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-wide text-emerald-300"><span>{claim.evidence_type}</span><span>·</span><span>{claim.claim_domain}</span></div><p className="mt-2 text-sm leading-6">{claim.claim_text}</p><p className="muted mt-2 text-xs">Confidence: {claim.confidence_label}. {claim.limitations || "No limitations statement supplied."}</p>{claim.publication_url && <a href={claim.publication_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-300">{claim.publication_title || "Source publication"} ↗</a>}</article>)}</div> : <p className="muted text-sm">No reviewed evidence claims are currently linked to this profile.</p>}
    </Section>
    <p className="muted mt-8 text-xs">A curator-verified record is not a clinical recommendation, proof of efficacy, or confirmation of regulatory approval. Evidence must be interpreted in its original study context.</p>
  </main>;
}

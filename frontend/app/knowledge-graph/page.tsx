"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Peptide = { id: string; preferred_name: string; peptide_category?: string | null };
type GraphNode = { id: string; label: string; type: string; review_status: string; metadata?: Record<string, unknown> };
type GraphEdge = { source: string; target: string; relationship: string; evidence_type: string; source_record_id?: string | null };
type Related = { id: string; preferred_name: string; peptide_category?: string; connection_type: string; shared_entity_name: string; shared_connection_count: number };
type Graph = { peptide_id: string; nodes: GraphNode[]; edges: GraphEdge[]; counts: { nodes: number; edges: number; targets: number; pathways: number; publications: number }; scope: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const nodeColors: Record<string, string> = {
  peptide: "#34d399", sequence: "#60a5fa", target: "#c084fc",
  pathway: "#fbbf24", structure: "#22d3ee", evidence_claim: "#fb923c", publication: "#f472b6",
  analytical_method: "#818cf8", formulation: "#fb923c", stability_observation: "#facc15",
  process_knowledge: "#2dd4bf", process_stage: "#14b8a6", interaction_assessment: "#e879f9",
  evidence_appraisal: "#a3e635", source: "#94a3b8",
};

export default function KnowledgeGraphPage() {
  const [peptides, setPeptides] = useState<Peptide[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Peptide | null>(null);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [error, setError] = useState("");\n  const [related, setRelated] = useState<Related[]>([]);\n  const [evidenceFilter, setEvidenceFilter] = useState("all");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/api/v1/peptides?limit=100&offset=0`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("Could not load the verified peptide catalogue."); return response.json(); })
      .then((data) => setPeptides(data.items || []))
      .catch((err) => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Catalogue error."); })
      .finally(() => { if (!controller.signal.aborted) setLoadingList(false); });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selected) { setGraph(null); return; }
    const controller = new AbortController();
    setLoadingGraph(true);
    setError("");
    fetch(`${API_BASE}/api/v1/peptides/${encodeURIComponent(selected.id)}/graph`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("Unable to load this peptide's verified knowledge graph."); return response.json(); })
      .then((data) => setGraph(data))
      .catch((err) => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Graph error."); })
      .finally(() => { if (!controller.signal.aborted) setLoadingGraph(false); });
    return () => controller.abort();
  }, [selected]);


  useEffect(() => {
    if (!selected) { setRelated([]); return; }
    const controller = new AbortController();
    fetch(`${API_BASE}/api/v1/peptides/${encodeURIComponent(selected.id)}/graph/related?limit=50`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("Related peptide lookup failed."); return response.json(); })
      .then((data) => setRelated(data.items || []))
      .catch(() => { if (!controller.signal.aborted) setRelated([]); });
    return () => controller.abort();
  }, [selected]);

  const filtered = useMemo(() => peptides.filter((item) => item.preferred_name.toLowerCase().includes(query.toLowerCase())), [peptides, query]);
  const positioned = useMemo(() => {
    if (!graph) return [];
    const center = graph.nodes.find((node) => node.type === "peptide");
    const others = graph.nodes.filter((node) => node.type !== "peptide");
    return [
      ...(center ? [{ ...center, x: 450, y: 290 }] : []),
      ...others.map((node, index) => {
        const angle = (2 * Math.PI * index) / Math.max(others.length, 1) - Math.PI / 2;
        const radius = others.length > 14 ? 230 : 190;
        return { ...node, x: 450 + Math.cos(angle) * radius, y: 290 + Math.sin(angle) * radius };
      }),
    ];
  }, [graph]);
  const coordinates = useMemo(() => new Map(positioned.map((node) => [node.id, node])), [positioned]);\n  const visibleEdges = useMemo(() => graph?.edges.filter((edge) => evidenceFilter === "all" || edge.evidence_type === evidenceFilter) || [], [graph, evidenceFilter]);

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300 hover:text-emerald-200">← Toolkit home</Link>
    <header className="mt-9 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">CONNECTED SCIENTIFIC INTELLIGENCE</p>
      <h1 className="mt-3 text-4xl font-semibold md:text-5xl">Peptide knowledge graph</h1>
      <p className="muted mt-4 leading-7">Explore curator-verified connections across peptide identity, sequences, targets, pathways, structures, publications, analytical methods, formulation observations, process knowledge and molecular interaction assessments.</p>
    </header>

    <section className="panel mt-8 p-5">
      <label className="block text-xs text-slate-400">Select a verified peptide</label>
      <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter peptide names…" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-emerald-400" />
      <div className="mt-3 flex flex-wrap gap-2">
        {loadingList && <span className="muted text-sm">Loading verified catalogue…</span>}
        {!loadingList && filtered.slice(0, 20).map((item) => <button key={item.id} onClick={() => setSelected(item)} className={`rounded-full border px-3 py-2 text-xs transition ${selected?.id === item.id ? "border-emerald-300 bg-emerald-300/10 text-emerald-200" : "border-slate-700 text-slate-300 hover:border-emerald-400"}`}>{item.preferred_name}</button>)}
        {!loadingList && peptides.length === 0 && <span className="muted text-sm">No verified peptide records are currently available.</span>}
      </div>
    </section>

    {error && <div role="alert" className="mt-4 rounded-xl border border-rose-400/30 bg-rose-400/5 p-4 text-sm text-rose-200">{error}</div>}
    {!selected && <div className="panel mt-5 p-10 text-center"><h2 className="text-lg font-semibold">Choose a peptide to explore</h2><p className="muted mt-2 text-sm">Only verified catalogue entries can be explored.</p></div>}
    {selected && <section className="mt-5">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <div><p className="accent text-xs tracking-widest">SELECTED ENTITY</p><h2 className="mt-1 text-2xl font-semibold">{selected.preferred_name}</h2></div>
        {graph && <div className="flex flex-wrap gap-2 text-xs text-slate-300"><span className="rounded-full border border-slate-700 px-3 py-1">{graph.counts.nodes} nodes</span><span className="rounded-full border border-slate-700 px-3 py-1">{graph.counts.edges} relationships</span><span className="rounded-full border border-slate-700 px-3 py-1">{graph.counts.publications} publications</span></div>}
      </div>
      {loadingGraph && <div className="panel p-8 text-sm muted">Building verified relationship graph…</div>}
      {graph && <div className="panel overflow-hidden p-3 md:p-5">\n        <label className="mb-3 flex items-center gap-3 text-xs text-slate-300">Evidence filter <select value={evidenceFilter} onChange={(event) => setEvidenceFilter(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"><option value="all">All evidence types</option>{Array.from(new Set(graph.edges.map((edge) => edge.evidence_type))).map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}</select></label>
        {visibleEdges.length === 0 ? <div className="p-10 text-center"><h3 className="font-semibold">No verified relationships recorded yet</h3><p className="muted mt-2 text-sm">This does not mean no biological relationships exist. It means none have passed curation in this platform.</p></div> : <>
          <div className="overflow-x-auto">
            <svg viewBox="0 0 900 580" role="img" aria-label={`Knowledge graph for ${selected.preferred_name}`} className="mx-auto min-w-[720px] w-full">
              {visibleEdges.map((edge, index) => {
                const from = coordinates.get(edge.source); const to = coordinates.get(edge.target);
                if (!from || !to) return null;
                return <g key={`${edge.source}-${edge.target}-${index}`}><line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#536779" strokeWidth="1.5" opacity=".8" /><title>{edge.relationship} · {edge.evidence_type}</title></g>;
              })}
              {positioned.map((node) => <g key={node.id}>
                <circle cx={node.x} cy={node.y} r={node.type === "peptide" ? 43 : 29} fill={nodeColors[node.type] || "#94a3b8"} fillOpacity=".16" stroke={nodeColors[node.type] || "#94a3b8"} strokeWidth={node.type === "peptide" ? 3 : 1.7} />
                <text x={node.x} y={node.y + 4} textAnchor="middle" fill="#edf5f8" fontSize={node.type === "peptide" ? 11 : 9}>{node.label.length > 17 ? node.label.slice(0, 16) + "…" : node.label}</text>
                <title>{node.type}: {node.label}</title>
              </g>)}
            </svg>
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 border-t border-slate-800 pt-4">{Object.entries(nodeColors).map(([type, color]) => <span key={type} className="flex items-center gap-2 text-xs text-slate-300"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{type.replace("_", " ")}</span>)}</div>
        </>}
        <p className="muted mt-4 text-xs leading-5">{graph.scope}</p>
      </div>}
      {graph && graph.edges.length > 0 && <div className="mt-4 grid gap-3 md:grid-cols-2">
        {graph.edges.map((edge, index) => {
          const source = graph.nodes.find((node) => node.id === edge.source);
          const target = graph.nodes.find((node) => node.id === edge.target);
          return <article key={index} className="panel p-4"><p className="text-sm font-medium">{source?.label} <span className="accent">→</span> {target?.label}</p><p className="muted mt-2 text-xs">{edge.relationship.replaceAll("_", " ")} · {edge.evidence_type.replaceAll("_", " ")} · curator verified</p></article>;
        })}
      </div>}
    </section>}
    <p className="muted mt-10 border-t border-slate-800 pt-5 text-xs">A displayed relationship reflects a curated database record, not proof of causality, clinical efficacy or regulatory approval.</p>
  </main>;
}

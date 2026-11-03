import Link from "next/link";

type Source = {
  name: string;
  domain: string;
  coverage: string;
  access: string;
  status: "Integrated" | "Integrated · credentials required" | "Link-out only";
  limitation: string;
};

const sources: Source[] = [
  { name: "FDA Drugs@FDA / openFDA", domain: "United States · drug products", coverage: "Drug application and product records, including source-native approval actions where available.", access: "Read-only API discovery", status: "Integrated", limitation: "Does not cover every biologic in the same way as CBER sources. A source search is not a global peptide census." },
  { name: "FDA Purple Book", domain: "United States · biological products", coverage: "CBER-licensed biological products, including reference products, biosimilars and interchangeable products.", access: "Read-only source snapshot", status: "Integrated", limitation: "Reconcile exact BLA, product and active ingredient with other FDA records. Snapshot date and source-native status must be retained." },
  { name: "NLM DailyMed SPL", domain: "United States · structured labels", coverage: "Structured product labeling, label versions and explicit section text, including Section 12.1 when present.", access: "Read-only API and SPL XML", status: "Integrated", limitation: "DailyMed presence is not proof of FDA approval and current SPL text may differ from the last FDA-approved label." },
  { name: "Health Canada Drug Product Database", domain: "Canada · drug products", coverage: "Drug Identification Numbers, product class, ingredients, strengths, dosage forms, routes and source-native status records.", access: "Read-only JSON/XML source", status: "Integrated", limitation: "Includes human and non-human product classes. Preserve the source status; do not translate it into an FDA status." },
  { name: "EMA Article 57 product snapshot", domain: "European Economic Area · medicinal products", coverage: "Published snapshot of products with valid marketing authorisations in the EEA at the time represented by the file.", access: "Read-only downloadable snapshot", status: "Integrated", limitation: "Not a complete register of refused, withdrawn, investigational or never-authorised products; confirm country-specific status with national authorities." },
  { name: "ClinicalTrials.gov", domain: "International · clinical studies", coverage: "Registered interventional and observational study records, statuses, sponsors and study descriptions.", access: "Read-only API", status: "Integrated", limitation: "A trial record is not marketing authorisation and does not prove efficacy or safety." },
  { name: "PubMed", domain: "International · biomedical literature", coverage: "Bibliographic records and abstracts for biomedical research.", access: "NCBI E-utilities; configuration may be required", status: "Integrated", limitation: "Literature discovery is not regulatory approval. Abstract text is not a substitute for full-text appraisal." },
  { name: "IUPHAR/BPS Guide to PHARMACOLOGY", domain: "International · expert pharmacology", coverage: "Expert-curated ligand, target and interaction records, including peptide ligands.", access: "Read-only API", status: "Integrated · credentials required", limitation: "Requires a registered API key. Database ODbL and content CC BY-SA obligations must be reviewed before redistribution." },
  { name: "DBAASP v4", domain: "International · antimicrobial peptides", coverage: "Peptide sequences, chemical modifications, target activity, antibiofilm, cytotoxicity, experimental combinations and linked references.", access: "Read-only API", status: "Integrated", limitation: "Domain-specific antimicrobial peptide coverage, not a complete peptide inventory. Preserve assay conditions and attribution." },
  { name: "DRAMP 5.0", domain: "International · antimicrobial peptides", coverage: "Curated antimicrobial peptide sequence datasets and selected sequence/SMILES exports.", access: "Read-only published data snapshots", status: "Integrated", limitation: "Antimicrobial peptide scope only. Patent dataset exports are excluded pending separate permission; source release and attribution are retained." },
  { name: "UniProt", domain: "International · protein sequence and function", coverage: "Protein sequence, organism and functional annotation cross-references.", access: "Read-only API", status: "Integrated", limitation: "Protein records are not automatically equivalent to therapeutic peptide products or synthetic peptide forms." },
  { name: "RCSB Protein Data Bank", domain: "International · macromolecular structures", coverage: "Experimental and computed structural entries and related metadata.", access: "Read-only API", status: "Integrated", limitation: "A structure match requires sequence/entity and construct review; structure presence does not prove a therapeutic mechanism." },
  { name: "PubChem", domain: "International · chemical identity", coverage: "Chemical identifiers, structures and physicochemical records where available.", access: "Read-only API", status: "Integrated", limitation: "Chemical name similarity is not enough to establish peptide sequence or product identity." },
  { name: "Antimicrobial Peptide Database (APD6)", domain: "International · antimicrobial peptide research", coverage: "External specialist database for antimicrobial peptide research.", access: "External source link", status: "Link-out only", limitation: "No bulk ingestion or copied dataset. Users must consult APD6 terms and the original record." },
];

const groups = ["Regulatory product sources", "Clinical and literature sources", "Scientific peptide and molecular resources"];
function groupFor(source: Source) {
  if (source.domain.includes("United States") || source.domain.includes("Canada") || source.domain.includes("European Economic Area")) return groups[0];
  if (source.domain.includes("clinical") || source.domain.includes("biomedical")) return groups[1];
  return groups[2];
}

export default function SourceCoveragePage() {
  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-8 max-w-4xl">
      <p className="accent text-xs tracking-[.2em]">GLOBAL SOURCE REGISTER</p>
      <h1 className="mt-3 text-4xl font-semibold">Source coverage & limitations</h1>
      <p className="muted mt-4 text-sm leading-7">A transparent register of the external sources connected to peptide discovery. It explains what each source contributes, how it is accessed and what it cannot establish. This is a source coverage map, not a claim that every peptide in the world has been captured.</p>
    </header>
    <section className="panel mt-7 p-5">
      <h2 className="font-semibold">How to interpret coverage</h2>
      <ul className="muted mt-3 list-disc space-y-2 pl-5 text-sm leading-6">
        <li>Regulatory authorisation is specific to the exact product, active ingredient or chemical form, jurisdiction, indication, route, dosage form and effective period.</li>
        <li>A search miss means only that the record was not found in the checked source using that query and retrieval date. It does not establish non-approval.</li>
        <li>Research database records, trial registrations, publications, labels and regulatory authorisations are different evidence classes.</li>
        <li>Source observations remain unreviewed until identity, source context and evidence are checked through the curation workflow.</li>
      </ul>
    </section>
    {groups.map(group => <section key={group} className="mt-9">
      <h2 className="text-xl font-semibold">{group}</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {sources.filter(source => groupFor(source) === group).map(source => <article key={source.name} className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs text-emerald-300">{source.domain}</span>
            <span className="rounded-full border border-slate-700 px-2 py-1 text-[11px] text-slate-300">{source.status}</span>
          </div>
          <h3 className="mt-3 text-lg font-semibold">{source.name}</h3>
          <p className="mt-3 text-sm leading-6 text-slate-300">{source.coverage}</p>
          <p className="muted mt-3 text-xs">Access: {source.access}</p>
          <p className="muted mt-2 text-xs leading-5">Limitations: {source.limitation}</p>
        </article>)}
      </div>
    </section>)}
    <section className="panel mt-9 p-5">
      <h2 className="font-semibold">Coverage expansion policy</h2>
      <p className="muted mt-2 text-sm leading-6">Additional national regulators and specialist databases will be added through versioned adapters after access terms, licensing, stable identifiers, pagination completeness, update cadence and source-native status semantics are documented. Planned sources are not displayed as integrated until the adapter and its tests are merged.</p>
      <Link href="/peptide-discovery" className="mt-4 inline-block text-sm text-emerald-300 underline">Open global peptide discovery →</Link>
    </section>
  </main>;
}

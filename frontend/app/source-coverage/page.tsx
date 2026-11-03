import Link from "next/link";

type Source = {
  name: string;
  url: string;
  domain: string;
  coverage: string;
  access: string;
  status: "Integrated" | "Integrated · credentials required" | "Link-out only";
  limitation: string;
};

const sources: Source[] = [
  { name: "MHRA Products (United Kingdom)", url: "https://products.mhra.gov.uk/", domain: "United Kingdom · national medicines", coverage: "Nationally licensed medicine product information, active-substance search, Product Licence numbers, Summaries of Product Characteristics, Patient Information Leaflets and published assessment reports.", access: "Official public product information search · manual link-out", status: "Link-out only", limitation: "This service covers nationally licensed UK medicines; centrally authorised products should be checked with EMA. Product information can remain visible after cancellation, so confirm current licence status and history." },
  { name: "TGA Australian Register of Therapeutic Goods", url: "https://www.tga.gov.au/products/regulations-all-products/about-australian-register-therapeutic-goods-artg/searching-australian-register-therapeutic-goods-artg", domain: "Australia · therapeutic goods", coverage: "Public ARTG search for therapeutic goods that may legally be supplied in Australia, with product/formulation and sponsor/manufacturer information where published.", access: "Official public ARTG search · manual link-out", status: "Link-out only", limitation: "Some therapeutic goods are exempt from ARTG inclusion. The public search is not a complete census of every product that may lawfully be supplied." },
  { name: "PMDA Japan approved products", url: "https://www.pmda.go.jp/english/review-services/reviews/approved-information/drugs/0002.html", domain: "Japan · approved medicines", coverage: "PMDA published lists of approved drug products and selected review reports; the Japanese product search provides product information and package inserts.", access: "Official public approved-product lists and search · manual link-out", status: "Link-out only", limitation: "English review reports are selective translations; Japanese originals prevail when translations differ. Automated ingestion and product status history are not integrated." },
  { name: "CDSCO India approved drugs / SUGAM", url: "https://cdscoonline.gov.in/CDSCO/cdscoDrugs", domain: "India · national regulatory approvals", coverage: "Official CDSCO approved drugs/vaccines/rDNA/blood-product search portal and published new-drug approval lists. Search results may include product name, composition, dosage, indication, manufacturer and approval date where published.", access: "Official portal and published PDF lists · manual link-out", status: "Link-out only", limitation: "No public documented machine-readable API has been validated for this integration. Do not scrape authenticated SUGAM workflows or treat a search result as a complete national product register; confirm exact product and current status with CDSCO." },
  { name: "FDA Drugs@FDA / openFDA", url: "https://www.accessdata.fda.gov/scripts/cder/daf/", domain: "United States · drug products", coverage: "Drug application and product records, including source-native approval actions where available.", access: "Read-only API discovery", status: "Integrated", limitation: "Does not cover every biologic in the same way as CBER sources. A source search is not a global peptide census." },
  { name: "FDA Purple Book", url: "https://purplebooksearch.fda.gov/", domain: "United States · biological products", coverage: "CBER-licensed biological products, including reference products, biosimilars and interchangeable products.", access: "Read-only source snapshot", status: "Integrated", limitation: "Reconcile exact BLA, product and active ingredient with other FDA records. Snapshot date and source-native status must be retained." },
  { name: "NLM DailyMed SPL", url: "https://dailymed.nlm.nih.gov/dailymed/", domain: "United States · structured labels", coverage: "Structured product labeling, label versions and explicit section text, including Section 12.1 when present.", access: "Read-only API and SPL XML", status: "Integrated", limitation: "DailyMed presence is not proof of FDA approval and current SPL text may differ from the last FDA-approved label." },
  { name: "Health Canada Drug Product Database", url: "https://health-products.canada.ca/dpd-bdpp/index-eng.jsp", domain: "Canada · drug products", coverage: "Drug Identification Numbers, product class, ingredients, strengths, dosage forms, routes and source-native status records.", access: "Read-only JSON/XML source", status: "Integrated", limitation: "Includes human and non-human product classes. Preserve the source status; do not translate it into an FDA status." },
  { name: "EMA Article 57 product snapshot", url: "https://www.ema.europa.eu/en/human-regulatory-overview/marketing-authorisation/medicines-available-european-union", domain: "European Economic Area · medicinal products", coverage: "Published snapshot of products with valid marketing authorisations in the EEA at the time represented by the file.", access: "Read-only downloadable snapshot", status: "Integrated", limitation: "Not a complete register of refused, withdrawn, investigational or never-authorised products; confirm country-specific status with national authorities." },
  { name: "ClinicalTrials.gov", url: "https://clinicaltrials.gov/", domain: "International · clinical studies", coverage: "Registered interventional and observational study records, statuses, sponsors and study descriptions.", access: "Read-only API", status: "Integrated", limitation: "A trial record is not marketing authorisation and does not prove efficacy or safety." },
  { name: "PubMed", url: "https://pubmed.ncbi.nlm.nih.gov/", domain: "International · biomedical literature", coverage: "Bibliographic records and abstracts for biomedical research.", access: "NCBI E-utilities; configuration may be required", status: "Integrated", limitation: "Literature discovery is not regulatory approval. Abstract text is not a substitute for full-text appraisal." },
  { name: "IUPHAR/BPS Guide to PHARMACOLOGY", url: "https://www.guidetopharmacology.org/", domain: "International · expert pharmacology", coverage: "Expert-curated ligand, target and interaction records, including peptide ligands.", access: "Read-only API", status: "Integrated · credentials required", limitation: "Requires a registered API key. Database ODbL and content CC BY-SA obligations must be reviewed before redistribution." },
  { name: "DBAASP v4", url: "https://dbaasp.org/", domain: "International · antimicrobial peptides", coverage: "Peptide sequences, chemical modifications, target activity, antibiofilm, cytotoxicity, experimental combinations and linked references.", access: "Read-only API", status: "Integrated", limitation: "Domain-specific antimicrobial peptide coverage, not a complete peptide inventory. Preserve assay conditions and attribution." },
  { name: "DRAMP 5.0", url: "https://dramp.cpu-bioinfor.org/", domain: "International · antimicrobial peptides", coverage: "Curated antimicrobial peptide sequence datasets and selected sequence/SMILES exports.", access: "Read-only published data snapshots", status: "Integrated", limitation: "Antimicrobial peptide scope only. Patent dataset exports are excluded pending separate permission; source release and attribution are retained." },
  { name: "UniProt", url: "https://www.uniprot.org/", domain: "International · protein sequence and function", coverage: "Protein sequence, organism and functional annotation cross-references.", access: "Read-only API", status: "Integrated", limitation: "Protein records are not automatically equivalent to therapeutic peptide products or synthetic peptide forms." },
  { name: "RCSB Protein Data Bank", url: "https://www.rcsb.org/", domain: "International · macromolecular structures", coverage: "Experimental and computed structural entries and related metadata.", access: "Read-only API", status: "Integrated", limitation: "A structure match requires sequence/entity and construct review; structure presence does not prove a therapeutic mechanism." },
  { name: "PubChem", url: "https://pubchem.ncbi.nlm.nih.gov/", domain: "International · chemical identity", coverage: "Chemical identifiers, structures and physicochemical records where available.", access: "Read-only API", status: "Integrated", limitation: "Chemical name similarity is not enough to establish peptide sequence or product identity." },
  { name: "Antimicrobial Peptide Database (APD6)", url: "https://aps.unmc.edu/", domain: "International · antimicrobial peptide research", coverage: "External specialist database for antimicrobial peptide research.", access: "External source link", status: "Link-out only", limitation: "No bulk ingestion or copied dataset. Users must consult APD6 terms and the original record." },
];

const groups = ["Regulatory product sources", "Clinical and literature sources", "Scientific peptide and molecular resources"];
function groupFor(source: Source) {
  if (source.domain.includes("United States") || source.domain.includes("Canada") || source.domain.includes("European Economic Area") || source.domain.includes("India") || source.domain.includes("United Kingdom") || source.domain.includes("Australia") || source.domain.includes("Japan")) return groups[0];
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
          <h3 className="mt-3 text-lg font-semibold">{source.name}</h3>\n          <a href={source.url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-emerald-300 underline">Open official source ↗</a>
          <p className="mt-3 text-sm leading-6 text-slate-300">{source.coverage}</p>
          <p className="muted mt-3 text-xs">Access: {source.access}</p>
          <p className="muted mt-2 text-xs leading-5">Limitations: {source.limitation}</p>
        </article>)}
      </div>
    </section>)}
    <section className="mt-9">
      <h2 className="text-xl font-semibold">Priority sources under evaluation</h2>
      <p className="muted mt-2 text-sm leading-6">These jurisdictions are part of the global coverage roadmap but are not yet connected as production ingestion adapters. Their official access method, dataset scope, licence and update cadence must be verified before integration.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ["India · CDSCO", "Official approved-drug search and published approval lists are linked above. Automated ingestion remains under evaluation because a public documented API and complete historical/status coverage have not yet been validated."],
          ["United Kingdom · MHRA", "National product authorisation and product-information sources; source access, status semantics and identifier mapping require evaluation."],
          ["Australia · TGA ARTG", "Official ARTG search is linked above. Automated ingestion, bulk access terms and peptide/biologic coverage are not integrated."],
          ["Japan · PMDA / MHLW", "Japanese drug and biologic approval information; official datasets, language handling and product identifiers require evaluation."],
          ["China · NMPA", "Chinese drug and biologic registration information; official publication sources, access constraints and identifier mapping require evaluation."],
          ["Other national authorities", "Additional national and regional regulators will be prioritised after source-access and coverage assessment."]
        ].map(([name, description]) => <article key={name} className="panel p-4">
          <div className="text-xs text-amber-300">Not integrated</div>
          <h3 className="mt-2 font-semibold">{name}</h3>
          <p className="muted mt-2 text-xs leading-5">{description}</p>
        </article>)}
      </div>
    </section>
    <section className="panel mt-9 p-5">
      <h2 className="font-semibold">Coverage expansion policy</h2>
      <p className="muted mt-2 text-sm leading-6">Additional national regulators and specialist databases will be added through versioned adapters after access terms, licensing, stable identifiers, pagination completeness, update cadence and source-native status semantics are documented. Planned sources are not displayed as integrated until the adapter and its tests are merged.</p>
      <Link href="/peptide-discovery" className="mt-4 inline-block text-sm text-emerald-300 underline">Open global peptide discovery →</Link>
    </section>
  </main>;
}

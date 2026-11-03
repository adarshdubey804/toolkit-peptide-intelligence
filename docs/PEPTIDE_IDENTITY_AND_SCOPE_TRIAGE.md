# Peptide identity and scope triage — workbook v1

**Source:** `peptides_fda_status_by_treatment.xlsx`, `Peptides` sheet (128 rows; source values must remain unchanged).
**Status:** triage rules and initial flags only. This is not a completed identity review and must not be presented as a validated peptide-only list.

## Why this gate is required

The workbook is named as a peptide list, but it contains heterogeneous molecular entities. Before a dossier is created, resolve the active moiety and the marketed product separately. Do not infer peptide identity from a therapeutic category, a drug-name suffix, a brand, or an FDA approval flag.

Use one of these controlled classifications:

- `defined_peptide`: a chemically defined amino-acid chain with a supported sequence or authoritative identity record.
- `modified_peptide`: a defined peptide with noncanonical residues, cyclization, lipidation, PEGylation, glycosylation or other covalent modification.
- `peptide_conjugate_or_radioligand`: a peptide covalently linked to a chelator, radionuclide, payload or carrier; describe both components.
- `polypeptide_or_protein`: larger chain, protein, mixture or biologic where the simple peptide label is inadequate.
- `peptide_mixture_or_polymer`: heterogeneous or non-sequence-defined peptide material.
- `non_peptide_or_non_peptide_active_moiety`: not a peptide active moiety; retain only if the project intentionally tracks peptide-adjacent therapeutics.
- `unresolved`: insufficient evidence; do not populate sequence, structure or mechanism by guesswork.

## Initial workbook records requiring explicit scope handling

These are triage flags, not final classifications:

| Workbook entry | Why it needs special handling | Required dossier treatment |
|---|---|---|
| Lutetium Lu 177 dotatate | Radiolabelled somatostatin peptide radioligand | Separate peptide ligand, chelator and radionuclide; cite the official label for sequence and structure |
| Gallium Ga 68 dotatate / dotatoc; Copper Cu 64 dotatate; Indium In 111 pentetreotide | Radiolabelled diagnostic peptide conjugates | Capture peptide identity and radiochemistry as distinct fields |
| Pegulicianine | Fluorescent imaging agent / conjugate; do not assume it is a simple peptide drug | Resolve active imaging moiety and peptide component from the official label |
| Romidepsin | Cyclic depsipeptide natural product; peptide-like chemistry needs explicit structural classification | Record depsipeptide status and exact structure source |
| Melphalan flufenamide | Peptide-conjugated drug (melphalan flufenamide); distinguish peptide carrier/conjugate from payload | Record conjugate architecture and regulatory history separately |
| Glatiramer acetate | Heterogeneous synthetic polypeptide mixture, not a single sequence-defined peptide | Do not invent one amino-acid sequence or one molecular structure |
| Cerebrolysin | Complex peptide mixture derived from porcine brain; not a single defined peptide | Treat as mixture; describe composition limits and jurisdiction-specific status |
| Insulins and other peptide/protein boundary cases | Conventional peptide-length definitions vary; therapeutic proteins may be included by project policy | Declare inclusion rule and chain length/structure source |
| Vancomycin, telavancin, dalbavancin, oritavancin | Glycopeptide/lipoglycopeptide antibiotics | Preserve glycosylation/lipid modifications and antimicrobial mechanism |
| Daptomycin, polymyxin B, colistin | Cyclic/lipopeptide antibiotics | Record lipid tail, cyclic peptide architecture and antimicrobial target |
| Caspofungin, micafungin, anidulafungin, rezafungin | Echinocandin lipopeptide antifungals | Distinguish peptide core and lipid side chain |
| Cyclosporine, voclosporin | Cyclic peptides with extensive noncanonical residues | Do not use standard protein sequence assumptions |
| Glatiramer acetate, Cerebrolysin, MGF/PEG-MGF | Mixture, mixture, and ambiguous product naming respectively | Require exact substance/form identity before sequence assignment |

## Authoritative evidence examples

1. **Gallium Ga 68 edotreotide / DOTATOC:** FDA-approved product label describes edotreotide as a cyclic eight-amino-acid peptide with covalently bound DOTA chelator, gives its sequence, and describes a disulfide bond. This demonstrates why radioligand dossiers need separate peptide and radiochemistry fields. Source: [FDA label, 2023](https://www.accessdata.fda.gov/drugsatfda_docs/label/2023/210828s003lbl.pdf).
2. **Romidepsin:** DailyMed official label identifies the drug as an HDAC inhibitor and gives initial US approval in 2009. Use the label and primary structural literature to document its depsipeptide architecture; do not infer this from the label's pharmacologic class alone. Source: [DailyMed romidepsin label](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=73a2028d-6735-4cd4-b63d-d072df9927a1).
3. **Antimicrobial peptide-based antibiotics:** a peer-reviewed review distinguishes common peptide, glycopeptide, lipopeptide and lipoglycopeptide structures. Source: [FDA-approved antibacterials and echinocandins review (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11851826/).

## Mandatory acceptance criteria per record

- Resolve generic name, synonym, exact salt/ester/conjugate and active moiety.
- Assign one controlled scope classification with a confidence level and reviewer/date.
- Record source and evidence for sequence, residue count, stereochemistry, cyclization, disulfide bonds and noncanonical residues, where applicable.
- Separate peptide ligand from radionuclide, chelator, linker, payload, lipid or PEG component.
- Distinguish official approval of a finished product from compounding status, investigational use, foreign approval and discontinued/withdrawn status.
- Store mechanism claims as claim-level statements with primary/authoritative citations and experimental context.
- If an item is not a peptide, mark it `non_peptide_or_non_peptide_active_moiety` and keep it in a clearly labelled adjacent-therapeutics collection only if product scope requires it.
- Missing or contradictory facts remain `unresolved`; never fill them with generated guesses.

**No workbook entry is marked fully curated by this document.**
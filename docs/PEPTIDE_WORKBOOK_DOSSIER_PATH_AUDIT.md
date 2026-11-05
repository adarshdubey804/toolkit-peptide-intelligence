# Workbook-to-dossier path audit

**Audit date:** 4 November 2026  
**Source:** `peptides_fda_status_by_treatment.xlsx`, `Peptides` worksheet  
**Source row count:** 128 populated names  
**Target:** PR #155, branch `pr-155-128-peptide-dossiers-evidence-media`

## Result

The PR's changed-file inventory was compared with all 128 workbook names. Four workbook rows had no matching dossier path and have now been added as independent folders:

| Workbook entry | Source name | Added dossier |
|---:|---|---|
| 001 | Insulin (human, recombinant) | `docs/dossiers/insulin-human-recombinant/README.md` |
| 015 | Glucagon | `docs/dossiers/glucagon/README.md` |
| 016 | Dasiglucagon | `docs/dossiers/dasiglucagon/README.md` |
| 044 | Palopegteriparatide | `docs/dossiers/palopegteriparatide/README.md` |

Ten workbook entries use an established canonical folder whose slug differs from the literal workbook name. The canonical dossiers were updated with an explicit workbook source mapping instead of creating duplicate folders:

| Workbook entry | Workbook name | Canonical dossier |
|---:|---|---|
| 018 | Cagrilintide (and CagriSema) | `cagrilintide` |
| 038 | Secretin (human / porcine) | `secretin` |
| 054 | CJC-1295 (with/without DAC) | `cjc-1295` |
| 060 | MGF / PEG-MGF | `mgf-peg-mgf` |
| 104 | Thymosin alpha-1 (thymalfasin) | `thymosin-alpha-1` |
| 106 | Aviptadil (vasoactive intestinal peptide) | `aviptadil` |
| 111 | Afamelanotide (Melanotan I) | `afamelanotide` |
| 117 | DSIP (delta sleep-inducing peptide / emideltide) | `dsip` |
| 122 | GHK-Cu (copper tripeptide) | `ghk-cu` |
| 124 | Epitalon (epithalon) | `epitalon` |

The Secretin dossier's prior workbook sequence annotation was corrected from 042 to 038 (Excel row 39).

## Additional legacy dossiers

The changed-file inventory also contains legacy/adjacent dossiers that are not literal workbook rows: `albiglutide`, `efpeglenatide`, `eloralintide`, `exenatide-extended-release`, and `macupatide`. These were not deleted. They may be useful research records, but must remain explicitly outside the 128-row workbook accounting unless separately mapped to an approved future catalogue.

## Important completion boundary

- This is a repository path/mapping audit, not proof that the workbook was imported into a live PostgreSQL deployment.
- The PR's authenticated import endpoint must still be exercised in the target environment with the actual XLSX, then its 128 source observations and organization-scoped folders verified in the database.
- File presence and a workbook cross-reference do not constitute scientific completion. Each factual claim still needs its own source locator and evidence classification.
- The dossiers remain `in_progress`; no unsupported status has been promoted to complete.
- CI for the latest head commit was running at audit time; final results must be checked before declaring the PR validated.


## Follow-up duplicate and numbering audit — 5 November 2026

A subsequent review of the earlier dossier commits and the complete PR #155 changed-file inventory found that these peptide dossiers already exist in the workbook dossier batch:

| Peptide | Existing canonical path in this PR | Existing dossier heading / workbook mapping |
|---|---|---|
| Ipamorelin | `docs/dossiers/ipamorelin/README.md` | Dossier 053; workbook entry 053 |
| CJC-1295 | `docs/dossiers/cjc-1295/README.md` | Dossier 054; workbook entry 054 |
| GHRP-6 | `docs/dossiers/ghrp-6/README.md` | Dossier 055; source sheet row 55 is stated in the dossier |
| GHRP-2 / pralmorelin | `docs/dossiers/ghrp-2/README.md` | Dossier 056; source sheet row 56 is stated in the dossier |
| Hexarelin / examorelin | `docs/dossiers/hexarelin/README.md` | Dossier 057; source sheet row 57 is stated in the dossier |
| Sermorelin | `docs/dossiers/sermorelin/README.md` | Its file labels itself workbook sequence 055 but also says Peptides data row 51 / Excel row 53 |

### Duplicate PRs detected and closed

- PR #156 attempted to add Ipamorelin again at `docs/peptide-dossiers/056-ipamorelin/README.md`. Closed as a duplicate of the existing Ipamorelin dossier above.
- PR #157 attempted to add GHRP-2 / pralmorelin again at `docs/peptide-dossiers/057-ghrp-2-pralmorelin/README.md`. Closed as a duplicate of the existing GHRP-2 dossier above.
- GHRP-6 was already present in the PR #155 inventory; no new GHRP-6 folder should be created.

### Numbering integrity issue

The existing Sermorelin file had used sequence number 055 while the GHRP-6 file is also titled Dossier 055. This was a dossier-number collision, not evidence that Sermorelin and GHRP-6 are the same peptide. Corrected Sermorelin's README heading to `Sermorelin (GEREF)` and retained its stated Peptides worksheet data row 51 / Excel row 53; the unsupported sequence label 055 was removed. Keep canonical identity, workbook row position and stable folder slug as separate identifiers. Do not use a dossier sequence number as a database primary key.

### Scope and remaining checks

- The PR #155 changed-file inventory contains 133 dossier folders, while the workbook contains 128 source rows. The path audit identifies five additional legacy/adjacent folders; these must remain explicitly outside workbook row accounting unless separately mapped.
- The workbook audit reports 128 unique names, but this is not equivalent to chemical-identity deduplication. Salts, conjugates, fragments, peptide-derived compounds and ambiguous names still require identity-level review.
- PR #155 remains the only intended workbook import/dossier batch in this comparison. Its workbook import has not been demonstrated against the deployed database in this audit.
- No claim is made that the 128 dossiers are all scientifically complete or curator-verified.

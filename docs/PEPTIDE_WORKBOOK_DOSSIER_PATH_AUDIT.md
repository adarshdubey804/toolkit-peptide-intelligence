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

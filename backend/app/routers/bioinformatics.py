from collections import Counter
from math import log10

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/v1/bioinformatics", tags=["bioinformatics"])

# Average residue masses (Da) for the 20 standard amino acids.
RESIDUE_MASS = {
    "A": 71.0788, "R": 156.1875, "N": 114.1038, "D": 115.0886,
    "C": 103.1388, "E": 129.1155, "Q": 128.1307, "G": 57.0519,
    "H": 137.1411, "I": 113.1594, "L": 113.1594, "K": 128.1741,
    "M": 131.1926, "F": 147.1766, "P": 97.1167, "S": 87.0782,
    "T": 101.1051, "W": 186.2132, "Y": 163.1760, "V": 99.1326,
}
MONOISOTOPIC_RESIDUE_MASS = {
    "A": 71.037114, "R": 156.101111, "N": 114.042927, "D": 115.026943,
    "C": 103.009185, "E": 129.042593, "Q": 128.058578, "G": 57.021464,
    "H": 137.058912, "I": 113.084064, "L": 113.084064, "K": 128.094963,
    "M": 131.040485, "F": 147.068414, "P": 97.052764, "S": 87.032028,
    "T": 101.047679, "W": 186.079313, "Y": 163.063329,
    "V": 99.068414,
}

PKA_ACIDIC = {"C": 8.33, "D": 3.86, "E": 4.25, "Y": 10.07}
PKA_BASIC = {"H": 6.00, "K": 10.54, "R": 12.48}
HYDROPATHY = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
    "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
    "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}


def clean_sequence(sequence: str) -> str:
    cleaned = "".join(sequence.split()).upper()
    if not cleaned:
        raise ValueError("Sequence cannot be empty.")
    invalid = sorted(set(cleaned) - set(RESIDUE_MASS))
    if invalid:
        raise ValueError("Only the 20 standard amino-acid one-letter codes are supported; invalid: " + ", ".join(invalid))
    return cleaned


def _charge_at_ph(sequence: str, ph: float) -> float:
    counts = Counter(sequence)
    positive = 1 / (1 + 10 ** (ph - 9.69))  # N-terminus
    positive += sum(counts[aa] / (1 + 10 ** (ph - pka)) for aa, pka in PKA_BASIC.items())
    negative = 1 / (1 + 10 ** (2.34 - ph))  # C-terminus
    negative += sum(counts[aa] / (1 + 10 ** (pka - ph)) for aa, pka in PKA_ACIDIC.items())
    return positive - negative


def estimate_isoelectric_point(sequence: str) -> float:
    low, high = 0.0, 14.0
    for _ in range(80):
        mid = (low + high) / 2
        if _charge_at_ph(sequence, mid) > 0:
            low = mid
        else:
            high = mid
    return round((low + high) / 2, 3)


class SequenceRequest(BaseModel):
    sequence: str = Field(min_length=1, max_length=2000)

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, value: str) -> str:
        try:
            return clean_sequence(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class AlignmentRequest(BaseModel):
    sequence_a: str = Field(min_length=1, max_length=500)
    sequence_b: str = Field(min_length=1, max_length=500)
    match_score: int = Field(default=2, ge=1, le=5)
    mismatch_score: int = Field(default=-1, ge=-5, le=0)
    gap_penalty: int = Field(default=-2, ge=-10, le=-1)

    @field_validator("sequence_a", "sequence_b")
    @classmethod
    def validate_sequence(cls, value: str) -> str:
        try:
            return clean_sequence(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


@router.post("/analyze")
def analyze_sequence(payload: SequenceRequest):
    sequence = payload.sequence
    counts = Counter(sequence)
    length = len(sequence)
    average_mass = sum(RESIDUE_MASS[aa] for aa in sequence) + 18.01528
    monoisotopic_mass = sum(MONOISOTOPIC_RESIDUE_MASS[aa] for aa in sequence) + 18.010565
    aromatic = counts["F"] + counts["W"] + counts["Y"]
    extinction_reduced = 5500 * counts["W"] + 1490 * counts["Y"]
    gravy = sum(HYDROPATHY[aa] for aa in sequence) / length
    composition = {aa: round(count / length * 100, 2) for aa, count in sorted(counts.items())}
    return {
        "sequence": sequence,
        "sequence_length": length,
        "molecular_weight_da_average": round(average_mass, 4),
        "molecular_weight_da_monoisotopic": round(monoisotopic_mass, 4),
        "estimated_isoelectric_point": estimate_isoelectric_point(sequence),
        "gravy_hydropathy_index": round(gravy, 4),
        "aromaticity_fraction": round(aromatic / length, 4),
        "amino_acid_counts": dict(sorted(counts.items())),
        "amino_acid_composition_percent": composition,
        "absorbance_280_extinction_coefficient_m_inv_cm_inv_reduced": extinction_reduced,
        "limitations": [
            "Estimates assume an unmodified linear peptide with free N- and C-termini.",
            "Average and monoisotopic masses exclude post-translational modifications, counterions, adducts and disulfide bond corrections.",
            "The pI is an approximate Henderson-Hasselbalch estimate using fixed residue pKa values; local structure and solvent can shift values.",
            "The 280 nm extinction estimate assumes reduced cysteines; disulfide-linked cysteine pairs can contribute additional absorbance.",
            "These calculations are not experimental measurements and should not be used as release specifications.",
        ],
        "calculation_status": "computed_estimate",
    }


@router.post("/align")
def align_sequences(payload: AlignmentRequest):
    a, b = payload.sequence_a, payload.sequence_b
    n, m = len(a), len(b)
    # Needleman-Wunsch global alignment with a linear gap penalty.
    score = [[0] * (m + 1) for _ in range(n + 1)]
    trace = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = i * payload.gap_penalty
        trace[i][0] = 1
    for j in range(1, m + 1):
        score[0][j] = j * payload.gap_penalty
        trace[0][j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diagonal = score[i - 1][j - 1] + (payload.match_score if a[i - 1] == b[j - 1] else payload.mismatch_score)
            up = score[i - 1][j] + payload.gap_penalty
            left = score[i][j - 1] + payload.gap_penalty
            best = max(diagonal, up, left)
            score[i][j] = best
            trace[i][j] = 0 if best == diagonal else (1 if best == up else 2)
    i, j = n, m
    aligned_a, aligned_b = [], []
    while i or j:
        direction = trace[i][j]
        if i and j and direction == 0:
            aligned_a.append(a[i - 1]); aligned_b.append(b[j - 1]); i -= 1; j -= 1
        elif i and (j == 0 or direction == 1):
            aligned_a.append(a[i - 1]); aligned_b.append("-"); i -= 1
        else:
            aligned_a.append("-"); aligned_b.append(b[j - 1]); j -= 1
    aligned_a.reverse(); aligned_b.reverse()
    aa, bb = "".join(aligned_a), "".join(aligned_b)
    columns = len(aa)
    identities = sum(x == y and x != "-" for x, y in zip(aa, bb))
    gaps = sum(x == "-" or y == "-" for x, y in zip(aa, bb))
    return {
        "aligned_sequence_a": aa,
        "aligned_sequence_b": bb,
        "alignment_score": score[n][m],
        "identity_count": identities,
        "alignment_length": columns,
        "identity_percent": round(identities / columns * 100, 2) if columns else 0,
        "gap_count": gaps,
        "method": "Needleman-Wunsch global alignment with linear gap penalty",
        "parameters": {"match": payload.match_score, "mismatch": payload.mismatch_score, "gap": payload.gap_penalty},
        "limitations": ["Simple scoring model; no substitution matrix or affine gap costs.", "Sequence similarity is not proof of structural or functional equivalence."],
    }

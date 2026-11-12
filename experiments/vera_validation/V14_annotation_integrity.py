"""Read-only SE-BRL annotation provenance and consistency audit."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
CODEBOOK = ROOT.parents[1] / "ml/se_brl/codebook.v0.1.0.json"

def inspect():
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    indicators = [
        item["id"]
        for dimension in codebook["dimensions"]
        for item in dimension["indicators"]
    ]

    sources = {
        "canonical": (
            "vera_behavioral_annotations.csv", "annotation_id"
        ),
        "ai_review": (
            "vera_behavioral_annotations_reviewed.xlsx", "ID"
        ),
        "batch_review": (
            "vera_batch_annotation_review.xlsx", "Annotation ID"
        ),
        "independent": (
            "independent_annotator_blank.xlsx", "annotation_id"
        ),
    }

    frames = {}
    for kind, (filename, id_field) in sources.items():
        path = ROOT / filename
        if not path.is_file():
            raise FileNotFoundError(filename)

        frame = (
            pd.read_csv(path)
            if path.suffix == ".csv"
            else pd.read_excel(path)
        )
        frame.columns = frame.columns.astype(str).str.strip()
        frame = frame.rename(columns={id_field: "ID"})
        missing = set(indicators + ["ID"]) - set(frame.columns)
        if missing:
            raise ValueError(f"{kind}: missing columns {sorted(missing)}")

        frame["ID"] = frame["ID"].astype("string").str.strip()
        if frame["ID"].isna().any() or frame["ID"].duplicated().any():
            raise ValueError(f"{kind}: invalid or duplicate IDs")

        frames[kind] = frame.set_index("ID")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{kind}: {len(frame)} rows; SHA256={digest}")

    canonical = frames["canonical"]
    for name, other in frames.items():
        if set(other.index) != set(canonical.index):
            raise ValueError(f"{name}: annotation ID set mismatch")

        comparable = 0
        disagreements = 0
        for indicator in indicators:
            left = canonical[indicator].astype("string").str.strip().str.lower()
            right = other[indicator].astype("string").str.strip().str.lower()
            valid = left.notna() & right.notna()
            comparable += int(valid.sum())
            disagreements += int((left[valid] != right[valid]).sum())

        populated = int(other[indicators].notna().sum().sum())
        print(
            f"{name}: populated={populated}/{len(other)*len(indicators)}; "
            f"comparable={comparable}; disagreements={disagreements}"
        )
        if disagreements:
            print("WARNING: overlapping annotation values disagree")

    independent = frames["independent"]
    independent_count = int(independent[indicators].notna().sum().sum())

    print("Independent reference judgments:", independent_count)
    print("Expert validation: NOT ESTABLISHED BY THESE FILES")
    print("Inter-annotator agreement: NOT ESTABLISHED")

    if independent_count == 0:
        print("SCIENTIFIC STATUS: independent validation blocked")
    else:
        print("SCIENTIFIC STATUS: independent labels require provenance audit")

    print("ANNOTATION INTEGRITY AUDIT COMPLETE")

if __name__ == "__main__":
    inspect()

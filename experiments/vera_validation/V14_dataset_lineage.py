"""Read-only SE-BRL email dataset lineage and leakage audit."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/data/processed/preprocessed/email_preprocessed.csv"
MANIFEST = ROOT / "experiments/results/experiments/input_manifest.csv"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def audit():
    from ml.research_policy import require_stage_authorization
    require_stage_authorization('validation')
    import pandas as pd
    print("=== 1. DATASET IDENTIFICATION ===")

    if not DATA.is_file():
        print("BLOCKED: Email preprocessed dataset missing")
        return

    print("File:", DATA.relative_to(ROOT))
    print("SHA256:", sha256(DATA))

    df = pd.read_csv(DATA, low_memory=False)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    required = [
        "source_dataset", "target", "observation_id",
        "group_id", "partition", "cv_fold"
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        print("FAIL: Missing required columns:", missing)
        return

    print("\n=== 2. SOURCE-LABEL CONTINGENCY ===")
    table = pd.crosstab(
        df["source_dataset"].fillna("<missing>"),
        df["target"].fillna("<missing>")
    )
    print(table.to_string())

    confounded = all(
        (row > 0).sum() == 1
        for _, row in table.iterrows()
    )

    print("Each source has one observed target class:", confounded)
    if confounded:
        print("WARNING: Source-label confounding detected")
        print("STATUS: Email generalization NOT ESTABLISHED")

    print("\n=== 3. ID INTEGRITY ===")
    print("Missing observation IDs:", df["observation_id"].isna().sum())
    print("Duplicate observation IDs:", df["observation_id"].duplicated().sum())
    print("Missing group IDs:", df["group_id"].isna().sum())

    print("\n=== 4. PARTITION INTEGRITY ===")
    print(df["partition"].value_counts(dropna=False).to_string())

    group_parts = df.groupby(
        "group_id", dropna=False
    )["partition"].nunique(dropna=False)

    print("Groups crossing partitions:", int((group_parts > 1).sum()))

    development = df[
        df["partition"].astype(str).str.lower() == "development"
    ]

    if len(development):
        folds = development.groupby(
            "group_id", dropna=False
        )["cv_fold"].nunique(dropna=False)

        print("Development groups crossing CV folds:",
              int((folds > 1).sum()))
        print("Development fold counts:")
        print(development["cv_fold"].value_counts(dropna=False).to_string())

    print("\n=== 5. MIXED TARGET GROUPS ===")
    mixed = df.groupby(
        "group_id", dropna=False
    )["target"].nunique(dropna=False)

    print("Groups containing multiple targets:",
          int((mixed > 1).sum()))

    print("\n=== 6. SPAPHISH SOURCE CHECK ===")
    sources = set(
        df["source_dataset"].dropna().astype(str).str.lower()
    )
    print("SpaPhish source present:", any("spaphish" in s for s in sources))

    print("\n=== 7. EXPERIMENT MANIFEST ===")
    if MANIFEST.is_file():
        print("Manifest exists: YES")
        print("Manifest SHA256:", sha256(MANIFEST))
        manifest = pd.read_csv(MANIFEST)
        print("Manifest rows:", len(manifest))
        print("Manifest columns:", manifest.columns.tolist())
        print("NOTE: Hash existence does not prove manifest alignment")
    else:
        print("Manifest exists: NO")

    print("\n=== 8. RESEARCH INTEGRITY VERDICT ===")
    print("Dataset source composition: AUDITED")
    print("Partition crossing: CHECKED")
    print("Development fold crossing: CHECKED")
    print("Semantic label correctness: NOT ESTABLISHED")
    print("Source-independent email detection: NOT ESTABLISHED")
    print("Saved experiment lineage: REQUIRES SEPARATE VERIFICATION")
    print("\nREAD-ONLY DATASET AUDIT COMPLETE")

if __name__ == "__main__":
    audit()

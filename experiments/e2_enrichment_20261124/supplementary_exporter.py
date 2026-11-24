
import csv
import hashlib
import json
from pathlib import Path

from behavioral_enrichment import behavioral_features
from supplementary_schema_validator import validate_vector

METADATA = (
    "observation_id",
    "source_dataset",
    "target",
    "group_id",
    "partition",
    "cv_fold",
)

EXPECTED = {
    "E2-A": 8,
    "E2-B": 24,
    "E2-C": 36,
    "E2-D": 44,
}

def build_representations(extraction):
    features = behavioral_features(extraction)

    baseline = features["baseline"]
    indicators = features["indicator"]
    evidence = features["evidence"]

    assert len(baseline) == 8
    assert len(indicators) == 24
    assert len(evidence) == 12

    assert not set(baseline) & set(indicators)
    assert not set(baseline) & set(evidence)
    assert not set(indicators) & set(evidence)

    vectors = {
        "E2-A": dict(baseline),
        "E2-B": dict(indicators),
        "E2-C": {**indicators, **evidence},
        "E2-D": {**baseline, **indicators, **evidence},
    }

    for name, vector in vectors.items():
        if set(vector) & set(METADATA):
            raise ValueError("Metadata leakage")

        validate_vector(
            vector,
            tuple(vector),
            EXPECTED[name]
        )

    return vectors


def export_representations(
    output_dir,
    records,
    ordered_dictionary,
    expected_metadata
):
    output_dir = Path(output_dir)

    records = list(records)

    if not records:
        raise ValueError("Empty development population")

    expected = {
        r["observation_id"]: r
        for r in expected_metadata
    }

    if len(expected) != len(expected_metadata):
        raise ValueError("Duplicate expected observation IDs")

    tables = {name: [] for name in EXPECTED}
    seen = set()
    groups = {}
    folds = {}

    for metadata, extraction in records:
        if set(metadata) != set(METADATA):
            raise ValueError("Unexpected metadata schema")

        if metadata["partition"] != "development":
            raise ValueError("Reserved partition rejected")

        oid = metadata["observation_id"]

        if oid in seen:
            raise ValueError("Duplicate observation ID")

        if oid not in expected:
            raise ValueError("Unexpected observation ID")

        if any(
            metadata[k] != expected[oid][k]
            for k in METADATA
        ):
            raise ValueError("Assignment mismatch")

        seen.add(oid)

        group = metadata["group_id"]
        fold = metadata["cv_fold"]
        target = metadata["target"]

        if target not in (0, 1):
            raise ValueError("Invalid target")

        groups.setdefault(group, set()).add(fold)
        folds.setdefault(fold, set()).add(target)

        vectors = build_representations(extraction)

        for name, vector in vectors.items():
            columns = tuple(ordered_dictionary[name])

            validate_vector(
                vector,
                columns,
                EXPECTED[name]
            )

            tables[name].append({
                **metadata,
                **{c: vector[c] for c in columns}
            })

    if seen != set(expected):
        raise ValueError("Incomplete development population")

    if any(len(v) != 1 for v in groups.values()):
        raise ValueError("Group crossing detected")

    if len(folds) != 5:
        raise ValueError("Expected five development folds")

    if any(v != {0, 1} for v in folds.values()):
        raise ValueError("Fold missing a target class")

    if output_dir.exists():
        raise FileExistsError(output_dir)

    output_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "rows": len(records),
        "groups": len(groups),
        "folds": len(folds),
        "files": {},
        "research_fitting_performed": False,
        "scientific_acceptance_established_by_export": False,
    }

    for name, rows in tables.items():
        path = output_dir / (name.lower() + ".csv")
        columns = [*METADATA, *ordered_dictionary[name]]

        with path.open("x", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        manifest["files"][name] = {
            "filename": path.name,
            "features": EXPECTED[name],
            "rows": len(rows),
            "sha256": hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        }

    path = output_dir / "feature_export_manifest.json"

    with path.open("x", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest

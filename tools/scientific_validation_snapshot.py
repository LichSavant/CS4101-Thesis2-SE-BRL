"""Aggregate historical assignment metadata without restoring sparse/LFS inputs.

This is an integrity check, never dataset admission or experimental evaluation.
Only three fixed assignment blobs are read; outcomes and content are excluded.
Run from the repository root: python -B tools/scientific_validation_snapshot.py
"""
import csv
import hashlib
import io
import json
import subprocess
from collections import Counter, defaultdict


MANIFESTS = {
    name: f"experiments/results/preprocessing/partitions/{name}_partition_manifest.csv"
    for name in ("email", "phiusiil", "uci")
}
FIELDS = ["observation_id", "source_dataset", "target", "group_id", "partition", "cv_fold"]


def summarize(payload):
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    if reader.fieldnames != FIELDS:
        raise ValueError("unexpected_metadata_schema")
    ids = set()
    groups = defaultdict(lambda: {"roles": set(), "folds": set(), "targets": set()})
    roles, classes, sources, development_folds = Counter(), Counter(), Counter(), Counter()
    fold_targets = defaultdict(Counter)
    duplicates = invalid = reserved_folds = 0
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed_metadata_row")
        role, fold, target = row["partition"], row["cv_fold"], row["target"]
        if (not row["observation_id"] or not row["group_id"] or not row["source_dataset"]
                or role not in {"development", "calibration", "test"} or target not in {"0", "1"}):
            invalid += 1
        duplicates += row["observation_id"] in ids
        ids.add(row["observation_id"])
        group = groups[row["group_id"]]
        group["roles"].add(role)
        group["targets"].add(target)
        if role == "development":
            if fold not in {str(i) + suffix for i in range(1, 6) for suffix in ("", ".0")}:
                invalid += 1
            group["folds"].add(fold.removesuffix(".0"))
            development_folds[fold.removesuffix(".0")] += 1
            fold_targets[fold.removesuffix(".0")][target] += 1
        elif fold:
            reserved_folds += 1
        roles[role] += 1
        classes[target] += 1
        sources[(row["source_dataset"], target)] += 1
    crossings = sum(len(g["roles"]) > 1 for g in groups.values())
    fold_crossings = sum(len(g["folds"]) > 1 for g in groups.values())
    checks = {
        "nonempty": bool(ids), "unique_ids": duplicates == 0,
        "valid_fields": invalid == 0, "reserved_folds_empty": reserved_folds == 0,
        "group_disjoint_roles": crossings == 0, "group_disjoint_folds": fold_crossings == 0,
        "five_development_folds": set(development_folds) == set("12345"),
        "both_targets": set(classes) == {"0", "1"},
        "both_targets_per_development_fold": bool(fold_targets) and all(
            set(counts) == {"0", "1"} for counts in fold_targets.values()),
    }
    return {
        "sha256": hashlib.sha256(payload).hexdigest(), "rows": sum(roles.values()),
        "groups": len(groups), "duplicate_ids": duplicates, "partition_counts": dict(roles),
        "historical_target_counts_not_source_verified": dict(classes),
        "historical_source_target_counts": [
            {"source": source, "target": target, "count": count}
            for (source, target), count in sorted(sources.items())
        ],
        "development_fold_counts": dict(sorted(development_folds.items())),
        "development_fold_target_counts": dict(sorted(fold_targets.items())),
        "each_source_has_only_one_historical_target": bool(sources) and all(
            len({target for source, target in sources if source == name}) == 1
            for name, _ in sources),
        "mixed_target_groups": sum(len(g["targets"]) > 1 for g in groups.values()),
        "role_crossing_groups": crossings, "fold_crossing_groups": fold_crossings,
        "checks": checks, "metadata_integrity_pass": all(checks.values()),
        "scientific_admission": False,
        "limits": "Historical metadata assertions only; no native-label, original-ID, duplicate-edge, domain/campaign independence or custody proof.",
    }


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def main():
    # Pin every read to the same immutable commit, even if HEAD subsequently moves.
    commit = git("rev-parse", "HEAD").decode().strip()
    result = {
        "scope": "historical_assignment_metadata_only_no_content_or_predictions",
        "commit": commit, "research_fitting_executions": 0,
        "scientific_experiments_executed": 0,
        "manifests": {name: summarize(git("show", f"{commit}:{path}"))
                      for name, path in MANIFESTS.items()},
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(m["metadata_integrity_pass"] for m in result["manifests"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())

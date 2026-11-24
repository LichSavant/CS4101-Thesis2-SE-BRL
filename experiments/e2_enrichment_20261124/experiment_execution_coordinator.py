
from pathlib import Path
import json
import hashlib
import pandas as pd

from nested_experimental_engine import evaluate_configuration

MATRICES = {
    "E2-Original": "e2-original.csv",
    "E2-A": "e2-a.csv",
    "E2-B": "e2-b.csv",
    "E2-C": "e2-c.csv",
    "E2-D": "e2-d.csv"
}

METADATA = [
    "observation_id", "source_dataset",
    "target", "group_id", "partition",
    "cv_fold"
]


def sha256(path):
    return hashlib.sha256(
        Path(path).read_bytes()
    ).hexdigest()


def run_experiments(
    feature_directory,
    output_directory,
    accepted_config,
    accepted_dictionary,
    expected_hashes,
    authorization_verified=False
):
    if authorization_verified is not True:
        raise PermissionError(
            "Verified exact-run authorization required"
        )

    feature_directory = Path(feature_directory)
    output_directory = Path(output_directory)

    if output_directory.exists():
        raise FileExistsError("Run directory already exists")

    if not (
        feature_directory / "extraction_receipt.json"
    ).is_file():
        raise ValueError("Complete extraction receipt required")

    grids = accepted_config["parameter_grids"]
    seed = accepted_config["seed"]

    prepared = {}
    reference = None

    for name, filename in MATRICES.items():
        path = feature_directory / filename

        if sha256(path) != expected_hashes[filename]:
            raise ValueError("Feature integrity failure")

        frame = pd.read_csv(path)

        dictionary_key = (
            "E2-A" if name == "E2-Original" else name
        )

        features = accepted_dictionary[dictionary_key]

        if list(frame.columns) != METADATA + features:
            raise ValueError("Ordered feature schema mismatch")

        if len(frame) != 15011:
            raise ValueError("Unexpected population size")

        if frame[METADATA].isna().any().any():
            raise ValueError("Incomplete metadata")

        if not frame["observation_id"].is_unique:
            raise ValueError("Duplicate observations")

        if not frame["partition"].eq("development").all():
            raise ValueError("Reserved record detected")

        aligned = frame[METADATA].sort_values(
            "observation_id"
        ).reset_index(drop=True)

        if reference is None:
            reference = aligned
        elif not reference.equals(aligned):
            raise ValueError("Unmatched experimental population")

        prepared[name] = (frame, features)

    output_directory.mkdir(
        parents=True,
        exist_ok=False
    )

    summary = []

    for name, (frame, features) in prepared.items():
        for family, grid in grids.items():

            print(
                "Running:", name, family,
                flush=True
            )

            result = evaluate_configuration(
                frame,
                features,
                family,
                grid,
                authorization_verified=authorization_verified,
                seed=seed
            )

            run_dir = output_directory / name / family
            run_dir.mkdir(parents=True, exist_ok=False)

            result["predictions"].to_csv(
                run_dir / "oof_predictions.csv",
                index=False
            )

            pd.DataFrame(
                result["fold_metrics"]
            ).to_csv(
                run_dir / "fold_metrics.csv",
                index=False
            )

            with (
                run_dir / "search_history.json"
            ).open("x", encoding="utf-8") as handle:
                json.dump(
                    result["search_history"],
                    handle,
                    indent=2
                )

            ap = result["mean_fold_ap"]
            f1 = result["mean_fold_f1"]

            summary.append({
                "representation": name,
                "features": len(features),
                "classifier": family,
                "mean_fold_ap": ap,
                "mean_fold_f1": f1,
                "minimum_objective_met": (
                    ap >= 0.80 and f1 >= 0.80
                ),
                "stretch_objective_met": (
                    ap >= 0.90 and f1 >= 0.90
                )
            })

    table = pd.DataFrame(summary)

    expected_runs = len(MATRICES) * len(grids)

    if len(table) != expected_runs:
        raise ValueError("Incomplete experimental comparison")

    table.to_csv(
        output_directory / "performance_summary.csv",
        index=False
    )

    hashes = {
        str(path.relative_to(output_directory)): sha256(path)
        for path in sorted(output_directory.rglob("*"))
        if path.is_file()
    }

    receipt = {
        "status": "EXECUTION_COMPLETE",
        "observations": 15011,
        "comparisons": expected_runs,
        "outer_folds": 5,
        "claim_scope": "exploratory_internal_validation",
        "historical_holdout_used": False,
        "output_hashes": hashes
    }

    with (
        output_directory / "execution_receipt.json"
    ).open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)

    return table

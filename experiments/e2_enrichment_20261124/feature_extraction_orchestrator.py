
from pathlib import Path
import hashlib
import json
import pandas as pd

from ml.preprocessing import preprocess

from restricted_delivery_adapter import (
    validate_delivery,
    iter_preprocessing_inputs,
    METADATA
)

from integrated_extraction_adapter import (
    SupplementaryExtractionAdapter
)

from supplementary_exporter import (
    export_representations
)


def prepare_development_features(
    payload_path,
    crosswalk_path,
    output_path,
    expected_payload_sha256,
    expected_crosswalk_sha256,
    approved_payload_fields,
    authorization_verified=False
):
    if authorization_verified is not True:
        raise PermissionError(
            "Verified no-fit authorization required"
        )

    output_path = Path(output_path)

    if output_path.exists():
        raise FileExistsError(
            "Output must use a fresh immutable path"
        )

    frame = validate_delivery(
        payload_path,
        crosswalk_path,
        expected_payload_sha256,
        expected_crosswalk_sha256,
        approved_payload_fields
    )

    adapter = SupplementaryExtractionAdapter()

    dictionary = json.loads(
        Path(__file__).with_name(
            "ordered_predictor_dictionary.json"
        ).read_text(encoding="utf-8")
    )["ordered_predictors"]

    records = []
    original_rows = []
    expected = frame[METADATA].to_dict("records")

    for index, (metadata, raw) in enumerate(
        iter_preprocessing_inputs(frame), start=1
    ):
        artifact = preprocess(raw)
        result = adapter.extract_pair(artifact)

        baseline = result["baseline_8"]

        if set(baseline) != set(dictionary["E2-A"]):
            raise ValueError("Baseline predictor mismatch")

        original_rows.append({
            **metadata,
            **baseline
        })

        records.append((
            metadata,
            result["candidate_extraction"]
        ))

        if index % 1000 == 0:
            print(
                "Processed:",
                index,
                "/",
                len(frame),
                flush=True
            )

    if len(records) != len(frame):
        raise ValueError("Incomplete extraction")

    manifest = export_representations(
        output_path,
        records,
        dictionary,
        expected
    )

    original = pd.DataFrame(
        original_rows,
        columns=METADATA + dictionary["E2-A"]
    )

    original_path = output_path / "e2-original.csv"

    with original_path.open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        original.to_csv(handle, index=False)

    receipt = {
        "rows": len(frame),
        "representations": {
            "E2-Original": 8,
            "E2-A": 8,
            "E2-B": 24,
            "E2-C": 36,
            "E2-D": 44
        },
        "original_baseline_sha256": hashlib.sha256(
            original_path.read_bytes()
        ).hexdigest(),
        "payload_sha256": expected_payload_sha256,
        "crosswalk_sha256": expected_crosswalk_sha256,
        "classifier_fitting_performed": False,
        "transformer_policy": "review_only",
        "candidate_export_manifest": manifest
    }

    with (
        output_path / "extraction_receipt.json"
    ).open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)

    return receipt

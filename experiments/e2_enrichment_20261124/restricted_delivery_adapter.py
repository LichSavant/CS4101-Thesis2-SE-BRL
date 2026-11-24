
from pathlib import Path
import hashlib
import pandas as pd

METADATA = [
    "observation_id",
    "source_dataset",
    "target",
    "group_id",
    "partition",
    "cv_fold"
]

ALLOWED_PAYLOAD = {
    "subject", "body", "sender", "reply_to"
}

PRIMARY_SOURCES = {
    "Nazario", "Enron", "SpamAssassin"
}


def sha256_file(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def validate_delivery(
    payload_path,
    crosswalk_path,
    expected_payload_sha256,
    expected_crosswalk_sha256,
    approved_payload_fields
):
    payload_path = Path(payload_path)
    crosswalk_path = Path(crosswalk_path)

    if sha256_file(crosswalk_path) != expected_crosswalk_sha256:
        raise ValueError("Crosswalk integrity failure")

    if sha256_file(payload_path) != expected_payload_sha256:
        raise ValueError("Payload integrity failure")

    fields = set(approved_payload_fields)

    if not fields.issubset(ALLOWED_PAYLOAD):
        raise ValueError("Unapproved payload fields")

    if not {"subject", "body"}.issubset(fields):
        raise ValueError("Required payload fields missing")

    header = pd.read_csv(payload_path, nrows=0)

    if set(header.columns) != set(METADATA) | fields:
        raise ValueError("Delivery schema mismatch")

    expected = pd.read_csv(crosswalk_path)

    if len(expected) != 15011:
        raise ValueError("Unexpected population size")

    if not expected["observation_id"].is_unique:
        raise ValueError("Duplicate expected IDs")

    if not expected["partition"].eq("development").all():
        raise ValueError("Reserved partition in crosswalk")

    if set(expected["source_dataset"]) != PRIMARY_SOURCES:
        raise ValueError("Unexpected source population")

    frame = pd.read_csv(payload_path)

    if len(frame) != len(expected):
        raise ValueError("Payload population mismatch")

    if frame[METADATA].isna().any().any():
        raise ValueError("Missing required metadata")

    if not frame["observation_id"].is_unique:
        raise ValueError("Duplicate delivered IDs")

    if not frame["partition"].eq("development").all():
        raise ValueError("Reserved partition detected")

    if set(frame["cv_fold"]) != {1, 2, 3, 4, 5}:
        raise ValueError("Fold mismatch")

    if set(frame["target"]) != {0, 1}:
        raise ValueError("Invalid target classes")

    if frame.groupby("group_id")["cv_fold"].nunique().max() != 1:
        raise ValueError("Group crosses development folds")

    if not frame.groupby("cv_fold")["target"].nunique().eq(2).all():
        raise ValueError("Missing target class within fold")

    matched = frame[METADATA].merge(
        expected[METADATA],
        on=METADATA,
        validate="one_to_one"
    )

    if len(matched) != len(expected):
        raise ValueError("Identity or assignment mismatch")

    return frame


def iter_preprocessing_inputs(frame):
    for record in frame.to_dict("records"):

        artifact = {
            "kind": "email",
            "body_collection_authorized": True,
            "study_purpose": "Approved supplementary E2 development evaluation"
        }

        for field in ALLOWED_PAYLOAD:
            if field in record and pd.notna(record[field]):
                artifact[field] = str(record[field])

        metadata = {
            field: record[field]
            for field in METADATA
        }

        yield metadata, artifact

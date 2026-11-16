"""Validate a candidate dictionary; never promote it to scientific approval."""
import hashlib
import json
from pathlib import Path

from ml.development_experiments import DevelopmentSpecification, FeatureColumn, behavioral_columns
from ml.development_runner import dataset_fingerprint
from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint

CANDIDATE_PATH = Path(__file__).with_name("feature_freeze_candidate.v0.1.0.json")
CODEBOOK_PATH = Path(__file__).with_name("se_brl") / "codebook.v0.1.0.json"


def validate_candidate(candidate):
    """Exact versioned field/order/type and authoritative-codebook binding.

    Candidate metadata is not an approval receipt or an operational rule freeze.
    Canonical definitions remain in the official pre_freeze codebook unchanged.
    """
    try:
        codebook = json.loads(CODEBOOK_PATH.read_bytes())
        if (set(candidate) != {"version", "status", "scope", "codebook_sha256", "indicators", "E1", "E2", "E3", "pending"}
                or candidate["version"] != "email-predictor-candidate-0.1.0"
                or candidate["status"] != "Pending" or candidate["scope"] != "Email candidate only"
                or candidate["codebook_sha256"] != hashlib.sha256(CODEBOOK_PATH.read_bytes()).hexdigest()):
            raise InputContractError("candidate_version_scope_or_codebook_mismatch")
        expected = [(i["id"], d["id"]) for d in codebook["dimensions"] for i in d["indicators"]]
        indicators = candidate["indicators"]
        if (len(indicators) != 12 or [(i["id"], i["dimension"]) for i in indicators] != expected
                or any(set(i) != {"id", "dimension", "definition_reference", "code_reference", "test_reference", "decision_status"}
                       or i["decision_status"] != "Pending"
                       or any(type(i[k]) is not str or not i[k].strip() for k in ("definition_reference", "code_reference", "test_reference"))
                       for i in indicators)):
            raise InputContractError("canonical_indicator_contract_mismatch")
        conventional = tuple(FeatureColumn(c["name"], c["kind"]) for c in candidate["E1"])
        if ([(c.name, c.kind) for c in conventional] != [("model_text", "text"),
                ("conventional:text_char_count", "numeric"), ("conventional:text_word_count", "numeric")]
                or any(set(c) != {"name", "kind", "missing", "derivation"} or c["missing"] != "reject"
                       or type(c["derivation"]) is not str or not c["derivation"].strip() for c in candidate["E1"])):
            raise InputContractError("exact_candidate_conventional_dictionary_required")
        expected_e2 = [{"name": n, "kind": "binary_integer", "missing": "reject",
                        "encoding": "support_available_pairs:11_supported,01_absent,00_unavailable"} for n in behavioral_columns()]
        if candidate["E2"] != expected_e2 or candidate["E3"] != [c.name for c in conventional] + list(behavioral_columns()):
            raise InputContractError("canonical_candidate_behavioral_order_required")
        if (type(candidate["pending"]) is not list or not candidate["pending"]
                or any(type(p) is not str or not p.strip() for p in candidate["pending"])):
            raise InputContractError("pending_scientific_choices_required")
        return {"status": "technically_valid_candidate", "scientifically_approved": False,
                "candidate_fingerprint": fingerprint(candidate)}
    except (KeyError, TypeError, ValueError):
        raise InputContractError("invalid_feature_candidate") from None


def load_candidate():
    candidate = json.loads(CANDIDATE_PATH.read_bytes())
    validate_candidate(candidate)
    return candidate


def validate_candidate_dataset(dataset, candidate):
    """All E1/E2/E3 views share the same validated D9 metadata population."""
    result = validate_candidate(candidate)
    digest = dataset_fingerprint(dataset)
    specification = dataset.specification
    expected = tuple((c["name"], c["kind"]) for c in candidate["E1"])
    if specification.dataset != "Email" or tuple((c.name, c.kind) for c in specification.conventional) != expected:
        raise InputContractError("candidate_dataset_dictionary_mismatch")
    for row in dataset.observations:
        text, characters, words = row.conventional
        if (type(text) is not str or not text.strip() or type(characters) is not int or type(words) is not int
                or characters != len(text) or words != len(text.split())):
            raise InputContractError("candidate_observed_text_counts_mismatch")
    return dict(result, input_fingerprint=digest, matched_configurations=list(dataset.configurations))

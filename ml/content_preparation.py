"""Shared Email/Web no-fit extraction from supplied development assignments.

No source discovery, new allocation, text synthesis, imputation or estimator fit.
Real execution needs the accepted source/identity/rule/dictionary/custody scope;
this in-memory function validates mechanics, not a caller's scientific authority.
"""
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from ml.branch_preparation import export_selected_handoff
from ml.development_experiments import (DevelopmentSpecification, METADATA, behavioral_columns,
    build_development_dataset, development_folds)
from ml.experiment_inputs import InputContractError, PartitionAssignment, validate_supplied_partitions
from ml.metadata import fingerprint
from ml.notebook_contracts import validate_feature_boundary, _fold
from ml.observed_features import conventional_dictionary, observed_conventional, VERSION
from ml.preprocessing import preprocess
from ml.se_brl.detectors import DetectorContext
from ml.se_brl.extraction import RuleEngine
from ml.se_brl.representation import BrlRepresentation


def extract_content_handoff(records, *, assignment_manifest, expected_observation_ids,
        specification, body_access_authorized, link_access_authorized, study_purpose,
        context_provider=None):
    """Complete batch validation before extraction; preserve supplied controls.

    The exact complete available-field candidate dictionary is required here.
    A reduced historical three-column pilot cannot silently become this E1.
    Partial unevaluated behavioral dimensions remain a blocking None, never 0.
    Independent references are a trusted server port, not record annotations.
    """
    if (not isinstance(specification, DevelopmentSpecification) or specification.dataset not in {"Email", "Web"}
            or type(body_access_authorized) is not bool or type(link_access_authorized) is not bool
            or type(study_purpose) is not str or not study_purpose.strip()
            or type(expected_observation_ids) is not frozenset or not expected_observation_ids):
        raise InputContractError("explicit_content_preparation_contract_required")
    modality = "content_bearing_email" if specification.dataset == "Email" else "content_bearing_webpage"
    if tuple((c.name, c.kind) for c in specification.conventional) != conventional_dictionary(modality):
        raise InputContractError("complete_available_field_dictionary_required")
    rows = tuple(dict(r) for r in records)
    manifest = tuple(dict(r) for r in assignment_manifest)
    if not rows or not manifest or any(set(r) != {*METADATA, "source_dataset"} for r in manifest):
        raise InputContractError("exact_supplied_assignment_schema_required")
    if {r["observation_id"] for r in manifest} != expected_observation_ids:
        raise InputContractError("supplied_assignment_population_mismatch")
    assignments = tuple(PartitionAssignment(r["observation_id"], r["group_id"], r["partition"], _fold(r["cv_fold"])) for r in manifest)
    counts = validate_supplied_partitions(assignments, folds=5)
    if not all(counts.values()):
        raise InputContractError("three_partition_roles_required")
    indexed = {r["observation_id"]: r for r in manifest}
    for role in counts:
        if {r["target"] for r in manifest if r["partition"] == role} != {0, 1}:
            raise InputContractError("two_class_partition_required")
    validate_feature_boundary(rows, dataset=specification.dataset, development_only=True)
    wanted = {r.observation_id for r in assignments if r.partition == "development"}
    if {r["observation_id"] for r in rows} != wanted:
        raise InputContractError("exact_development_delivery_required")
    if any(any(r[key] != indexed[r["observation_id"]][key] for key in (*METADATA, "source_dataset")) for r in rows):
        raise InputContractError("supplied_assignment_metadata_changed")
    if any(r.get("language") != "en" for r in rows):
        raise InputContractError("explicit_supported_language_required")
    conventional, behavioral, evidence, unavailable = [], [], [], Counter()
    for row in rows:
        if specification.dataset == "Email":
            raw = {"kind": "email"}
            for field in ("subject", "body", "sender", "reply_to", "headers"):
                if row.get(field) is not None:
                    raw[field] = row[field]
            if "body" in raw:
                if not body_access_authorized:
                    raise InputContractError("research_body_access_not_authorized")
                raw.update(body_collection_authorized=True, study_purpose=study_purpose)
        else:
            raw = {"kind": "webpage"}
            for field in ("html", "visible_text", "title", "page_url"):
                if row.get(field) is not None:
                    raw[field] = row[field]
        if row.get("urls") is not None:
            if not link_access_authorized:
                raise InputContractError("research_link_access_not_authorized")
            if type(row["urls"]) is not list:
                raise InputContractError("source_links_need_documented_array_encoding")
            raw["urls"] = row["urls"]
        raw["link_extraction_authorized"] = link_access_authorized
        artifact = preprocess(raw)
        context = context_provider(artifact) if context_provider else DetectorContext()
        extraction = RuleEngine().extract(artifact, context)
        representation = BrlRepresentation(extraction)
        if any(v is None for v in representation.deterministic_slots):
            raise InputContractError("behavioral_evaluation_incomplete_requires_accepted_policy")
        observed = observed_conventional(artifact, identity_context=context)
        unavailable.update(observed.unavailable)
        derived = dict(row)
        if any(n in derived for n, _ in conventional_dictionary(modality)):
            raise InputContractError("unverified_preexisting_predictors_forbidden")
        derived.update(observed.values)
        fields = (("subject", "body", "sender", "reply_to", "headers", "urls") if specification.dataset == "Email"
                  else ("title", "page_url", "urls"))
        for field in fields:
            # Explicit audit metadata preserves None versus observed empty
            # values across CSV serialization, never enters the predictor list.
            derived.setdefault(field, None)
            derived["source_"+field+"_available"] = int(row.get(field) is not None)
        if specification.dataset == "Web":
            derived["source_html_available"] = int(row["html"] is not None)
            derived["source_visible_text_available"] = int(row["visible_text"] is not None)
        conventional.append(derived)
        behavioral.append({**{k: row[k] for k in METADATA},
                           **dict(zip(behavioral_columns(), representation.deterministic_slots, strict=True))})
        # No text or content-bearing identifiers in the aggregate receipt.
        evidence.append({"observation_id": row["observation_id"], "indicators": [
            {"id": i.indicator_id, "state": i.evidence_state, "status": i.evaluation_status,
             "locators": [{"field": s.field, "start": s.start, "end": s.end, "location": s.location}
                          for e in i.evidence for s in (e.span,)+e.supporting_spans]} for i in extraction.indicators]})
    dataset = build_development_dataset(conventional, behavioral, specification=specification)
    for config in dataset.configurations:
        development_folds(dataset, config)
    receipt = {"extractor_version": VERSION, "branch": specification.dataset,
        "development_observations": len(rows), "unavailable_predictor_counts": dict(unavailable),
        "assignment_metadata_fingerprint": fingerprint(manifest), "evidence_fingerprint": fingerprint(evidence),
        "all_learned_processing_fits": 0, "models_fitted": 0,
        "research_readiness": "not_established_by_software_validation"}
    return tuple(conventional), tuple(behavioral), tuple(evidence), receipt


def prepare_content_handoff(checkout, run_id, records, **options):
    """Only fixed D9 outputs, exclusive creation after all extraction succeeds."""
    rows, vectors, evidence, receipt = extract_content_handoff(records, **options)
    branch = options["specification"].dataset
    outputs = export_selected_handoff(Path(checkout)/"experiments/runs"/run_id, (branch,), {branch: rows}, {branch: vectors})
    return outputs, evidence, receipt

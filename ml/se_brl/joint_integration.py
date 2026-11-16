"""Proposed offline email integration, using genuine pinned counterpart types.

Identity is joined explicitly, never inferred from callback order or field
contents. No predictor vector, research permission or joint approval is emitted.
Only trusted explicitly injected software scorers/reviewers may be used.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from itertools import islice

from ml.counterpart_checkout import COUNTERPART_COMMIT, CounterpartRuntime
from ml.metadata import fingerprint, freeze_json, json_value
from ml.preprocessing import preprocess
from ml.research_policy import reject_excluded
from .review_adapter import analyze_evidence, email_request_from_view, record_from_request
from .semantic_review import validate_review


CONTRACT_VERSION = "r22-joint-email-0.1.1-proposed"
MAX_RECORDS = 128


class JointIntegrationError(ValueError):
    """Sanitized errors never contain supplied evidence or upstream diagnostics."""


@dataclass(frozen=True, slots=True)
class EvidenceAuthorization:
    evidence_sha256: str
    body_collection_authorized: bool = False
    link_extraction_authorized: bool = False
    study_purpose: str = ""


@dataclass(frozen=True, slots=True)
class JointBatchReport:
    document: Mapping

    def __post_init__(self):
        object.__setattr__(self, "document", freeze_json(self.document))

    def to_dict(self):
        return json_value(self.document)


def evidence_fingerprint(observation) -> str:
    """Bind a grant to original evidence, identity, source snapshot and language.

    Never include source labels, targets, partitions, folds or grouping in
    analysis input. This digest is custody bookkeeping, not a predictor.
    """
    return fingerprint({"observation_id": observation.observation_id,
        "original_record_id": observation.original_record_id,
        "dataset": {"id": observation.dataset.dataset_id, "snapshot": observation.dataset.snapshot_id,
                    "reference": observation.dataset.provenance_reference}, "language": observation.language,
        "evidence": {name: getattr(observation, name).value for name in ("subject", "body", "sender", "links")}})


def joint_preprocess(raw: Mapping, peer: CounterpartRuntime):
    """Strict intersection: Vera rejects first; differing prepared views reject.

    Original sources are unchanged. This proposed profile does not rewrite or
    silently relax either preprocessor's behavior/version.
    """
    local = preprocess(raw)
    counterpart = peer.preprocessing.preprocess(raw)
    if asdict(local) != asdict(counterpart):
        raise JointIntegrationError("preprocessing_views_differ")
    return local, counterpart


def _bounded(values):
    result = tuple(islice(iter(values), MAX_RECORDS + 1))
    if len(result) > MAX_RECORDS:
        raise JointIntegrationError("batch_size_limit")
    return result


def integrate_email_batch(peer: CounterpartRuntime, observations, assignments, authorizations: Mapping, *,
                          identity, expected_total, expected_targets, folds=5,
                          engineering_only=False, scorer=None, reviewer=None) -> JointBatchReport:
    """Batch validation/staging completes before the first reviewer/scorer call.

    The genuine peer join/gate returns evidence views only. IDs returned by that
    API are then checked against the exact source wrappers and joined to scoped
    authorizations. Closed partitions never reach preprocessing or a reviewer.
    Unsupported language and missing text remain unavailable. Unconsented
    supplied body/links reject; they are never silently discarded or analyzed.
    """
    if engineering_only is not True:
        raise JointIntegrationError("engineering_only_scope_required")
    if not isinstance(peer, CounterpartRuntime) or peer.commit != COUNTERPART_COMMIT:
        raise JointIntegrationError("verified_selected_counterpart_required")
    peer.verify()
    rows, assigned = _bounded(observations), _bounded(assignments)
    if not isinstance(authorizations, Mapping):
        raise JointIntegrationError("explicit_authorizations_required")
    try:
        reject_excluded((identity.dataset_id, identity.snapshot_id, identity.provenance_reference))
        for row in rows:
            reject_excluded((row.observation_id, row.original_record_id, row.label_reference,
                             row.dataset.dataset_id, row.dataset.snapshot_id, row.dataset.provenance_reference))
        for assignment in assigned:
            reject_excluded(assignment.group_id)
        # Actual committed counterpart implementation; callback only projects
        # already supplied wrappers, never analyzes, fits or transmits evidence.
        gated = peer.integration.evaluate_development_lexical(rows, assigned, identity=identity,
            expected_total=expected_total, expected_targets=expected_targets, folds=folds, evaluate=lambda view: view)
    except Exception:
        raise JointIntegrationError("counterpart_batch_rejected") from None
    by_id = {row.observation_id: row for row in rows}
    eligible = {item.observation_id for item in gated if item.evaluation.status == "evaluated"}
    if set(authorizations) != eligible:
        raise JointIntegrationError("authorization_identity_coverage_mismatch")
    staged = {}
    for item in gated:
        if item.evaluation.status != "evaluated":
            continue
        row, view = by_id[item.observation_id], item.evaluation.result
        if (not isinstance(view, peer.integration.EmailEvidenceInput)
                or any(getattr(view, key) is not getattr(row, key) for key in ("subject", "body", "sender", "links"))):
            raise JointIntegrationError("counterpart_evidence_identity_mismatch")
        grant = authorizations[item.observation_id]
        if (type(grant) is not EvidenceAuthorization or type(grant.evidence_sha256) is not str
                or grant.evidence_sha256 != evidence_fingerprint(row)):
            raise JointIntegrationError("authorization_evidence_binding_mismatch")
        try:
            request = email_request_from_view(view, artifact_id=row.observation_id, source_id=identity.dataset_id,
                source_reference=identity.provenance_reference, language=row.language,
                body_collection_authorized=grant.body_collection_authorized,
                link_extraction_authorized=grant.link_extraction_authorized, study_purpose=grant.study_purpose)
            record = record_from_request(request)
            _, peer_artifact = joint_preprocess(record.artifact_input, peer)
            peer_extraction = peer.extraction.RuleEngine().extract(peer_artifact)
            peer_envelope = peer.envelope.not_evaluated_result(peer_artifact.modality_id, peer_extraction.assessment)
            lifecycle = peer.api_adapter.to_sebrl_api_response(peer_envelope).model_dump(mode="json")
        except Exception:
            raise JointIntegrationError("evidence_or_consent_rejected") from None
        staged[item.observation_id] = request, record, peer_extraction, lifecycle, grant.evidence_sha256
    reviewer = analyze_evidence if reviewer is None else reviewer
    if not callable(reviewer):
        raise JointIntegrationError("reviewer_required")
    result = []
    for item in gated:
        row = by_id[item.observation_id]
        availability = {key: getattr(row, key).availability.value for key in ("subject", "body", "sender", "links")}
        if item.evaluation.status != "evaluated":
            result.append({"observation_id": row.observation_id, "status": "unavailable",
                           "reason": item.evaluation.reason, "field_availability": availability,
                           "review": None, "peer_lifecycle": None})
            continue
        request, record, peer_extraction, lifecycle, digest = staged[row.observation_id]
        try:
            # Freeze/copy before validation; later caller mutation cannot alter
            # an accepted report. Validation is against this original record.
            report = json_value(freeze_json(reviewer(request, scorer=scorer)))
            validate_review(report, record)
        except Exception:
            raise JointIntegrationError("review_output_rejected") from None
        peer_states = {r.indicator_id: r.evidence_state for r in peer_extraction.indicators}
        differences = [r["indicator_id"] for r in report["indicators"] if r["deterministic_state"] != peer_states[r["indicator_id"]]]
        result.append({"observation_id": row.observation_id,
                       "status": "review_required" if differences else "reviewed_engineering_only",
                       "reason": "deterministic_runtime_difference" if differences else None,
                       "field_availability": availability, "evidence_sha256": digest,
                       "deterministic_difference_ids": differences, "review": report, "peer_lifecycle": lifecycle})
    return JointBatchReport({"schema_version": CONTRACT_VERSION, "counterpart_commit": peer.commit,
        "records": result, "excluded_partition_ids": [a.observation_id for a in assigned if a.partition != "development"],
        "status": "PROPOSED_PENDING_JOINT_ACCEPTANCE", "joint_acceptance": False,
        "research_release": False, "predictor_export": False})

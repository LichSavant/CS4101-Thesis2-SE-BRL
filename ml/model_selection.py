"""Explicit synthetic implementation of the Table 4.9 decision hierarchy.

No scientific tolerances, hard SRS limits, uncertainty settings or benchmark
protocol are defaulted here. Unknown limits are not treated as no limit.
"""
from dataclasses import dataclass
from collections.abc import Mapping

from ml.development_experiments import CLASSIFIER_FAMILIES
from ml.evaluation_metrics import paired_group_bootstrap, binary_metrics, _numbers
from ml.experiment_inputs import InputContractError, PartitionAssignment, validate_supplied_partitions
from ml.metadata import freeze_json, json_value


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    families: tuple[str, ...]
    configuration: str
    delta_pr: float
    resamples: int
    confidence: float
    seed: int
    hard_limits: Mapping
    memory_evidence: str
    calibration_order: tuple[str, ...]
    efficiency_order: tuple[str, ...]
    protocol_reference: str

    def __post_init__(self):
        if (type(self.families) is not tuple or not self.families or len(set(self.families)) != len(self.families)
                or not set(self.families) <= set(CLASSIFIER_FAMILIES)):
            raise InputContractError("explicit_expected_families_required")
        if self.configuration not in {"E3", "U1"}:
            raise InputContractError("implementation_representation_required")
        _numbers((self.delta_pr, self.confidence))
        if (not 0 <= self.delta_pr <= 1 or not 0 < self.confidence < 1
                or type(self.resamples) is not int or self.resamples < 2
                or type(self.seed) is not int or self.seed < 0):
            raise InputContractError("explicit_uncertainty_and_equivalence_required")
        expected = {"minimum_recall", "minimum_precision", "maximum_p95_ms", "maximum_memory_bytes"}
        if not isinstance(self.hard_limits, Mapping) or set(self.hard_limits) != expected:
            raise InputContractError("explicit_srs_disposition_required")
        for name, value in self.hard_limits.items():
            # None is an EXPLICIT caller disposition of no applicable limit;
            # absent/unknown limits are rejected, never silently defaulted.
            if value is not None:
                _numbers((value,))
                if value < 0 or (name.startswith("minimum") and value > 1):
                    raise InputContractError("invalid_srs_limit")
        if self.memory_evidence not in {"measured_required", "unavailable_allowed_without_limit"}:
            raise InputContractError("explicit_memory_evidence_policy_required")
        if (type(self.calibration_order) is not tuple or set(self.calibration_order) != {"brier_score", "ece"}
                or len(self.calibration_order) != 2 or type(self.efficiency_order) is not tuple
                or len(set(self.efficiency_order)) != len(self.efficiency_order)
                or set(self.efficiency_order) != {"p95_batch_ms", "throughput_artifacts_per_second", "measured_memory_bytes_max", "serialized_model_bytes"}):
            raise InputContractError("explicit_complete_tie_orders_required")
        if type(self.protocol_reference) is not str or not self.protocol_reference.startswith(("synthetic:", "research:")):
            raise InputContractError("scoped_selection_reference_required")
        object.__setattr__(self, "hard_limits", freeze_json(self.hard_limits))


def select_synthetic_family(candidates, policy):
    if not isinstance(policy, SelectionPolicy) or not policy.protocol_reference.startswith("synthetic:"):
        raise InputContractError("synthetic_selection_reference_required")
    return _select_family(candidates, policy)


def select_research_family(candidates, policy, *, execution_contexts):
    """Full accepted four-family evidence; never runs candidates on sealed data."""
    from ml.preflight import require_research_fitting
    if (not isinstance(policy, SelectionPolicy) or not policy.protocol_reference.startswith("research:")
            or policy.families != CLASSIFIER_FAMILIES or policy.resamples != 2000 or policy.confidence != .95
            or not isinstance(execution_contexts, Mapping) or set(execution_contexts) != set(policy.families)
            or set(candidates) != set(policy.families)):
        raise InputContractError("complete_accepted_four_family_selection_required")
    for family, context in execution_contexts.items():
        require_research_fitting(context)
        if context._state.get("boundary") != "E-development-fitting-only":
            raise InputContractError("principal_model_selection_scope_required")
        context.verify_result(candidates[family]["result"])
        if candidates[family]["benchmark"].get("authorization_sha256") != context.authorization_sha256:
            raise InputContractError("accepted_benchmark_authorization_mismatch")
        from ml.metadata import canonical_json
        frozen = context.selection_record["policy"]
        actual = {"families": policy.families, "configuration": policy.configuration, "delta_pr": policy.delta_pr,
            "resamples": policy.resamples, "confidence": policy.confidence, "seed": policy.seed, "hard_limits": policy.hard_limits,
            "memory_evidence": policy.memory_evidence, "calibration_order": policy.calibration_order,
            "efficiency_order": policy.efficiency_order, "protocol_reference": policy.protocol_reference}
        if canonical_json(frozen) != canonical_json(actual):
            raise InputContractError("accepted_selection_policy_changed")
    return _select_family(candidates, policy, research=True)


def _select_family(candidates, policy, research=False):
    """Matched OOF evidence -> hard gates -> AP/equivalence -> ties -> freeze.

    Each candidate supplies result, benchmark with a common nonempty comparison
    fingerprint, and explicit numeric simplicity_rank. Bootstrap uncertainty is
    computed from matched rows, never accepted as an unauthenticated interval.
    Inconclusive equivalence stops selection. No selected research model is made.
    """
    if (not isinstance(policy, SelectionPolicy) or not isinstance(candidates, Mapping)
            or set(candidates) != set(policy.families)):
        raise InputContractError("explicit_synthetic_selection_inputs_required")
    indexed, metrics, benchmarks, ranks, excluded = {}, {}, {}, {}, {}
    controls = reference = None
    category = "RESEARCH RESULT" if research else "SYNTHETIC RESULT"
    execution = "AUTHORIZED DEVELOPMENT ONLY" if research else "BLOCKED"
    for family, candidate in candidates.items():
        try:
            result, benchmark, rank = candidate["result"], candidate["benchmark"], candidate["simplicity_rank"]
            if (result["result_category"] != category or result["research_execution"] != execution
                    or result["request"]["family"] != family or type(rank) is not int or rank < 0
                    or benchmark["result_category"] != category):
                raise InputContractError("synthetic_candidate_evidence_required")
            rows = [r for r in result["oof_predictions"] if r["configuration"] == policy.configuration]
            index = {r["observation_id"]: r for r in rows}
            if not rows or len(rows) != len(index):
                raise InputContractError("unique_selection_population_required")
            validate_supplied_partitions(tuple(PartitionAssignment(r["observation_id"], r["group_id"], "development", r["fold"])
                                               for r in rows), folds=5)
            if {r["fold"] for r in rows} != set(range(1, 6)):
                raise InputContractError("complete_five_fold_selection_required")
            if any(r["probability"] != r["score"] for r in rows):
                raise InputContractError("explicit_comparable_probability_scores_required")
            current = (result["input_fingerprint"], tuple(sorted((i, r["target"], r["group_id"], r["fold"]) for i, r in index.items())),
                       result["request"].get("protocol_reference"), result["request"]["calibration_edges"],
                       result["request"].get("outer_ranking_statistic"), result["request"].get("threshold"))
            if controls is not None and current != controls:
                raise InputContractError("selection_matched_controls_mismatch")
            controls = current
            current_reference = benchmark["comparison_fingerprint"]
            if type(current_reference) is not str or not current_reference.strip() or (reference is not None and reference != current_reference):
                raise InputContractError("common_benchmark_protocol_required")
            reference = current_reference
            m = result["pooled_metrics"][policy.configuration]
            # Recompute ranking/calibration rather than trusting stored summaries.
            recomputed = binary_metrics(tuple(r["target"] for r in rows), tuple(r["score"] for r in rows), positive_label=1,
                threshold=.5, probabilities=tuple(r["probability"] for r in rows),
                calibration_edges=result["request"]["calibration_edges"])
            if any(m[k] != recomputed[k] for k in ("average_precision", "brier_score", "ece")):
                raise InputContractError("selection_summary_prediction_mismatch")
            if "decision_records" in result:
                decisions = [r for r in result["decision_records"] if r["configuration"] == policy.configuration]
                decision_index = {r["observation_id"]: r["decision"] for r in decisions}
                if (len(decision_index) != len(decisions) or set(decision_index) != set(index)
                        or any(type(d) is not int or d not in (0, 1) for d in decision_index.values())):
                    raise InputContractError("exact_selection_decisions_required")
                operating = binary_metrics(tuple(r["target"] for r in rows), tuple(decision_index[r["observation_id"]] for r in rows),
                                           positive_label=1, threshold=.5)
            else:
                threshold = result["request"]["threshold"]
                if threshold["mode"] != "fixed":
                    raise InputContractError("training_threshold_decisions_required")
                _numbers((threshold["value"],), probability=True)
                operating = binary_metrics(tuple(r["target"] for r in rows), tuple(r["score"] for r in rows),
                                           positive_label=1, threshold=threshold["value"])
            if any(m[k] != operating[k] for k in ("recall", "precision")):
                raise InputContractError("selection_operating_metrics_mismatch")
            for key in ("average_precision", "recall", "precision", *policy.calibration_order):
                _numbers((m[key],), probability=True)
            for key in policy.efficiency_order:
                if key == "measured_memory_bytes_max" and benchmark[key] is None:
                    if (policy.memory_evidence != "unavailable_allowed_without_limit"
                            or policy.hard_limits["maximum_memory_bytes"] is not None):
                        raise InputContractError("required_memory_measurement_missing")
                    continue
                _numbers((benchmark[key],))
                if benchmark[key] < 0 or (key == "throughput_artifacts_per_second" and benchmark[key] <= 0):
                    raise InputContractError("measured_efficiency_evidence_required")
            failed = []
            for key, actual, minimum in (("minimum_recall", m["recall"], True), ("minimum_precision", m["precision"], True),
                    ("maximum_p95_ms", benchmark["p95_batch_ms"], False), ("maximum_memory_bytes", benchmark["measured_memory_bytes_max"], False)):
                limit = policy.hard_limits[key]
                if limit is not None and (actual < limit if minimum else actual > limit):
                    failed.append(key)
            if failed:
                excluded[family] = failed
            else:
                indexed[family], metrics[family], benchmarks[family], ranks[family] = index, m, benchmark, rank
        except InputContractError:
            raise
        except (KeyError, TypeError, ValueError):
            raise InputContractError("incomplete_selection_evidence") from None
    base = {"result_category": category, "research_execution": execution, "excluded": excluded,
            "policy": {"families": policy.families, "configuration": policy.configuration, "delta_pr": policy.delta_pr, "resamples": policy.resamples,
                "confidence": policy.confidence, "seed": policy.seed, "hard_limits": policy.hard_limits,
                "memory_evidence": policy.memory_evidence,
                "calibration_order": policy.calibration_order, "efficiency_order": policy.efficiency_order,
                "protocol_reference": policy.protocol_reference}, "comparisons": {}}
    if not indexed:
        return json_value(freeze_json(dict(base, status="no_eligible_candidate", selected=None)))
    leader = max(indexed, key=lambda f: metrics[f]["average_precision"])
    contenders = [leader]
    inconclusive = []
    for family in indexed:
        if family == leader:
            continue
        ids = sorted(indexed[leader])
        left, right = indexed[leader], indexed[family]
        interval = paired_group_bootstrap(tuple(left[i]["target"] for i in ids), tuple(left[i]["score"] for i in ids),
            tuple(right[i]["score"] for i in ids), tuple(left[i]["group_id"] for i in ids), positive_label=1,
            resamples=policy.resamples, confidence=policy.confidence, seed=policy.seed)
        lohi = interval["interval"]
        # Undefined draws never supply enough evidence for an equivalence claim.
        if interval["resamples_undefined"] or lohi is None:
            disposition = "inconclusive"
        elif lohi[0] >= -policy.delta_pr and lohi[1] <= policy.delta_pr:
            disposition = "practically_equivalent"
            contenders.append(family)
        elif lohi[0] > policy.delta_pr:
            disposition = "materially_weaker"
        else:
            disposition = "inconclusive"
        if disposition == "inconclusive":
            inconclusive.append(family)
        base["comparisons"][family] = dict(interval, disposition=disposition, reference_family=leader)
    if inconclusive:
        return json_value(freeze_json(dict(base, status="inconclusive_uncertainty", selected=None)))
    stages = []
    for key in policy.calibration_order + policy.efficiency_order + ("simplicity_rank",):
        if len(contenders) == 1:
            break
        if key == "measured_memory_bytes_max" and any(benchmarks[f][key] is None for f in contenders):
            stages.append({"criterion": key, "remaining": list(contenders),
                           "disposition": "unavailable_under_explicit_policy; no memory ranking or zero imputation"})
            continue
        def value(family):
            v = ranks[family] if key == "simplicity_rank" else (metrics[family][key] if key in policy.calibration_order else benchmarks[family][key])
            return -v if key == "throughput_artifacts_per_second" else v
        best = min(value(f) for f in contenders)
        contenders = [f for f in contenders if value(f) == best]
        stages.append({"criterion": key, "remaining": list(contenders)})
    if len(contenders) > 1 and "logistic_regression" in contenders:
        contenders = ["logistic_regression"]
        stages.append({"criterion": "final_logistic_regression_preference", "remaining": contenders})
    selected = contenders[0] if len(contenders) == 1 else None
    return json_value(freeze_json(dict(base, status=("research_selection_complete" if research else "synthetic_selection_complete") if selected else "unresolved_final_tie",
                                      selected=selected, tie_stages=stages)))

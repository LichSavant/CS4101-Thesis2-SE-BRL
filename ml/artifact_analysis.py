"""Explicit artifact -> features/evidence -> selected model -> DecisionObject.

No network, fitting, dataset discovery or persistence occurs during analysis.
Trust-reference context is server supplied, never taken from the artifact.
The initial export/loader accepts synthetic compatible bundles only; research
promotion must use the separately accepted final-freeze boundary.
"""
from dataclasses import asdict, dataclass
from collections.abc import Mapping
import hashlib
import json
import math
from pathlib import Path
import time
from uuid import uuid4

from ml.attribution import explain, VERSION as ATTRIBUTION_VERSION
from ml.classifier_adapters import FoldClassifier
from ml.decision import RiskPolicy, SCHEMA_VERSION, decide, validate_decision
from ml.development_experiments import behavioral_columns, _manifest_object, _within
from ml.experiment_engine import FittedSigmoid
from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json, fingerprint, freeze_json
from ml.model_persistence import save_fold_artifact, load_fold_artifact
from ml.observed_features import observed_conventional, conventional_dictionary, VERSION as CONVENTIONAL_VERSION
from ml.preprocessing import preprocess, PREPROCESSING_VERSION
from ml.se_brl.codebook import load_codebook
from ml.se_brl.detectors import DetectorContext
from ml.se_brl.extraction import RuleEngine, unavailable_technical_extraction
from ml.se_brl.representation import BrlRepresentation
from ml.se_brl.rules import RULESET_VERSION

VERSION = "artifact-analysis-0.1.0"
BUNDLE_VERSION = "analytical-bundle-0.2.0"


def component_versions():
    codebook = load_codebook()
    return {"analysis": VERSION, "preprocessing": PREPROCESSING_VERSION,
            "conventional": CONVENTIONAL_VERSION, "rules": RULESET_VERSION,
            "codebook": codebook["codebook_version"], "attribution": ATTRIBUTION_VERSION,
            "decision": SCHEMA_VERSION,
            "extractor_sha256": fingerprint({name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                for name in ("preprocessing.py", "features.py", "observed_features.py", "attribution.py", "decision.py",
                             "artifact_analysis.py", "classifier_adapters.py")}
                | {"se_brl/"+name: hashlib.sha256(Path(__file__).with_name("se_brl").joinpath(name).read_bytes()).hexdigest()
                   for name in ("rules.py", "extraction.py", "context.py", "detectors.py", "representation.py", "assessment.py", "codebook.v0.1.0.json")})}


@dataclass(frozen=True, slots=True)
class AnalyticalBundle:
    classifier: FoldClassifier
    calibrator: FittedSigmoid
    policy: RiskPolicy
    classification_threshold: float
    identifier: str
    scope: str
    native_domains: object = None

    def __post_init__(self):
        if (not isinstance(self.classifier, FoldClassifier) or self.classifier.pipeline is None
                or not isinstance(self.calibrator, FittedSigmoid) or not isinstance(self.policy, RiskPolicy)
                or type(self.classification_threshold) not in (int, float)
                or not math.isfinite(self.classification_threshold) or not 0 <= self.classification_threshold <= 1
                or type(self.identifier) is not str or not self.identifier.strip()
                or self.scope != "synthetic_fixture" or self.policy.scope != self.scope):
            raise InputContractError("compatible_synthetic_analytical_bundle_required")
        modality = {"Email": "content_bearing_email", "Web": "content_bearing_webpage"}.get(self.classifier.dictionary.dataset)
        if modality is None:
            if (self.classifier.dictionary.dataset not in {"UCI", "PhiUSIIL"} or self.classifier.configuration != "U1"
                    or any(c.kind != "numeric" for c in self.classifier.dictionary.conventional)):
                raise InputContractError("runtime_requires_source_specific_technical_dictionary")
            if self.classifier.dictionary.dataset == "UCI":
                if (not isinstance(self.native_domains, Mapping) or set(self.native_domains) != set(self.classifier.expected)
                        or any(type(v) not in (tuple, list) or not v or any(type(x) is not int or x not in (-1,0,1) for x in v)
                               for v in self.native_domains.values())):
                    raise InputContractError("explicit_UCI_native_feature_domains_required")
                object.__setattr__(self,"native_domains",freeze_json(self.native_domains))
        else:
            actual = tuple((c.name, c.kind) for c in self.classifier.dictionary.conventional)
            available = dict(conventional_dictionary(modality))
            if any(available.get(name) != kind for name, kind in actual):
                raise InputContractError("runtime_dictionary_extractor_mismatch")
        if self.classifier.feature_names != self.classifier.expected:
            raise InputContractError("runtime_requires_exact_selected_predictor_dictionary")
        if self.classifier.model.family == "linear_svm" and self.calibrator.specification.transform != "identity":
            raise InputContractError("runtime_margin_calibration_mismatch")


def write_bundle(directory, bundle, *, code_reference):
    if not isinstance(bundle, AnalyticalBundle):
        raise InputContractError("analytical_bundle_required")
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_bundle_directory_required")
    directory.mkdir()
    created = []
    try:
        model_digest = save_fold_artifact(directory / "model", bundle.classifier, code_reference=code_reference)
        created.extend(p for p in (directory / "model").iterdir())
        state = canonical_json(bundle.calibrator.state()).encode()
        with (directory / "calibrator.json").open("xb") as f:
            created.append(directory / "calibrator.json")
            f.write(state)
        manifest = {"version": BUNDLE_VERSION, "scope": bundle.scope, "identifier": bundle.identifier,
                    "components": component_versions(), "code_reference": code_reference,
                    "model_manifest_sha256": model_digest,
                    "calibrator_sha256": hashlib.sha256(state).hexdigest(),
                    "risk_policy": asdict(bundle.policy), "classification_threshold": bundle.classification_threshold,
                    "native_domains": bundle.native_domains,
                    "limitations": ["SYNTHETIC RESULT: not a validated research model or approved research threshold.",
                                    "Fixture dictionary is not evidence of a complete research E1 baseline."]}
        body = canonical_json(manifest).encode()
        with (directory / "manifest.json").open("xb") as f:
            created.append(directory / "manifest.json")
            f.write(body)
        return hashlib.sha256(body).hexdigest()
    except Exception:
        for path in reversed(created):
            path.unlink()
        if (directory / "model").is_dir():
            (directory / "model").rmdir()
        directory.rmdir()
        raise


def load_bundle(directory, *, expected_manifest_sha256, max_bytes):
    """Digest must come from trusted operator configuration, not the client."""
    import re
    if (type(expected_manifest_sha256) is not str or not re.fullmatch("[a-f0-9]{64}", expected_manifest_sha256)
            or type(max_bytes) is not int or max_bytes < 1):
        raise InputContractError("independent_bundle_digest_and_limit_required")
    directory = Path(directory)
    try:
        manifest_path = _within(directory, "manifest.json")
        if manifest_path.stat().st_size > max_bytes:
            raise InputContractError("analytical_bundle_oversized")
        body = manifest_path.read_bytes()
        if hashlib.sha256(body).hexdigest() != expected_manifest_sha256:
            raise InputContractError("analytical_bundle_digest_mismatch")
        manifest = json.loads(body, object_pairs_hook=_manifest_object)
        if (manifest["version"] != BUNDLE_VERSION or manifest["scope"] != "synthetic_fixture"
                or manifest["components"] != component_versions()
                or {p.name for p in directory.iterdir()} != {"manifest.json", "calibrator.json", "model"}):
            raise InputContractError("analytical_bundle_version_or_files_mismatch")
        path = _within(directory, "calibrator.json")
        if path.stat().st_size > min(max_bytes, 65536):
            raise InputContractError("calibrator_oversized")
        state = path.read_bytes()
        if hashlib.sha256(state).hexdigest() != manifest["calibrator_sha256"]:
            raise InputContractError("calibrator_digest_mismatch")
        classifier = load_fold_artifact(_within(directory, "model"),
            expected_manifest_sha256=manifest["model_manifest_sha256"], max_bytes=max_bytes)
        calibrator = FittedSigmoid.from_state(json.loads(state, object_pairs_hook=_manifest_object))
        return AnalyticalBundle(classifier, calibrator, RiskPolicy(**manifest["risk_policy"]),
            manifest["classification_threshold"], manifest["identifier"], manifest["scope"], manifest["native_domains"])
    except InputContractError:
        raise
    except Exception:
        raise InputContractError("analytical_bundle_invalid") from None


def _evidence(extraction):
    # Deliberately no snippets/addresses/URLs in the API result. Locators point
    # to the caller's own submitted original fields; text never enters logs/DB.
    return [{"indicator_id": i.indicator_id, "dimension_id": i.dimension_id,
             "state": i.evidence_state or "not_evaluated", "evaluation_status": i.evaluation_status,
             "evidence": [{"rule_id": e.rule_id, "ruleset_version": e.ruleset_version,
                 "locators": [{"field": s.field, "start": s.start, "end": s.end,
                               "location": s.location} for s in (e.span,) + e.supporting_spans]} for e in i.evidence]}
            for i in extraction.indicators]


def _findings(artifact, conventional):
    findings = []
    # Candidate technical primitives, not identity/legitimacy judgments.
    for name, family, label in (
        ("conventional:sender_reply_domain_differ", "identity_authentication", "sender_reply_domains_differ"),
        ("conventional:observed_brand_domain_mismatch", "brand_domain_relation", "audited_brand_domain_mismatch"),
        ("conventional:password_input_count", "form_structure", "password_input_observed"),
    ):
        value = conventional.values.get(name)
        if value is not None and value > 0:
            locators = []
            if family == "form_structure":
                locators = [{"field": "html", "start": s.start, "end": s.end, "location": s.location}
                            for s in artifact.structures if s.tag == "input" and dict(s.attributes).get("type", "").casefold() == "password"]
            elif family == "identity_authentication":
                locators = [{"field": f, "start": 0, "end": len(v), "location": f}
                            for f, v in (("sender", artifact.sender), ("reply_to", artifact.reply_to)) if v]
            findings.append({"finding": label, "family": family, "value": value, "locators": locators,
                             "provenance": "observed_technical_primitive_not_classification"})
    return findings


class ArtifactAnalyzer:
    def __init__(self, bundles=None, *, timeout_seconds=10., clock=time.monotonic, context_provider=None):
        if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
            raise InputContractError("analysis_timeout_required")
        self.bundles = dict(bundles or {})
        for modality, bundle in self.bundles.items():
            if not isinstance(bundle, AnalyticalBundle):
                raise InputContractError("analytical_bundle_routing_mismatch")
            expected = {"Email": "content_bearing_email", "Web": "content_bearing_webpage",
                        "UCI": "UCI", "PhiUSIIL": "PhiUSIIL"}.get(bundle.classifier.dictionary.dataset)
            if not isinstance(bundle, AnalyticalBundle) or modality != expected:
                raise InputContractError("analytical_bundle_routing_mismatch")
        self.timeout_seconds, self.clock = timeout_seconds, clock
        self.context_provider = context_provider or (lambda artifact: DetectorContext())

    def analyze(self, raw, *, language):
        start = self.clock()
        value = {"schema_version": SCHEMA_VERSION, "run_id": uuid4().hex,
                 "artifact_sha256": fingerprint(raw), "modality": "unknown", "status": "review_required",
                 "result_category": "not_evaluated", "research_validated": False,
                 "classification": None, "calibrated_probability": None, "technical_findings": [],
                 "behavioral_evidence": [], "attribution": None, "decision": None,
                 "limitations": [], "versions": component_versions(), "timing_ms": {}}
        reasons = []
        # Failure policy has no operational probability thresholds. Only used
        # to construct Review Required when no compatible bundle can be loaded.
        policy = RiskPolicy(.5, .9, 1., "synthetic:no-model-failure-policy", "synthetic_fixture")
        severity, families, coverage = 0, (), 0.
        stage = "parser"
        try:
            technical = isinstance(raw, dict) and raw.get("kind") == "technical"
            if technical:
                if set(raw) != {"kind", "dataset", "features"} or raw.get("dataset") not in {"UCI", "PhiUSIIL"} or type(raw["features"]) is not dict:
                    raise InputContractError("source_specific_engineered_record_required")
                artifact = preprocess({"kind":"technical"})
            else:
                artifact = preprocess(raw)
            value["modality"] = artifact.modality_id
            content_bearing = artifact.modality_id in {"content_bearing_email", "content_bearing_webpage"}
            if content_bearing and language != "en":
                raise InputContractError("unsupported_or_unknown_language")
            if content_bearing and not artifact.required_content_available:
                raise InputContractError("missing_required_content")
            context = self.context_provider(artifact) if content_bearing else None
            extraction = RuleEngine().extract(artifact, context) if content_bearing else unavailable_technical_extraction(artifact.modality_id)
            representation = BrlRepresentation(extraction)
            value["behavioral_evidence"] = _evidence(extraction)
            coverage = sum(i.evaluation_status == "rule_evaluated" for i in extraction.indicators) / 12
            supported = {i.indicator_id for i in extraction.indicators if i.evidence_state == "supported"}
            severity = (3 if "financial_action_request" in supported else 2 if "credential_sensitive_data_request" in supported
                        else 1 if "call_to_action" in supported else 0)
            stage = "features"
            conventional = observed_conventional(artifact, identity_context=context) if content_bearing else None
            if content_bearing:
                value["technical_findings"] = _findings(artifact, conventional)
            elif not technical:
                raise InputContractError("source_specific_technical_features_required")
            families = tuple(sorted(({"behavioral_language"} if supported else set()) |
                                    {f["family"] for f in value["technical_findings"]}))
            stage = "model"
            bundle = self.bundles.get(artifact.modality_id if content_bearing else raw["dataset"])
            if bundle is None:
                raise InputContractError("compatible_bundle_unavailable")
            policy = bundle.policy
            value["versions"]["selected_model"] = bundle.identifier
            value["limitations"].append("SYNTHETIC RESULT: model, calibration and thresholds are fixture-only; not validated research predictions.")
            if content_bearing:
                values = dict(conventional.values)
                values.update(zip(behavioral_columns(), representation.deterministic_slots, strict=True))
            else:
                values = dict(raw["features"])
                if (set(values) != set(bundle.classifier.expected) or any(type(v) not in (int,float) or not math.isfinite(v) for v in values.values())
                        or (bundle.native_domains is not None and any(v not in bundle.native_domains[n] for n,v in values.items()))):
                    raise InputContractError("exact_finite_native_technical_vector_required")
                coverage = 1.  # all required technical values; not behavioral availability
                value["versions"]["technical_branch"] = raw["dataset"]
                value["technical_findings"] = [{"finding":n,"family":"source_provided_value","value":v,"locators":[],
                    "provenance":"uninterpreted_native_value_not_behavioral_evidence"} for n,v in values.items()]
            row = tuple(values[n] for n in bundle.classifier.feature_names)
            if any(v is None for n, v in zip(bundle.classifier.feature_names, row) if n in behavioral_columns()):
                raise InputContractError("behavioral_evaluation_incomplete")
            model_start = self.clock()
            scores = bundle.classifier.score((row,), observation_ids=(value["run_id"],))
            value["timing_ms"]["classifier_pipeline"] = (self.clock()-model_start)*1000
            # This includes fitted preprocessing; not a model-only benchmark.
            stage = "calibration"
            probability = bundle.calibrator.probabilities(scores.scores)[0]
            stage = "attribution"
            attribution = explain(bundle.classifier, row)
            attribution["selected_model_version"] = bundle.identifier
            stage = "decision"
            if self.clock()-start > self.timeout_seconds:
                raise InputContractError("analysis_timeout")
            decision = decide(probability, severity=severity, families=families, coverage=coverage, policy=policy)
            if decision["tier"] == "review_required":
                reasons.extend(decision["reasons"])
            else:
                value.update(status="complete", result_category="synthetic_model_generated", calibrated_probability=probability, attribution=attribution,
                             classification="phishing" if probability >= bundle.classification_threshold else "legitimate")
                value["decision"] = decision
        except Exception as error:
            # Never relay estimator/parser exceptions (may include artifact text).
            reason = str(error) if isinstance(error, InputContractError) else "component_failure"
            import re
            reasons.append(reason if re.fullmatch(r"[a-z0-9_]+", reason) else "component_failure")
        if value["decision"] is None:
            value["decision"] = decide(None, severity=severity, families=families, coverage=coverage,
                                        policy=policy, reasons=tuple(dict.fromkeys(reasons)))
            value["limitations"].append("Review Required at stage: " + stage + ". Verify independently; no definitive prediction is available.")
        value["timing_ms"]["analysis_end_to_end"] = max(0., (self.clock()-start)*1000)
        return validate_decision(value)

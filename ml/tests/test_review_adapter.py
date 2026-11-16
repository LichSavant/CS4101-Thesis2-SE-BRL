from dataclasses import dataclass
from copy import deepcopy
import json
from pathlib import Path

import pytest

from ml.research_policy import ResearchPolicyError, reject_excluded, load_policy, require_stage_authorization, RESEARCH_STAGES
from ml.se_brl.review_adapter import analyze_evidence, email_request_from_view, interface_specification, record_from_request
from ml.se_brl.semantic_review import ReviewContractError


@dataclass(frozen=True)
class TextField:
    value: str | None = None


@dataclass(frozen=True)
class LinkField:
    value: tuple[str,...] | None = None


@dataclass(frozen=True)
class EmailEvidenceInput:
    subject: TextField
    body: TextField
    sender: TextField
    links: LinkField


def request(body=None,links=None,**extra):
    return email_request_from_view(EmailEvidenceInput(TextField("Act now."),TextField(body),TextField("sender@example.test"),LinkField(links)),
                                  artifact_id="synthetic:adapter",source_id="synthetic-fixture",source_reference="synthetic-only",
                                  language="en",**extra)


def test_published_callback_shape_is_supported_without_bookkeeping_predictors():
    report=analyze_evidence(request())
    assert len(report["indicators"])==12 and report["schema_version"]=="1.0.0"
    assert report["indicators"][0]["deterministic_state"]=="supported"
    assert all(r["semantic_status"] in {"not_requested","unavailable"} for r in report["indicators"])
    for field in ("target","partition","group_id","cv_fold","native_label","source_label"):
        changed=request();changed[field]="forbidden"
        with pytest.raises(ReviewContractError):analyze_evidence(changed)
        changed=request();changed["fields"][field]="forbidden"
        with pytest.raises(ReviewContractError):analyze_evidence(changed)
    assert interface_specification()["scientific_release"] is False


def test_unknown_vs_known_empty_and_explicit_collection_consent():
    assert "body" not in request()["fields"] and "urls" not in request()["fields"]
    with pytest.raises(ValueError):request(body="private synthetic body")
    with pytest.raises(ValueError):request(links=("https://example.test/",))
    req=request(body="",links=(),body_collection_authorized=True,study_purpose="synthetic fixture")
    assert req["fields"]["body"]=="" and req["fields"]["urls"]==[]
    req=request(body="Synthetic content",links=("https://example.test/",),body_collection_authorized=True,
                link_extraction_authorized=True,study_purpose="synthetic fixture")
    assert analyze_evidence(req)["modality"]=="content_bearing_email"


@pytest.mark.parametrize("language", ["und","es","EN",None,True])
def test_unsupported_or_unknown_languages_are_not_ordinary_negatives(language):
    changed=request();changed["language"]=language
    with pytest.raises(ReviewContractError):analyze_evidence(changed)


@pytest.mark.parametrize("alias", ["SpaFish","SPA FISH","spa-fish","spa_fish","ＳｐａＦｉｓｈ","spa\u200bfish"])
def test_exclusion_alias_metadata_is_rejected_without_any_corpus_access(alias):
    with pytest.raises(ResearchPolicyError):reject_excluded({"parents":[{"source":alias}]})
    changed=request();changed["source_id"]=alias
    with pytest.raises(ResearchPolicyError):analyze_evidence(changed)


def test_closed_policy_and_no_implicit_model_or_corpus_loading():
    for stage in RESEARCH_STAGES:
        with pytest.raises(ResearchPolicyError):require_stage_authorization(stage)
    policy=load_policy()
    assert policy["policy_version"]=="1.0.1"
    assert not policy["approved_training_datasets"] and not policy["approved_annotation_sources"] and not policy["accepted_experiments"]
    class Poison:
        @property
        def target(self):raise AssertionError("No target may be inspected")
    with pytest.raises(ReviewContractError):email_request_from_view(Poison(),artifact_id="a",source_id="b",source_reference="c",language="en")


def test_versioned_synthetic_contract_fixtures_roundtrip_exactly():
    folder=Path(__file__).parents[1]/"fixtures/semantic-review-v1"
    supplied=json.loads((folder/"request.json").read_text())
    expected=json.loads((folder/"response.json").read_text())
    assert supplied["source_id"]=="synthetic-only"
    assert analyze_evidence(supplied)==expected
    assert json.loads((folder/"interface.json").read_text())==interface_specification()

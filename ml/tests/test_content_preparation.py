from copy import deepcopy
from dataclasses import replace

import pytest

from ml.content_preparation import prepare_content_handoff
from ml.development_experiments import DevelopmentSpecification, FeatureColumn, load_development_dataset
from ml.experiment_inputs import InputContractError
from ml.observed_features import conventional_dictionary


def fixture(branch):
    rows, manifest = [], []
    for fold in range(1, 6):
        for target in (0, 1):
            i = len(rows)
            metadata = dict(observation_id=f"synthetic-{branch}-{i}", target=target, group_id=f"synthetic-group-{fold}",
                            partition="development", cv_fold=fold)
            if branch == "Email":
                row = dict(metadata, source_dataset="Nazario" if target else "Enron", source_row_id=fold-1,
                    label=target, subject=f"Synthetic subject {i}. "+("Act now." if target else "Meeting notes."), body=None, language="en")
            else:
                row = dict(metadata, source_dataset="Phishing Website Dataset", source_file="phishing.csv" if target else "not-phishing.csv",
                    source_row_id=fold-1, source_label="phishing" if target else "legitimate", html=None,
                    visible_text=f"Synthetic visible text {i}. "+("Act now." if target else "Meeting notes."), language="en")
            rows.append(row); manifest.append({**metadata, "source_dataset": row["source_dataset"]})
    for role in ("calibration", "test"):
        for target in (0, 1):
            manifest.append(dict(observation_id=f"synthetic-{role}-{target}", target=target, group_id=f"supplied-{role}-{target}",
                partition=role, cv_fold=None, source_dataset="Nazario" if target else "Enron"))
    modality = "content_bearing_email" if branch == "Email" else "content_bearing_webpage"
    spec = DevelopmentSpecification(branch, tuple(FeatureColumn(n,k) for n,k in conventional_dictionary(modality)),
        "synthetic:content-extraction", "synthetic:full-available-field-candidate")
    return rows, dict(assignment_manifest=manifest, expected_observation_ids=frozenset(r["observation_id"] for r in manifest),
        specification=spec, body_access_authorized=False, link_access_authorized=False, study_purpose="Synthetic field contract verification")


@pytest.mark.parametrize("branch", ("Email", "Web"))
def test_exact_full_dictionary_handoff_alignment_and_unavailability(branch, tmp_path):
    rows, options = fixture(branch)
    before = deepcopy(rows)
    options["assignment_manifest"].reverse()
    outputs, evidence, receipt = prepare_content_handoff(tmp_path, "synthetic-content", rows, **options)
    assert len(outputs) == 3 and rows == before
    loaded = load_development_dataset(tmp_path, "synthetic-content", specification=options["specification"])
    assert [r.observation_id for r in loaded.observations] == [r["observation_id"] for r in rows]
    assert [e["observation_id"] for e in evidence] == [r["observation_id"] for r in rows]
    for r, e in zip(rows, evidence):
        for indicator in e["indicators"]:
            for locator in indicator["locators"]:
                assert "Act now" == r[locator["field"]][locator["start"]:locator["end"]]
    assert receipt["all_learned_processing_fits"] == receipt["models_fitted"] == 0
    assert receipt["unavailable_predictor_counts"]["conventional:observed_brand_domain_mismatch"] == len(rows)
    with pytest.raises(InputContractError):
        prepare_content_handoff(tmp_path, "synthetic-content", rows, **options)


@pytest.mark.parametrize("case", ("reserved", "metadata", "unknown_language", "body_without_consent", "incomplete_trust", "reduced_dictionary"))
def test_failures_create_no_files_and_never_fabricate_inputs(tmp_path, case):
    rows, options = fixture("Email")
    if case == "reserved": rows[0]["partition"] = "test"
    elif case == "metadata": rows[0]["group_id"] = "wrong-supplied-group"
    elif case == "unknown_language": rows[0]["language"] = "und"
    elif case == "body_without_consent": rows[0]["body"] = "Sensitive synthetic fixture"
    elif case == "incomplete_trust": rows[0]["sender"] = "sender@example.test"
    else: options["specification"] = replace(options["specification"], conventional=(FeatureColumn("model_text","text"),))
    with pytest.raises(InputContractError):
        prepare_content_handoff(tmp_path, "synthetic-content", rows, **options)
    assert not any(tmp_path.iterdir())

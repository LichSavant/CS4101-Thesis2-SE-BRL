import hashlib
from collections import Counter

import pytest

from ml.experiment_inputs import InputContractError, validate_supplied_partitions
from ml.prospective_allocation import connected_groups, exact_relationships, allocate, export_allocation
from ml.prospective_allocation import near_relationships
from ml.prospective_allocation import minhash_relationships


def fixture():
    targets, relationships = {}, []
    for group in range(30):
        left, right = f"synthetic-{group}-a", f"synthetic-{group}-b"
        targets.update({left: 0, right: 1})
        relationships.append(dict(left=left, right=right, kind="exact_duplicate", evidence_reference="synthetic:mixed-native-group"))
    groups = connected_groups(tuple(targets), tuple(relationships), policy_reference="synthetic:explicit-policy")
    return targets, groups


def test_deterministic_connected_components_and_mixed_groups_remain_unsplit(tmp_path):
    targets, groups = fixture()
    parameters = dict(fractions=(.7, .15, .15), seed=42, maximum_fraction_error=.08, policy_reference="synthetic:allocation-option")
    assignments, report = allocate(targets, groups, **parameters)
    again = allocate(dict(reversed(tuple(targets.items()))), dict(reversed(tuple(groups.items()))), **parameters)
    assert assignments == again[0] and report == again[1]
    assert report["mixed_target_groups_retained_unsplit"] == 30
    assert report["model_fits"] == 0
    assert set(a.cv_fold for a in assignments if a.partition == "development") == {1,2,3,4,5}
    counts = validate_supplied_partitions(assignments)
    assert all(counts.values())
    digest = export_allocation(tmp_path / "allocation", assignments, report, targets_by_id=targets, sources_by_id={i:"Synthetic" for i in targets})
    assert len(digest) == 64
    with pytest.raises(InputContractError, match="unused"):
        export_allocation(tmp_path / "allocation", assignments, report, targets_by_id=targets, sources_by_id={i:"Synthetic" for i in targets})


def test_admissible_edges_only_and_exact_keys_have_explicit_provenance():
    same = hashlib.sha256(b"equivalent normalized content").hexdigest()
    edges = exact_relationships({"b":same,"a":same,"c":"e"*64}, normalization_reference="synthetic:same-normalization")
    groups = connected_groups(("a","b","c"),edges,policy_reference="synthetic:hash-evidence")
    assert groups["a"] == groups["b"] != groups["c"]
    with pytest.raises(InputContractError):
        connected_groups(("a","b"),({"left":"a","right":"x","kind":"campaign","evidence_reference":"synthetic:unknown"},),policy_reference="synthetic:test")
    with pytest.raises(InputContractError):
        connected_groups(("a","b"),({"left":"a","right":"b","kind":"source_label","evidence_reference":"synthetic:forbidden"},),policy_reference="synthetic:test")


def test_unmet_constraints_fail_without_fallback_or_output():
    targets, groups = fixture()
    with pytest.raises(InputContractError,match="constraints"):
        allocate(targets,{i:"single-connected-component" for i in targets},fractions=(.7,.15,.15),seed=42,maximum_fraction_error=.01,policy_reference="synthetic:test")
    with pytest.raises(InputContractError):
        allocate(targets,groups,fractions=(.7,.15,.15),seed=42,maximum_fraction_error=None,policy_reference="synthetic:test")


@pytest.mark.parametrize("threshold",(.3,.5,.9,1.))
def test_near_prefix_join_matches_independent_exhaustive_oracle(threshold):
    import random,itertools
    rng=random.Random(42)
    inputs={f"fixture-{i}":tuple(rng.choice(tuple("abcdefghijk")) for _ in range(rng.randrange(3,20))) for i in range(30)}
    inputs["known-near-a"]=tuple("abcdefghijklmnop")
    inputs["known-near-b"]=tuple("abcdefghijklmnopq")
    actual,report=near_relationships(inputs,shingle_size=2,threshold=threshold,minimum_shingles=2,
        max_candidates=10000,max_seconds=5,normalization_reference="synthetic:normalized-tokens")
    sets={i:set(zip(t,t[1:])) for i,t in inputs.items()}
    expected={tuple(sorted((a,b))) for a,b in itertools.combinations(inputs,2)
        if len(sets[a])>=2 and len(sets[b])>=2 and len(sets[a]&sets[b])/len(sets[a]|sets[b])>=threshold}
    assert {tuple(sorted((e["left"],e["right"]))) for e in actual}==expected
    assert report["model_fits"]==0


def test_near_join_budget_failure_and_short_coverage_are_explicit():
    inputs={str(i):tuple("abcdefghijklmnop") for i in range(10)}
    with pytest.raises(InputContractError,match="candidate_budget"):
        near_relationships(inputs,shingle_size=5,threshold=.9,minimum_shingles=5,max_candidates=1,max_seconds=5,normalization_reference="synthetic:test")
    edges,report=near_relationships({"short":("one",)},shingle_size=5,threshold=.9,minimum_shingles=5,max_candidates=1,max_seconds=5,normalization_reference="synthetic:test")
    assert not edges and report["short_records_without_near_coverage"]==1


def test_pinned_minhash_refinement_repeatability_and_explicit_recall_limit():
    pytest.importorskip("datasketch")
    inputs={"a":tuple("abcdefghijklmnop"),"b":tuple("abcdefghijklmnopq"),"c":tuple("zzzyyyxxxwwwvvv"),"short":("one",)}
    options=dict(shingle_size=5,threshold=.9,minimum_shingles=5,num_perm=128,bands=32,rows_per_band=4,seed=42,
        max_candidates=100,max_seconds=5,normalization_reference="synthetic:shared-normalization")
    edges,report=minhash_relationships(inputs,**options)
    again=minhash_relationships(dict(reversed(tuple(inputs.items()))),**options)
    assert (edges,report)==again
    assert {(e["left"],e["right"]) for e in edges}=={("a","b")}
    assert report["short_records_without_near_coverage"]==1 and "miss" in report["recall_limitation"]
    with pytest.raises(InputContractError,match="candidate_budget"):
        minhash_relationships({str(i):tuple("abcdefghijklmnop") for i in range(10)},**dict(options,max_candidates=1))

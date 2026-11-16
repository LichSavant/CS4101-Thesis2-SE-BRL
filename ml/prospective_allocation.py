"""Prospective metadata mechanics; explicit accepted relationships and settings.

No dataset discovery or default scientific relationship threshold. Edges must
already be established by the accepted source-audit policy. Unknown campaign,
template or domain relationships are not invented from labels or source names.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import math
from pathlib import Path
import time

from ml.experiment_inputs import InputContractError, PartitionAssignment, validate_supplied_partitions
from ml.metadata import canonical_json, fingerprint

VERSION = "prospective-components-greedy-allocation-0.1.0"
KINDS = frozenset({"exact_duplicate", "near_duplicate", "template", "campaign", "domain"})


def connected_groups(observation_ids, relationships, *, policy_reference):
    if (type(observation_ids) is not tuple or not observation_ids or len(set(observation_ids)) != len(observation_ids)
            or any(type(i) is not str or not i.strip() for i in observation_ids)
            or type(relationships) is not tuple or type(policy_reference) is not str or not policy_reference.strip()):
        raise InputContractError("explicit_identity_and_relationship_policy_required")
    parent = {i: i for i in observation_ids}
    def root(i):
        while i != parent[i]:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = set()
    for edge in relationships:
        if (type(edge) is not dict or set(edge) != {"left", "right", "kind", "evidence_reference"}
                or edge["left"] not in parent or edge["right"] not in parent or edge["left"] == edge["right"]
                or edge["kind"] not in KINDS or type(edge["evidence_reference"]) is not str or not edge["evidence_reference"].strip()):
            raise InputContractError("admissible_source_relationship_required")
        key = (*sorted((edge["left"], edge["right"])), edge["kind"])
        if key in seen:
            raise InputContractError("duplicate_relationship_record")
        seen.add(key)
        left, right = root(edge["left"]), root(edge["right"])
        parent[max(left, right)] = min(left, right)
    components = defaultdict(list)
    for i in sorted(parent):
        components[root(i)].append(i)
    result = {}
    for members in components.values():
        group = "component-v1-"+fingerprint({"members": members, "policy": policy_reference})
        result.update((i, group) for i in members)
    return result


def exact_relationships(keys_by_id, *, normalization_reference):
    """Only equivalent supplied content hashes; labels never form identity keys."""
    import re
    if type(keys_by_id) is not dict or not keys_by_id or type(normalization_reference) is not str or not normalization_reference.strip():
        raise InputContractError("explicit_equivalent_hash_provenance_required")
    buckets = defaultdict(list)
    for oid, key in keys_by_id.items():
        if type(oid) is not str or not oid or type(key) is not str or not re.fullmatch(r"[a-f0-9]{64}", key):
            raise InputContractError("valid_content_digest_required")
        buckets[key].append(oid)
    return tuple({"left": members[0], "right": i, "kind": "exact_duplicate", "evidence_reference": normalization_reference}
                 for bucket in sorted(buckets.values()) if len(bucket) > 1 for members in (sorted(bucket),) for i in members[1:])


def near_relationships(tokens_by_id, *, shingle_size, threshold, minimum_shingles,
                       max_candidates, max_seconds, normalization_reference):
    """Exact Jaccard join with a common-order prefix filter, not an LSH guess.

    Explicit parameters are candidate science until accepted. Statistics here
    are for pre-allocation grouping only, never classifier preprocessing. A
    budget failure returns no partial edges. Short inputs retain exact matching
    but have explicitly unavailable near-match coverage under this policy.
    """
    if (type(tokens_by_id) is not dict or not tokens_by_id
            or any(type(i) is not str or not i or type(t) is not tuple or any(type(w) is not str or not w for w in t) for i,t in tokens_by_id.items())
            or type(shingle_size) is not int or shingle_size < 1 or type(minimum_shingles) is not int or minimum_shingles < 1
            or type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0 < threshold <= 1
            or type(max_candidates) is not int or max_candidates < 1 or type(max_seconds) not in (int,float)
            or not math.isfinite(max_seconds) or max_seconds <= 0
            or type(normalization_reference) is not str or not normalization_reference.strip()):
        raise InputContractError("explicit_near_duplicate_contract_required")
    deadline=time.monotonic()+max_seconds
    def budget():
        if time.monotonic()>deadline:
            raise InputContractError("near_duplicate_time_budget_exceeded")
    shingles={}
    for oid,tokens in tokens_by_id.items():
        budget()
        value=frozenset(tuple(tokens[i:i+shingle_size]) for i in range(len(tokens)-shingle_size+1))
        if len(value)>=minimum_shingles: shingles[oid]=value
    frequencies=Counter(s for value in shingles.values() for s in value)
    postings=defaultdict(list)
    candidates=set()
    for oid in sorted(shingles):
        budget()
        ordered=sorted(shingles[oid],key=lambda s:(frequencies[s],s))
        prefix=ordered[:len(ordered)-math.ceil(threshold*len(ordered))+1]
        for s in prefix:
            for other in postings[s]:
                # Necessary length condition for Jaccard >= threshold.
                if min(len(shingles[oid]),len(shingles[other])) >= threshold*max(len(shingles[oid]),len(shingles[other])):
                    candidates.add((other,oid))
                    if len(candidates)>max_candidates:
                        raise InputContractError("near_duplicate_candidate_budget_exceeded")
            postings[s].append(oid)
    edges=[]
    for left,right in sorted(candidates):
        budget()
        a,b=shingles[left],shingles[right]
        overlap=len(a&b);union=len(a|b)
        if overlap/union>=threshold:
            edges.append({"left":left,"right":right,"kind":"near_duplicate",
                "evidence_reference":f"{normalization_reference}; exact shingle Jaccard {overlap}/{union}"})
    return tuple(edges),{"method":"exact_jaccard_common_order_prefix_join","shingle_size":shingle_size,"threshold":threshold,
        "minimum_shingles":minimum_shingles,"records":len(tokens_by_id),"eligible_near_match_records":len(shingles),
        "short_records_without_near_coverage":len(tokens_by_id)-len(shingles),"candidate_pairs":len(candidates),
        "qualifying_pairs":len(edges),"max_candidates":max_candidates,"max_seconds":max_seconds,
        "normalization_reference":normalization_reference,"model_fits":0}


def minhash_relationships(tokens_by_id, *, shingle_size, threshold, minimum_shingles, num_perm,
                          bands, rows_per_band, seed, max_candidates, max_seconds, normalization_reference):
    """Paper Table 4.4 MinHash/LSH candidates with exact Jaccard refinement.

    LSH is approximate: refinement removes false positives, not missed pairs.
    The exact-prefix join above is an optional recall audit under its own budget.
    No threshold, seed, banding or short-record rule is silently defaulted.
    """
    from importlib import metadata
    if (type(num_perm) is not int or num_perm < 2 or type(bands) is not int or bands < 2
            or type(rows_per_band) is not int or rows_per_band < 1 or bands*rows_per_band != num_perm
            or type(seed) is not int or not 0 <= seed < 2**32):
        raise InputContractError("explicit_minhash_settings_required")
    # Reuse the exact join's input validation without generating pair candidates.
    # This one-record pass validates science/resource types and no corpus data.
    if type(tokens_by_id) is not dict or not tokens_by_id:
        raise InputContractError("explicit_near_duplicate_contract_required")
    for oid,tokens in tokens_by_id.items():
        if type(oid) is not str or not oid or type(tokens) is not tuple or any(type(w) is not str or not w for w in tokens):
            raise InputContractError("explicit_near_duplicate_contract_required")
    near_relationships({"contract-probe":()},shingle_size=shingle_size,threshold=threshold,minimum_shingles=minimum_shingles,
        max_candidates=max_candidates,max_seconds=max_seconds,normalization_reference=normalization_reference)
    try:
        if metadata.version("datasketch") != "1.6.5":
            raise InputContractError("pinned_minhash_version_required")
        from datasketch import MinHash, MinHashLSH
    except (ImportError, metadata.PackageNotFoundError):
        raise InputContractError("minhash_dependency_unavailable") from None
    deadline=time.monotonic()+max_seconds
    def budget():
        if time.monotonic()>deadline:
            raise InputContractError("near_duplicate_time_budget_exceeded")
    index=MinHashLSH(num_perm=num_perm,params=(bands,rows_per_band))
    sets={};edges=[];candidates=0;short=0
    for oid in sorted(tokens_by_id):
        budget()
        tokens=tokens_by_id[oid]
        shingles=frozenset(tuple(tokens[i:i+shingle_size]) for i in range(len(tokens)-shingle_size+1))
        if len(shingles)<minimum_shingles:
            short+=1;continue
        sketch=MinHash(num_perm=num_perm,seed=seed)
        batch=[]
        for shingle in sorted(shingles):
            batch.append(canonical_json(shingle).encode())
            if len(batch)==1024:
                sketch.update_batch(batch);batch=[];budget()
        if batch:sketch.update_batch(batch)
        for other in sorted(index.query(sketch)):
            budget();candidates+=1
            if candidates>max_candidates:
                raise InputContractError("near_duplicate_candidate_budget_exceeded")
            overlap=len(shingles&sets[other]);union=len(shingles|sets[other])
            if overlap/union>=threshold:
                edges.append({"left":other,"right":oid,"kind":"near_duplicate",
                    "evidence_reference":f"{normalization_reference}; datasketch 1.6.5; exact Jaccard {overlap}/{union}"})
        sets[oid]=shingles;index.insert(oid,sketch)
    return tuple(edges),{"method":"minhash_lsh_exact_jaccard_refinement","datasketch_version":"1.6.5",
        "num_perm":num_perm,"bands":bands,"rows_per_band":rows_per_band,"seed":seed,"shingle_size":shingle_size,
        "threshold":threshold,"minimum_shingles":minimum_shingles,"records":len(tokens_by_id),
        "short_records_without_near_coverage":short,"candidate_pairs":candidates,"qualifying_pairs":len(edges),
        "max_candidates":max_candidates,"max_seconds":max_seconds,"normalization_reference":normalization_reference,
        "recall_limitation":"Approximate candidate retrieval can miss qualifying pairs; exact refinement does not prove exhaustive recall.","model_fits":0}


def _assign(group_counts, fractions, seed, scope):
    total = tuple(sum(v[k] for v in group_counts.values()) for k in (0, 1))
    counts = [[0, 0] for _ in fractions]
    result = {}
    ordered = sorted(group_counts, key=lambda g: (-sum(group_counts[g]), fingerprint((seed, scope, g))))
    for group in ordered:
        values = group_counts[group]
        def cost(bucket):
            # Greedy global target-count discrepancy; no group is ever split.
            return sum(((counts[b][k]+(values[k] if b == bucket else 0))/total[k]-fractions[b])**2
                       for b in range(len(fractions)) for k in (0, 1))
        bucket = min(range(len(fractions)), key=lambda b: (cost(b), fingerprint((seed, scope, group, b))))
        result[group] = bucket
        for k in (0, 1):
            counts[bucket][k] += values[k]
    return result, counts, total


def allocate(targets_by_id, groups_by_id, *, fractions, seed, maximum_fraction_error, policy_reference):
    """Explicit allocation option; reject infeasible/unmet constraints, no fallback.

    This heuristic can fail even when another allocation might be feasible; its
    failure does not prove mathematical infeasibility. Never retry seeds until a
    preferred result appears or split groups to force requested proportions.
    """
    if (type(targets_by_id) is not dict or type(groups_by_id) is not dict or not targets_by_id
            or set(targets_by_id) != set(groups_by_id) or any(type(y) is not int or y not in (0, 1) for y in targets_by_id.values())
            or set(targets_by_id.values()) != {0, 1} or any(type(g) is not str or not g for g in groups_by_id.values())
            or type(fractions) is not tuple or len(fractions) != 3
            or any(type(f) not in (int, float) or not math.isfinite(f) or not 0 < f < 1 for f in fractions)
            or not math.isclose(sum(fractions), 1.) or type(seed) is not int or seed < 0
            or type(maximum_fraction_error) not in (int, float) or not math.isfinite(maximum_fraction_error)
            or not 0 <= maximum_fraction_error < 1 or type(policy_reference) is not str or not policy_reference.strip()):
        raise InputContractError("explicit_group_allocation_settings_required")
    grouped = defaultdict(lambda: [0, 0])
    for oid, y in targets_by_id.items():
        grouped[groups_by_id[oid]][y] += 1
    partitions, counts, totals = _assign(grouped, fractions, seed, "partition")
    if any(not min(c) or any(abs(c[k]/totals[k]-fractions[b]) > maximum_fraction_error for k in (0, 1)) for b, c in enumerate(counts)):
        raise InputContractError("group_allocation_did_not_meet_declared_partition_constraints")
    development = {g: c for g, c in grouped.items() if partitions[g] == 0}
    if len(development) < 5:
        raise InputContractError("insufficient_development_groups_for_five_folds")
    folds, fold_counts, fold_totals = _assign(development, (.2,)*5, seed, "development-fold")
    if any(not min(c) or any(abs(c[k]/fold_totals[k]-.2) > maximum_fraction_error for k in (0, 1)) for c in fold_counts):
        raise InputContractError("group_allocation_did_not_meet_declared_fold_constraints")
    roles = ("development", "calibration", "test")
    assignments = tuple(PartitionAssignment(oid, groups_by_id[oid], roles[partitions[groups_by_id[oid]]],
        folds[groups_by_id[oid]]+1 if partitions[groups_by_id[oid]] == 0 else None) for oid in sorted(targets_by_id))
    validate_supplied_partitions(assignments, folds=5)
    report = {"version": VERSION, "policy_reference": policy_reference, "seed": seed, "fractions": fractions,
        "maximum_fraction_error": maximum_fraction_error, "groups": len(grouped), "observations": len(assignments),
        "mixed_target_groups_retained_unsplit": sum(all(c) for c in grouped.values()),
        "partition_class_counts": dict(zip(roles, counts)), "development_fold_class_counts": fold_counts,
        "assignment_fingerprint": fingerprint([{"id": a.observation_id, "group": a.group_id, "partition": a.partition, "fold": a.cv_fold} for a in assignments]),
        "exposure_note": "New allocation does not reseal historically exposed observations.", "model_fits": 0}
    return assignments, report


def export_allocation(directory, assignments, report, *, targets_by_id, sources_by_id):
    """Exclusive metadata bundle. No raw source/feature payloads are exported."""
    directory = Path(directory)
    if directory.exists() or not directory.parent.is_dir():
        raise InputContractError("unused_allocation_directory_required")
    validate_supplied_partitions(assignments, folds=5)
    ids = {a.observation_id for a in assignments}
    if ids != set(targets_by_id) or ids != set(sources_by_id):
        raise InputContractError("exact_allocation_export_population_required")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=("observation_id", "source_dataset", "target", "group_id", "partition", "cv_fold"))
    writer.writeheader()
    writer.writerows({"observation_id": a.observation_id, "source_dataset": sources_by_id[a.observation_id],
        "target": targets_by_id[a.observation_id], "group_id": a.group_id, "partition": a.partition, "cv_fold": a.cv_fold} for a in assignments)
    payloads = {"assignments.csv": stream.getvalue().encode(), "allocation_report.json": canonical_json(report).encode()}
    manifest = {"version": VERSION, "outputs": {n: hashlib.sha256(b).hexdigest() for n, b in payloads.items()}, "model_fits": 0}
    body = canonical_json(manifest).encode()
    payloads["allocation_manifest.json"] = body
    directory.mkdir()
    created = []
    try:
        for name, payload in payloads.items():
            with (directory / name).open("xb") as f:
                created.append(directory / name); f.write(payload)
    except OSError:
        for p in reversed(created): p.unlink()
        directory.rmdir()
        raise InputContractError("allocation_export_failed") from None
    return hashlib.sha256(body).hexdigest()

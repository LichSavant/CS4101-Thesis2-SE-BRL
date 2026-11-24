"""Read-only historical PhiUSIIL reconciliation; never admission or fitting.

Only development positions are decoded from source/clean CSVs. Other records
are traversed as opaque CSV framing. Same-position equality is a prospective
verification of current bytes, not independently authenticated execution history.
Outputs are exclusive, local evidence; no predictor delivery is generated.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


COLUMNS = ('observation_id', 'source_dataset', 'target', 'group_id', 'partition', 'cv_fold')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical_fold(value):
    if value in {'1', '2', '3', '4', '5'}:
        return value
    if value in {'1.0', '2.0', '3.0', '4.0', '5.0'}:
        return value[0]
    raise ValueError('noncanonical_or_nonintegral_development_fold')


def selected_records(path, positions):
    """Yield (zero-based position, parsed row) only for selected records/header.

    CSV framing supports quoted newlines, escaped quotes and literal quotes in
    unquoted fields. Nonselected records are neither decoded nor CSV-parsed.
    Iteration stops after the last requested record, avoiding unnecessary reads.
    """
    wanted = set(positions) | {-1}
    last = max(wanted)
    position, state, pieces = -1, 'start', []
    with Path(path).open('rb') as stream:
        for line in stream:
            selected = position in wanted
            if selected:
                pieces.append(line)
            for char in line:
                if state == 'quoted':
                    if char == 34:
                        state = 'after_quote'
                elif state == 'after_quote':
                    if char == 34:
                        state = 'quoted'
                    elif char == 44:
                        state = 'start'
                    elif char not in (10, 13):
                        raise ValueError('invalid_csv_after_quote')
                elif char == 34 and state == 'start':
                    state = 'quoted'
                elif char == 44:
                    state = 'start'
                elif char not in (10, 13):
                    state = 'unquoted'
            if state != 'quoted':
                if selected:
                    rows = list(csv.reader(io.StringIO(b''.join(pieces).decode('utf-8-sig'), newline=''), strict=True))
                    if len(rows) != 1:
                        raise ValueError('invalid_csv_record_boundary')
                    yield position, rows[0]
                if position == last:
                    return
                position += 1
                state, pieces = 'start', []
        if state == 'quoted':
            raise ValueError('unterminated_csv_quote')


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def equivalent_cells(left, right, header, numeric_fields):
    """Exact decimal equality for explicitly declared numeric source fields.

    No tolerance, float rounding, imputation, text coercion or label conversion.
    This compares representation; it does not select a predictor dictionary.
    """
    for name, a, b in zip(header, left, right):
        if a == b:
            continue
        if name not in numeric_fields:
            return False
        try:
            x, y = Decimal(a), Decimal(b)
            if not x.is_finite() or not y.is_finite() or x != y:
                return False
        except InvalidOperation:
            return False
    return True


def reconcile(original, cleaned, manifest, output, expected, *, numeric_fields=(), numeric_evidence_sha256=None):
    paths = {'original': Path(original), 'cleaned': Path(cleaned), 'manifest': Path(manifest)}
    hashes = {name: digest(path) for name, path in paths.items()}
    for name in ('original', 'cleaned'):
        if hashes[name] != expected[name]:
            raise ValueError('source_hash_mismatch:' + name)
    # Diagnose the known platform newline difference without rewriting its source.
    manifest_lf = hashlib.sha256(paths['manifest'].read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    if manifest_lf != expected['manifest']:
        raise ValueError('assignment_hash_mismatch')
    dev = {}
    groups, folds, labels, coverage = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(Counter)
    seen, role_counts = set(), Counter()
    with paths['manifest'].open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames) != COLUMNS:
            raise ValueError('assignment_schema_mismatch')
        for row in reader:
            oid, role, group = row['observation_id'], row['partition'], row['group_id']
            if oid in seen or role not in {'development', 'calibration', 'test'}:
                raise ValueError('duplicate_id_or_invalid_role')
            seen.add(oid)
            groups[group].add(role)
            role_counts[role] += 1
            if role != 'development':
                continue  # Do not evaluate reserved target values.
            if row['source_dataset'] != 'PhiUSIIL' or not oid.startswith('PhiUSIIL::'):
                raise ValueError('wrong_source_or_id_format')
            text = oid.removeprefix('PhiUSIIL::')
            if not text.isascii() or not text.isdecimal() or str(int(text)) != text:
                raise ValueError('noncanonical_cleaned_position')
            position = int(text)
            if position in dev or row['target'] not in {'0', '1'}:
                raise ValueError('duplicate_position_or_invalid_target')
            fixed = dict(row, cv_fold=canonical_fold(row['cv_fold']))
            dev[position] = fixed
            folds[group].add(fixed['cv_fold'])
            labels[group].add(row['target'])
            coverage[fixed['cv_fold']][row['target']] += 1
    if not dev or any(len(v) > 1 for v in groups.values()) or any(len(v) > 1 for v in folds.values()):
        raise ValueError('empty_development_or_group_crossing')
    if set(coverage) != {'1','2','3','4','5'} or any(set(v) != {'0','1'} for v in coverage.values()):
        raise ValueError('fold_class_coverage_failed')
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    assignment = out/'development_assignments.normalized.csv'
    with assignment.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(dev[p] for p in sorted(dev))
    raw_iter, clean_iter = selected_records(paths['original'], dev), selected_records(paths['cleaned'], dev)
    _, raw_header = next(raw_iter)
    _, clean_header = next(clean_iter)
    if raw_header != clean_header or len(set(raw_header)) != len(raw_header):
        raise ValueError('source_schema_difference')
    label_index = raw_header.index('label')
    domain_index = raw_header.index('Domain')
    # Exact cells or declared numeric representation equality, without changing
    # source values. Undocumented transformations remain unresolved.
    counts = Counter()
    domain_groups, group_domains = defaultdict(set), defaultdict(set)
    iterator = iter(clean_iter)
    lineage = out/'development_lineage.candidate.jsonl'
    with lineage.open('x', encoding='utf-8', newline='\n') as stream:
        for position, raw in raw_iter:
            clean_position, clean = next(iterator)
            if position != clean_position or len(raw) != len(raw_header) or len(clean) != len(raw_header):
                raise ValueError('source_record_shape_or_position_mismatch')
            native = raw[label_index]
            target_ok = native in {'0','1'} and str(1-int(native)) == dev[position]['target']
            equal = raw == clean
            equivalent = equivalent_cells(raw, clean, raw_header, numeric_fields)
            status = ('exact_cell_and_target_match' if equal else 'declared_numeric_representation_match') if equivalent and target_ok else 'unresolved'
            counts[status] += 1
            if not equal:
                counts['cell_mismatch'] += 1
            if not target_ok:
                counts['target_mismatch'] += 1
            group = dev[position]['group_id']
            # Only hash the development domain; do not disclose URLs/domains.
            domain = hashlib.sha256(clean[domain_index].strip().lower().encode()).hexdigest()
            domain_groups[domain].add(group)
            group_domains[group].add(domain)
            row_hash = lambda row: hashlib.sha256(json.dumps(row, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()
            stream.write(json.dumps({'observation_id':dev[position]['observation_id'], 'original_position_candidate':position,
                'cleaned_position':position, 'original_cells_sha256':row_hash(raw), 'cleaned_cells_sha256':row_hash(clean),
                'status':status, 'historical_lineage_authenticated':False}, sort_keys=True)+'\n')
    processed = counts['exact_cell_and_target_match'] + counts['declared_numeric_representation_match'] + counts['unresolved']
    if processed != len(dev):
        raise ValueError('missing_selected_source_positions')
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise ValueError('extra_cleaned_selected_records')
    if any(digest(path) != hashes[name] for name, path in paths.items()):
        raise ValueError('input_changed_during_execution')
    receipt = {'operation':'explicitly requested no-fit development reconciliation',
        'adapter_sha256':digest(Path(__file__)),
        'numeric_representation_evidence_sha256':numeric_evidence_sha256,
        'numeric_comparison_fields':sorted(numeric_fields),
        'input_sha256':hashes, 'manifest_lf_sha256':manifest_lf,
        'source_files_modified':False,'development_assignment_rows':len(dev),
        'source_and_clean_development_positions_compared':processed,'counts':dict(counts),
        'normalized_folds':['1','2','3','4','5'],'assignment_values_preserved_except_fold_representation':True,
        'partition_counts_metadata_only':dict(role_counts), 'group_role_crossings':0,'development_group_fold_crossings':0,
        'development_mixed_target_groups':sum(len(v)>1 for v in labels.values()),
        'development_fold_class_counts':dict(coverage),
        'development_domain_spans_groups':sum(len(v)>1 for v in domain_groups.values()),
        'development_group_spans_domains':sum(len(v)>1 for v in group_domains.values()),
        'candidate_mapping':'same cleaned rank and original position; all cells exact or declared numeric fields exactly Decimal-equal; native-target correspondence checked',
        'independent_historical_lineage_authenticated':False,
        'ambiguity_limitation':'No cross-position uniqueness or reserved-row comparison performed. Same-position matches do not prove unique historical lineage.',
        'reserved_source_records_decoded':0,'predictor_feature_outputs':0,'admission':'BLOCKED','fits':0,
        'output_sha256':{p.name:digest(p) for p in (assignment,lineage)}}
    write_json(out/'reconciliation_receipt.json', receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    policy=json.loads((root/'ml/research-inputs.v1.json').read_bytes())['artifacts']
    names={'original':'experiments/datasets-raw/webpage/PhiUSIL/PhiUSIIL_Phishing_URL_Dataset.csv',
           'cleaned':'experiments/data/interim/webpage/phiusiil_clean.csv',
           'manifest':'experiments/results/preprocessing/partitions/phiusiil_partition_manifest.csv'}
    metadata=root/'docs/research/2026-11-18_technical_admission/phiusiil/official-metadata.json'
    evidence=root/'docs/research/2026-11-18_technical_admission/phiusiil/feature-dictionary.evidence.json'
    if digest(metadata) != json.loads(evidence.read_bytes())['source_metadata_sha256']:
        raise ValueError('official_type_evidence_hash_mismatch')
    variables=json.loads(metadata.read_bytes())['data']['variables']
    numeric=tuple(v['name'] for v in variables if v['role']=='Feature' and v['type'] in {'Integer','Continuous','Real'})
    result=reconcile(*(args.source_root/names[n] for n in ('original','cleaned','manifest')), args.output,
                     {n:policy[p]['sha256'] for n,p in names.items()}, numeric_fields=numeric,
                     numeric_evidence_sha256=digest(metadata))
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':
    main()

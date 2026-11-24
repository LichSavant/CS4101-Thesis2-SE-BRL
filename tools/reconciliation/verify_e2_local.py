"""Verify preserved E2 bytes and schemas without extraction, training, or telemetry."""
import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E2 = ROOT / 'experiments/e2_enrichment_20261124'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    checks = []
    for name, field in [('v42_candidate_freeze_receipt.json', 'artifact_hashes'),
                        ('v42_exact_run_acceptance_packet.json', 'artifact_hashes')]:
        receipt = json.loads((E2 / name).read_text())
        for relative, expected in receipt[field].items():
            path = E2 / relative
            checks.append({'receipt': name, 'path': relative,
                           'pass': path.is_file() and digest(path) == expected})
            if '--staged' in sys.argv:
                staged = subprocess.run(['git', 'show', ':' + path.relative_to(ROOT).as_posix()],
                                        cwd=ROOT, capture_output=True)
                if staged.returncode == 0:
                    checks.append({'receipt': name, 'path': relative, 'scope': 'staged_bytes',
                                   'pass': hashlib.sha256(staged.stdout).hexdigest() == expected})
    receipt = json.loads((E2 / 'v42_matched_execution_inputs/extraction_receipt.json').read_text())
    matrices = {}
    reference = None
    for name, expected in receipt['feature_hashes'].items():
        path = E2 / 'v42_matched_execution_inputs' / name
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            fields = reader.fieldnames
        metadata = ['observation_id', 'source_dataset', 'target', 'group_id', 'partition', 'cv_fold']
        identity = [tuple(row[key] for key in metadata) for row in rows]
        if reference is None:
            reference = identity
        groups = {}
        for row in rows:
            groups.setdefault(row['group_id'], set()).add(row['cv_fold'])
        checks.append({'path': 'v42_matched_execution_inputs/' + name,
                       'pass': digest(path) == expected and len(rows) == 15011
                       and identity == reference and len({r['observation_id'] for r in rows}) == len(rows)
                       and all(r['partition'] == 'development' for r in rows)
                       and all(len(folds) == 1 for folds in groups.values())})
        matrices[name] = {'observations': len(rows), 'predictors': len(fields) - len(metadata)}
    rules = json.loads((E2 / 'integrated_behavioral_rules_v42.json').read_text())['rules']
    checks.append({'path': 'integrated_behavioral_rules_v42.json', 'pass': len(rules) == 35})
    parsed = 0
    for p in E2.glob('*.py'):
        ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
        parsed += 1
    result = {'status': 'PASS' if all(c['pass'] for c in checks) else 'FAIL',
              'checks': checks, 'matrices': matrices, 'python_modules_parsed': parsed,
              'classifier_fitting_performed': False, 'scientific_admission_granted': False,
              'scope': 'byte integrity, development schema and existing group/fold isolation only; no near-duplicate or campaign-isolation claim'}
    out = ROOT / '.reconciliation-local/e2-verification.json'
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(result['status'], len(checks), 'checks;', parsed, 'modules parsed; no fitting')
    for c in checks:
        if not c['pass']:
            print('FAILED', c['receipt'] if 'receipt' in c else 'matrix/schema', c['path'])
    return 0 if result['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())

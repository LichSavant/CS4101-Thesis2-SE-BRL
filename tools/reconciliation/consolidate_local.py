"""Preserve source variants and assemble a local candidate without fitting or publishing.

Requires inventory_local.py first. Git branch/index updates are deliberately separate.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / '.reconciliation-local'
SCI = ROOT / '.scientific-validation-20261117'
BASE = '6bded57d38e9b83ba718d7795b97e2130128c23f'
REMOTE = 'ee7976ef04aa6060b0c7a5e18e5a6529e0af695e'
RESEARCH = 'e95492ef13039782b43e55dcad42f2421b5aee85'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def tree(ref):
    return git('ls-tree', '-rz', '--name-only', ref).decode().strip('\0').split('\0')

def blob(ref, path):
    return git('show', f'{ref}:{path}')

def normalized(data):
    return data.replace(b'\r\n', b'\n').rstrip()

def write(path, data):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)

def main():
    if (LOCAL / 'integration-decisions.json').exists():
        raise RuntimeError('Assembly already recorded; do not overwrite subsequent integration edits')
    if not (LOCAL / 'inventory.json').exists():
        raise RuntimeError('Recovery inventory required')
    decisions = []
    base_paths = set(tree(BASE))
    remote_paths = set(tree(REMOTE))
    research_paths = set(tree(RESEARCH))
    for path in sorted(remote_paths | research_paths):
        if path.startswith(('experiments/datasets-raw/', 'experiments/data/')):
            decisions.append({'path': path, 'disposition': 'restricted_original_in_place_no_overwrite'})
            continue
        # Research history extends canonical main; use its committed implementation.
        ref = RESEARCH if path in research_paths else REMOTE
        desired = blob(ref, path)
        target = ROOT / path
        if target.exists() and target.read_bytes() != desired:
            current = target.read_bytes()
            known = [desired]
            if path in base_paths:
                known.append(blob(BASE, path))
            if path in remote_paths:
                known.append(blob(REMOTE, path))
            duplicate = any(normalized(current) == normalized(k) for k in known)
            if not duplicate:
                # Every overwritten variant has an immutable content-addressed recovery copy.
                sha = hashlib.sha256(current).hexdigest()
                recovery = LOCAL / 'objects' / sha
                if not recovery.exists():
                    recovery.write_bytes(current)
                decisions.append({'path': path, 'disposition': 'committed_source_selected_local_variant_preserved',
                                  'source_commit': ref, 'local_sha256': sha})
            else:
                decisions.append({'path': path, 'disposition': 'committed_source_selected_duplicate_or_ancestor',
                                  'source_commit': ref})
        else:
            decisions.append({'path': path, 'disposition': 'committed_source_integrated', 'source_commit': ref})
        write(path, desired)

    # Preserve all supplementary E2 artifacts locally, including completed extraction.
    # They are ignored as a unit until publication review classifies individual files.
    for relative in ['experiments/e2_enrichment_20261124', 'experiments/chapter5',
                     'docs/research/2026-11-19_sebrl_nli_development_review',
                     'docs/research/2026-11-21_sebrl_nli_development_review']:
        source = SCI / relative
        if not source.exists():
            continue
        for p in source.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts:
                continue
            dest = ROOT / p.relative_to(SCI)
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            if dest.exists() and dest.read_bytes() != p.read_bytes():
                decisions.append({'path': str(dest.relative_to(ROOT)), 'disposition': 'conflict_source_preserved_in_original',
                                  'source_sha256': sha})
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            decisions.append({'path': dest.relative_to(ROOT).as_posix(), 'source': str(p),
                              'sha256': sha, 'disposition': 'experimental_or_restricted_local_preservation'})

    # Uncommitted rule candidates must never silently replace admitted production rules.
    candidate = ROOT / 'experiments/e2_enrichment_20261124/source_snapshots/scientific_worktree'
    for relative in ['ml/se_brl/context.py', 'ml/se_brl/rules.py',
                     'ml/tests/test_context_detectors.py', 'ml/tests/test_candidate_rule_regression.py',
                     'experiments/vera_validation/V13D_hybrid_extractor.py']:
        source = SCI / relative
        if source.exists():
            dest = candidate / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            decisions.append({'path': dest.relative_to(ROOT).as_posix(), 'source': str(source),
                              'disposition': 'uncommitted_research_candidate_preserved_not_promoted'})
    # Preserve evaluation runners without executing them.
    for source in (SCI / 'scripts').glob('evaluate_sebrl_nli_review*.py'):
        dest = ROOT / 'scripts' / source.name
        if not dest.exists():
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(source, dest)
            decisions.append({'path': dest.relative_to(ROOT).as_posix(), 'disposition': 'research_runner_preserved'})
    ignores = '''
# Reconciliation recovery and restricted local research (never publish wholesale).
/.reconciliation-local/
/.r22-*/
/.scientific-validation-20261117/
/.sprint-transformer-release-readiness/
/experiments/e2_enrichment_20261124/
/experiments/chapter5/
/experiments/runs/
/experiments/datasets-raw/
/experiments/data/interim/
/engineering_completion_*/
/engineering_release_candidate_*/
/engineering_repairs_*/
*.tsbuildinfo
*.log
'''
    with (ROOT / '.gitignore').open('a', encoding='utf-8') as out:
        out.write(ignores)
    (LOCAL / 'integration-decisions.json').write_text(json.dumps(decisions, indent=2), encoding='utf-8')
    print(f'Assembled {len(decisions)} file dispositions; original sources preserved.')

if __name__ == '__main__':
    main()

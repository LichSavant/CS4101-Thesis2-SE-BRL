"""Read-only source inventory and content-addressed recovery (never a publisher)."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.reconciliation-local'
SKIP = {'.git', 'node_modules', '__pycache__', '.pytest_cache', '.venv',
        '.venv-scientific', 'dist', 'build', '.reconciliation-local'}
SOURCES = [ROOT, ROOT / '.scientific-validation-20261117',
           ROOT / '.sprint-transformer-release-readiness', ROOT / '.r22-phase1-integration',
           ROOT / '.r22-review', ROOT / '.r22-vera', ROOT / '.r22-audit/vera-source',
           ROOT.parent / 'Thesis_Prototype', ROOT.parent / 'SE-BRL-Research-Review-Export']

def git(root, *args):
    p = subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', '-C', str(root), *args],
                       capture_output=True)
    return {'exit': p.returncode, 'output': p.stdout.decode('utf-8', 'replace'),
            'error': p.stderr.decode('utf-8', 'replace')}

def files(root):
    errors = []
    for base, dirs, names in os.walk(root, onerror=lambda e: errors.append(str(e))):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(('.venv', '.pytest'))
                   and not (Path(base) == ROOT and d.startswith(('.r22', '.scientific', '.sprint')))]
        for name in names:
            p = Path(base) / name
            if name == '.git' or p.is_symlink():
                continue
            yield p

def main():
    OUT.mkdir(exist_ok=True)
    objects = OUT / 'objects'
    objects.mkdir(exist_ok=True)
    inventory = []
    for root in SOURCES:
        record = {'path': str(root), 'exists': root.exists(), 'files': []}
        if not root.exists():
            inventory.append(record)
            continue
        for key, args in [('head', ['rev-parse', 'HEAD']), ('status', ['status', '--porcelain=v1']),
                          ('branches', ['branch', '-avv']), ('remotes', ['remote', '-v']),
                          ('stashes', ['stash', 'list']), ('worktrees', ['worktree', 'list', '--porcelain'])]:
            record[key] = git(root, *args)
        for p in files(root):
            rel = p.relative_to(root).as_posix()
            try:
                data = p.read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                # Large/raw data remain in place, inventoried by hash. Never overwrite them.
                restricted = any(t in rel.split('/') for t in ['datasets-raw', 'datasets-acquired', 'data'])
                recover = not restricted and len(data) < 5_000_000 and p.suffix.lower() not in {
                    '.zip', '.onnx', '.bin', '.safetensors', '.csv', '.parquet', '.db', '.sqlite3'}
                if recover and not (objects / sha).exists():
                    (objects / sha).write_bytes(data)
                record['files'].append({'path': rel, 'sha256': sha, 'bytes': len(data),
                                        'recovery': str(Path('objects') / sha) if recover else 'original_in_place'})
            except OSError as exc:
                record['files'].append({'path': rel, 'error': str(exc)})
        inventory.append(record)
        print(root.name, len(record['files']), record.get('head', {}).get('output', '').strip())
    (OUT / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    # Exact tracked diff provides an additional compact recovery reference, without raw datasets.
    for root in SOURCES:
        if not root.exists():
            continue
        diff = git(root, 'diff', '--binary', 'HEAD', '--', 'apps', 'backend', 'ml', 'packages', 'tools',
                   'scripts', 'docs', '*.json', '.gitignore')
        (OUT / f'{root.name}-tracked.patch').write_text(diff['output'], encoding='utf-8')

if __name__ == '__main__':
    main()

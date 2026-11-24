"""Preserve distinct public Vera review changes without changing production policy."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REF = '337c3c4f23c1aeff7b16f5d6924eb377a52393af'
PARENT = '25677a98236895ad16c6acf6aa75499dd2552fd9'
DEST = ROOT / 'research/historical/vera-review-337c3c4'

def main():
    changed = subprocess.check_output(['git', 'diff', '--name-only', PARENT, REF], cwd=ROOT).decode().splitlines()
    records = []
    for path in changed:
        data = subprocess.check_output(['git', 'show', f'{REF}:{path}'], cwd=ROOT)
        current = ROOT / path
        same = current.is_file() and current.read_bytes().replace(b'\r\n', b'\n').rstrip() == data.replace(b'\r\n', b'\n').rstrip()
        record = {'source_path': path, 'source_commit': REF, 'sha256': hashlib.sha256(data).hexdigest(),
                  'disposition': 'canonical_duplicate' if same else 'historical_review_variant'}
        if not same:
            target = DEST / path
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError('Refusing to overwrite historical variant: ' + path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            record['destination'] = target.relative_to(ROOT).as_posix()
        records.append(record)
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'source-manifest.json').write_text(json.dumps({'source_repository': 'https://github.com/veramarietherese/-SE-BRL-Research-Review-Vera',
        'source_commit': REF, 'prior_review_commit': PARENT, 'files': records}, indent=2), encoding='utf-8')
    (DEST / 'README.md').write_text('''# Historical Vera review contributions

Source: Vera review commit `337c3c4f23c1aeff7b16f5d6924eb377a52393af`.
The source manifest classifies every changed file since `25677a9` against the
consolidated canonical implementation. Distinct variants are retained here with
their original paths and exact bytes; identical canonical files are not duplicated.

This is a provenance archive, not a second runtime or an admitted replacement.
Its modules and tests retain original imports and are not installed or discovered
by the canonical test commands. Canonical main already contains the approved R22
integration. Review these variants against that integration before any future
semantic-policy adoption. Historical approvals and results retain their original
scope; copying them grants no new scientific authorization.
''', encoding='utf-8')
    print(len(records), 'Vera changes classified;', sum(r['disposition'] != 'canonical_duplicate' for r in records), 'variants preserved')

if __name__ == '__main__':
    main()

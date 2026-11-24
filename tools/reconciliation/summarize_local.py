"""Classify inventoried contributions; emit metadata only, never research rows."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / '.reconciliation-local'

def main():
    sources = json.loads((LOCAL / 'inventory.json').read_text())
    dispositions = []
    for source in sources:
        counts = collections.Counter()
        root = Path(source['path'])
        for record in source['files']:
            relative = record['path']
            if 'sha256' not in record:
                status = 'inaccessible'
            else:
                current = ROOT / relative
                identical = current.is_file() and hashlib.sha256(current.read_bytes()).hexdigest() == record['sha256']
                if identical:
                    status = 'canonical_identical'
                elif record['recovery'] != 'original_in_place':
                    status = 'historical_variant_preserved_in_content_addressed_recovery'
                else:
                    status = 'restricted_or_large_original_retained_in_place'
            counts[status] += 1
            dispositions.append({'source': str(root), 'path': relative, 'sha256': record.get('sha256'), 'disposition': status})
        source['classification_counts'] = dict(counts)
        source['independent_git_root'] = (root / '.git').exists()
    (LOCAL / 'source-dispositions.json').write_text(json.dumps(dispositions, indent=2), encoding='utf-8')
    branches = subprocess.check_output(['git', 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads', 'refs/remotes'], cwd=ROOT).decode().splitlines()
    summary = {'date': '2026-11-25', 'workspaces': [{k: s[k] for k in ['path', 'exists', 'independent_git_root', 'classification_counts']} for s in sources],
               'branch_refs': branches,
               'additional_locations': [
                   {'path': 'C:/Users/Dhanwil/Desktop/SEBRL_Recovery_20261120', 'disposition': 'existing_git_metadata_recovery_retained_no_duplicate_backup'},
                   {'path': 'C:/Users/Dhanwil/AppData/Local/Temp/sebrl-final-int', 'head': '6e699b2f75f77f95ae51b4c0c67e8ff35f927eea', 'disposition': 'clean_detached_worktree_ancestor_of_canonical_main'},
                   {'path': '.r22-phase1-integration/.venv-transformer/integration-final', 'head': '27e19d17046b0e9d83eb0a9ff0517239bf1a48f4', 'disposition': 'locked_initializing_worktree_ancestor_retained'},
                   {'path': 'Vera original device/workspaces', 'disposition': 'not_accessible_remote_review_source_only'}],
               'publication': 'BLOCKED_pending_existing_restricted_LFS_history_review',
               'fitting': 'NOT_AUTHORIZED_NOT_EXECUTED', 'next_action': 'Review dataset/LFS publication boundary before branch push; no main merge without final approval'}
    (LOCAL / 'state.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(len(sources), 'source inventories;', len(dispositions), 'file dispositions;', len(branches), 'branch refs')

if __name__ == '__main__':
    main()

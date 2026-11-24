"""Locate an archived historical path without reading or modifying its contents."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def resolve_path(original, state):
    path = Path(original)
    if not path.is_absolute():
        path = ROOT / path
    duplicate_copies = {Path(item['path']): Path(item['retained'])
                        for item in state['deduplicated']}
    relocations = sorted(state['relocations'], key=lambda item: len(item['source']), reverse=True)
    visited = set()
    while path not in visited:
        visited.add(path)
        if path in duplicate_copies:
            path = duplicate_copies[path]
            continue
        for item in relocations:
            source = Path(item['source'])
            if path == source or source in path.parents:
                path = Path(item['destination']) / path.relative_to(source)
                break
        else:
            return path
    raise ValueError('Relocation mapping contains a cycle')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_path')
    parser.add_argument('--state', type=Path, default=ROOT / '.local/cleanup-state.json')
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding='utf-8-sig'))
    path = resolve_path(args.original_path, state)
    if not path.exists():
        parser.error('Mapped artifact is absent or inaccessible: ' + str(path))
    print(path)


if __name__ == '__main__':
    main()

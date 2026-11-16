"""Export/verify code and cell order only; never execute a notebook."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ml.notebook_sources import NOTEBOOK_STAGES, extract_source, verify_projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=Path("experiments/notebook-sources"))
    parser.add_argument("--notebooks", type=Path, help="Optional read-only original source directory")
    parser.add_argument("--write", action="store_true", help="Create a new output directory; never overwrite")
    args = parser.parse_args()
    if args.write and (args.notebooks is None or args.sources.exists()):
        parser.error("--write requires originals and a new output directory")
    documents = []
    if args.notebooks:
        for name in NOTEBOOK_STAGES:
            first = extract_source(args.notebooks / name)
            if extract_source(args.notebooks / name) != first:
                raise ValueError("Repeated source projection differs")
            documents.append(first)
    if args.write:
        # Validate all sources before creating anything; original files stay read-only.
        for document in documents:
            verify_projection(document)
        args.sources.mkdir(parents=True, exist_ok=False)
        for document in documents:
            (args.sources / (Path(document["notebook"]).stem + ".source.json")).write_text(
                json.dumps(document, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    saved = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(args.sources.glob("*.source.json"))]
    if len(saved) != 5 or {d["notebook"] for d in saved} != set(NOTEBOOK_STAGES):
        raise ValueError("Exactly five actual notebook projections required")
    if documents and sorted(saved, key=lambda d: d["notebook"]) != documents:
        raise ValueError("Saved code/cell order differs from actual notebook source")
    results = [verify_projection(document) for document in saved]
    print(json.dumps({"status": "PASS", "original_sources_compared_twice": bool(documents),
                      "retained_outputs_decoded": False, "notebooks_executed": False,
                      "results": results}, indent=2))


if __name__ == "__main__":
    main()

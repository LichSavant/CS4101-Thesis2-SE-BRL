"""SE-BRL synthetic development challenge comparison (NOT scientific validation).

Place in scripts/ of the existing research worktree and run from repository root:
    python -B -m scripts.evaluate_sebrl_development_challenges

This script reads two explicitly named synthetic challenge CSVs, runs only the existing
rules-only extractor, and compares against disclosed provisional expectations.
It never calls a research-stage authorization or changes that policy: this is NOT
an authorized independent validation, test-set evaluation, or NLI assessment.
No models are trained and original files are not modified.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "experiments" / "vera_validation"
OUTPUT = ROOT / "docs" / "research" / "2026-11-19_sebrl_development_challenge_outputs"
SOURCE = HERE / "V13D_hybrid_extractor.py"
LEX = HERE / "lexical_shortcut_challenges.csv"
CF = HERE / "counterfactual_pairs.csv"
VALID = {"supported", "absent", "unavailable"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path, columns: set[str]) -> list[dict[str, str]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or redirected input: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or not columns.issubset(reader.fieldnames):
            raise ValueError(f"Invalid CSV columns: {path.name}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Empty CSV: {path.name}")
    return rows


def write_csv(path: Path, rows: list[dict]):
    with path.open("x", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    # Fail before evaluating or writing if a previous output exists.
    if OUTPUT.exists():
        raise FileExistsError(f"Existing output preserved: {OUTPUT}")
    if not SOURCE.is_file() or SOURCE.is_symlink():
        raise ValueError("Existing extractor not available as a regular file")
    lex = read_csv(LEX, {"case_id", "challenge_type", "text", "target_indicator", "expected_state_provisional"})
    cf = read_csv(CF, {"pair_id", "target_indicator", "baseline_text", "counterfactual_text", "baseline_expected_provisional", "counterfactual_expected_provisional"})
    if len({r['case_id'] for r in lex}) != len(lex) or len({r['pair_id'] for r in cf}) != len(cf):
        raise ValueError("Duplicate challenge IDs")
    for r in lex:
        if r["expected_state_provisional"] not in VALID:
            raise ValueError(f"Invalid provisional state: {r['case_id']}")
    for r in cf:
        if r["baseline_expected_provisional"] not in VALID or r["counterfactual_expected_provisional"] not in VALID:
            raise ValueError(f"Invalid provisional state: {r['pair_id']}")

    sys.path.insert(0, str(HERE))
    from V13D_hybrid_extractor import rules_only  # pylint: disable=import-error

    def predict(text: str, indicator: str):
        result = rules_only(text, modality="content_bearing_email")
        if indicator not in result:
            raise ValueError(f"Unknown indicator: {indicator}")
        item = result[indicator]
        state = item["state"]
        if state not in VALID:
            raise ValueError("Unexpected extractor state")
        return state, json.dumps(item.get("evidence", []), ensure_ascii=False)

    lexical_output = []
    for r in lex:
        state, evidence = predict(r["text"], r["target_indicator"])
        lexical_output.append({
            "case_id": r["case_id"], "challenge_type": r["challenge_type"], "target_indicator": r["target_indicator"],
            "text": r["text"], "provisional_expected": r["expected_state_provisional"],
            "rules_only_predicted": state, "rules_evidence_json": evidence,
            "matches_provisional": str(state == r["expected_state_provisional"]).lower(),
        })

    counterfactual_output = []
    for r in cf:
        base, base_evidence = predict(r["baseline_text"], r["target_indicator"])
        changed, changed_evidence = predict(r["counterfactual_text"], r["target_indicator"])
        counterfactual_output.append({
            "pair_id": r["pair_id"], "target_indicator": r["target_indicator"],
            "baseline_text": r["baseline_text"], "baseline_provisional_expected": r["baseline_expected_provisional"],
            "baseline_rules_prediction": base, "baseline_rules_evidence_json": base_evidence,
            "counterfactual_text": r["counterfactual_text"],
            "counterfactual_provisional_expected": r["counterfactual_expected_provisional"],
            "counterfactual_rules_prediction": changed, "counterfactual_rules_evidence_json": changed_evidence,
            "both_match_provisional": str(base == r["baseline_expected_provisional"] and changed == r["counterfactual_expected_provisional"]).lower(),
            "directional_absent_to_supported": str(base == "absent" and changed == "supported").lower(),
        })

    lex_match = sum(r["matches_provisional"] == "true" for r in lexical_output)
    cf_pair_match = sum(r["both_match_provisional"] == "true" for r in counterfactual_output)
    cf_directional = sum(r["directional_absent_to_supported"] == "true" for r in counterfactual_output)
    summary = {
        "status": "DEVELOPMENT_CHALLENGE_COMPARISON_COMPLETE",
        "scope": "synthetic development-only, known provisional expected states; not independent human ground truth",
        "extractor_mode": "rules_only",
        "modality_assumption": "content_bearing_email",
        "model_fits": 0, "nli_inference": False,
        "lexical": {"total": len(lex), "matches_provisional": lex_match,
                    "mismatches": [r["case_id"] for r in lexical_output if r["matches_provisional"] != "true"],
                    "categories": dict(Counter(r["challenge_type"] for r in lex))},
        "counterfactual": {"pairs": len(cf), "both_states_match_provisional": cf_pair_match,
                           "absent_to_supported_directional": cf_directional,
                           "mismatches": [r["pair_id"] for r in counterfactual_output if r["both_match_provisional"] != "true"]},
        "source_sha256": {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in (SOURCE, LEX, CF,
                      ROOT / "ml" / "se_brl" / "codebook.v0.1.0.json")},
        "scientific_limitations": [
            "Original challenge files contain visible provisional expectations; no blinding",
            "These are synthetic development cases, not independently adjudicated real-world labels",
            "Behavioral scientific validation authorization remains closed and unchanged",
            "Only target-indicator states are assessed; no full 12-indicator effectiveness claim",
            "Transformer/NLI is not executed; review-only contribution is not evaluated",
            "No train/test generalization or statistical significance is implied",
        ],
    }
    OUTPUT.mkdir(parents=True, exist_ok=False)
    write_csv(OUTPUT / "lexical_rules_only.csv", lexical_output)
    write_csv(OUTPUT / "counterfactual_rules_only.csv", counterfactual_output)
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "lexical": summary["lexical"],
                      "counterfactual": summary["counterfactual"], "fits": 0,
                      "output": str(OUTPUT.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

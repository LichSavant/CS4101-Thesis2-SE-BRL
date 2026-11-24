
from pathlib import Path
from dataclasses import replace
import hashlib
import json
import types

from ml.se_brl import extraction
from ml.se_brl.rules import RULES
from ml.se_brl.extraction import RuleEngine

from supplementary_exporter import build_representations

HERE = Path(__file__).resolve().parent


class SupplementaryExtractionAdapter:

    def __init__(self):
        self.config = json.loads(
            (HERE / "candidate_rules_v3.json")
            .read_text(encoding="utf-8")
        )

        self.dictionary = json.loads(
            (HERE / "ordered_predictor_dictionary.json")
            .read_text(encoding="utf-8")
        )["ordered_predictors"]

        original = {r.rule_id: r for r in RULES}
        supplied = self.config["rules"]
        candidate = {r["rule_id"]: r for r in supplied}

        if len(candidate) != len(supplied):
            raise ValueError("Duplicate candidate rule IDs")

        if set(original) != set(candidate):
            raise ValueError("Candidate rule registry mismatch")

        rules = []

        for rule in RULES:
            item = candidate[rule.rule_id]

            if rule.indicator_id != item["indicator_id"]:
                raise ValueError("Indicator meaning changed")

            rules.append(
                replace(rule, pattern=item["pattern"])
            )

        context_path = HERE / "candidate_context_v1.py"

        from ml.se_brl import context as original_context

        candidate_context = types.ModuleType(
            "ml.se_brl._supplementary_context"
        )

        candidate_context.__package__ = "ml.se_brl"
        candidate_context.__file__ = str(context_path)

        import sys

        sys.modules[candidate_context.__name__] = candidate_context

        try:
            exec(
                compile(
                    context_path.read_text(encoding="utf-8"),
                    str(context_path),
                    "exec"
                ),
                candidate_context.__dict__
            )
        except Exception:
            sys.modules.pop(candidate_context.__name__, None)
            raise

        self.candidate_context = candidate_context.ContextIndex

        self.baseline_engine = RuleEngine()

        self.candidate_engine = RuleEngine(
            rules=tuple(rules),
            version=self.config["candidate_version"]
        )

    def extract_pair(self, prepared_artifact):

        baseline_result = self.baseline_engine.extract(
            prepared_artifact
        )

        original_context = extraction.ContextIndex

        try:
            extraction.ContextIndex = self.candidate_context

            candidate_result = self.candidate_engine.extract(
                prepared_artifact
            )
        finally:
            extraction.ContextIndex = original_context

        baseline_vectors = build_representations(
            baseline_result
        )

        candidate_vectors = build_representations(
            candidate_result
        )

        for name, columns in self.dictionary.items():
            if set(candidate_vectors[name]) != set(columns):
                raise ValueError("Ordered predictor mismatch")

        return {
            "baseline_extraction": baseline_result,
            "candidate_extraction": candidate_result,
            "baseline_8": baseline_vectors["E2-A"],
            "candidate_vectors": candidate_vectors
        }

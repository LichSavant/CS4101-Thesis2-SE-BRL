"""Read-only code/cell-order projection. Outputs and metadata are opaque bytes.

This module never imports or executes notebook code. Only structural keys,
cell_type, nbformat, and code-cell source are JSON-decoded. Markdown/raw source,
outputs, execution counts, attachments and metadata are structurally skipped.
"""
from __future__ import annotations

import hashlib
import ast
import json
import re
from pathlib import Path


class SourceProjectionError(ValueError):
    pass


class _Reader:
    def __init__(self, stream):
        self.stream = stream

    def peek(self):
        pos = self.stream.tell()
        value = self.stream.read(1)
        self.stream.seek(pos)
        return value

    def whitespace(self):
        while self.peek() in (b" ", b"\n", b"\r", b"\t"):
            self.stream.read(1)

    def take(self, token):
        self.whitespace()
        if self.stream.read(1) != token:
            raise SourceProjectionError("Invalid JSON structure")

    def string(self):
        self.take(b'"')
        while True:
            c = self.stream.read(1)
            if not c or c < b" ":
                raise SourceProjectionError("Invalid JSON string")
            if c == b'"':
                return
            if c == b"\\":
                escaped = self.stream.read(1)
                if escaped == b"u":
                    if not re.fullmatch(b"[0-9a-fA-F]{4}", self.stream.read(4)):
                        raise SourceProjectionError("Invalid JSON escape")
                elif escaped not in (b'"', b"\\", b"/", b"b", b"f", b"n", b"r", b"t"):
                    raise SourceProjectionError("Invalid JSON escape")

    def skip(self, depth=0):
        if depth > 128:
            raise SourceProjectionError("JSON nesting limit")
        self.whitespace()
        c = self.peek()
        if c == b'"':
            self.string()
        elif c in (b"{", b"["):
            self.stream.read(1)
            closing = b"}" if c == b"{" else b"]"
            self.whitespace()
            if self.peek() == closing:
                self.stream.read(1)
                return
            while True:
                if c == b"{":
                    self.string()  # opaque key, including keys inside outputs
                    self.take(b":")
                self.skip(depth + 1)
                self.whitespace()
                delimiter = self.stream.read(1)
                if delimiter == closing:
                    return
                if delimiter != b",":
                    raise SourceProjectionError("Invalid JSON delimiter")
        else:
            token = bytearray()
            while self.peek() and self.peek() not in b" \n\r\t,]}":
                token.extend(self.stream.read(1))
                if len(token) > 128:
                    raise SourceProjectionError("Invalid JSON scalar")
            if not re.fullmatch(rb"(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)", token):
                raise SourceProjectionError("Invalid JSON scalar")

    def decode_range(self, start, end, limit):
        if end - start > limit:
            raise SourceProjectionError("Selected source size limit")
        resume = self.stream.tell()
        self.stream.seek(start)
        raw = self.stream.read(end - start)
        self.stream.seek(resume)
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError):
            raise SourceProjectionError("Invalid selected source JSON") from None

    def members(self):
        self.take(b"{")
        self.whitespace()
        if self.peek() == b"}":
            self.stream.read(1)
            return
        seen = set()
        while True:
            self.whitespace()
            start = self.stream.tell()
            self.string()
            key = self.decode_range(start, self.stream.tell(), 1024)
            if key in seen:
                raise SourceProjectionError("Duplicate structural key")
            seen.add(key)
            self.take(b":")
            self.whitespace()
            yield key  # caller must consume value before generator resumes
            self.whitespace()
            delimiter = self.stream.read(1)
            if delimiter == b"}":
                return
            if delimiter != b",":
                raise SourceProjectionError("Invalid object delimiter")

    def cell(self, index):
        kind = source_range = None
        for key in self.members():
            start = self.stream.tell()
            self.skip()
            end = self.stream.tell()
            if key == "cell_type":
                kind = self.decode_range(start, end, 64)
            elif key == "source":
                source_range = (start, end)
        if kind not in ("code", "markdown", "raw") or source_range is None:
            raise SourceProjectionError("Missing cell type or source")
        cell = {"index": index, "cell_type": kind}
        if kind == "code":
            source = self.decode_range(*source_range, 2_000_000)
            if isinstance(source, list) and all(type(line) is str for line in source):
                source = "".join(source)
            if type(source) is not str:
                raise SourceProjectionError("Invalid code source")
            cell["source"] = source
        return cell

    def cells(self):
        result = []
        self.take(b"[")
        self.whitespace()
        if self.peek() == b"]":
            self.stream.read(1)
            return result
        while True:
            if len(result) >= 10_000:
                raise SourceProjectionError("Cell count limit")
            result.append(self.cell(len(result)))
            self.whitespace()
            delimiter = self.stream.read(1)
            if delimiter == b"]":
                return result
            if delimiter != b",":
                raise SourceProjectionError("Invalid cells delimiter")


def extract_source(path: Path) -> dict:
    """Read a regular notebook without following symlinks or decoding outputs."""
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
        raise SourceProjectionError("Expected a bounded regular notebook")
    before = path.stat()
    cells = version = None
    with path.open("rb") as stream:
        reader = _Reader(stream)
        for key in reader.members():
            if key == "cells":
                cells = reader.cells()
            else:
                start = stream.tell()
                reader.skip()
                if key == "nbformat":
                    version = reader.decode_range(start, stream.tell(), 16)
        reader.whitespace()
        if reader.peek():
            raise SourceProjectionError("Trailing notebook content")
    if type(version) is not int or version != 4 or cells is None:
        raise SourceProjectionError("Expected notebook format 4")
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise SourceProjectionError("Notebook changed during projection")
    result = {"schema": "notebook-code-source-v1", "notebook": path.name, "nbformat": 4, "cells": cells}
    result["code_order_sha256"] = hashlib.sha256(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


NOTEBOOK_STAGES = {
    "01_data_audit.ipynb": "preprocessing", "02_data_cleaning.ipynb": "preprocessing",
    "03_preprocessing.ipynb": "preprocessing", "04_feature_extraction.ipynb": "features",
    "05_experiments.ipynb": "training",
}
_BOOTSTRAP = '''from pathlib import Path as _PolicyPath
import sys as _policy_sys
_policy_root = next((p for p in [_PolicyPath.cwd(), *_PolicyPath.cwd().parents]
                     if (p / "ml" / "research_policy.py").is_file()), None)
if _policy_root is None:
    raise RuntimeError("Research policy unavailable; refusing execution")
if str(_policy_root) not in _policy_sys.path:
    _policy_sys.path.insert(0, str(_policy_root))
from ml.research_policy import require_stage_authorization, read_research_csv, verify_research_path
'''


def verify_projection(document: dict) -> dict:
    """Verify exact closed bootstrap and checked loaders using AST only.

    Invalid later Python is reported, never repaired or executed. This checks
    sequential, unmodified sources; arbitrary interactive cell reordering is not
    authorized. It is not a claim that the analytical notebook is runnable.
    """
    from ml.research_policy import reject_excluded
    if (set(document) != {"schema", "notebook", "nbformat", "cells", "code_order_sha256"}
            or document["schema"] != "notebook-code-source-v1" or document["nbformat"] != 4
            or document["notebook"] not in NOTEBOOK_STAGES):
        raise SourceProjectionError("Invalid source projection schema")
    content = {key: value for key, value in document.items() if key != "code_order_sha256"}
    digest = hashlib.sha256(json.dumps(content, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if digest != document["code_order_sha256"]:
        raise SourceProjectionError("Code/cell-order fingerprint mismatch")
    cells = document["cells"]
    if type(cells) is not list or not cells or cells[0].get("cell_type") != "code":
        raise SourceProjectionError("First cell must be the guard")
    stage = NOTEBOOK_STAGES[document["notebook"]]
    expected = ast.parse(_BOOTSTRAP + f'require_stage_authorization("{stage}")\n')
    try:
        actual = ast.parse(cells[0]["source"])
    except (KeyError, SyntaxError):
        raise SourceProjectionError("Invalid first guard cell") from None
    if ast.dump(actual) != ast.dump(expected):
        raise SourceProjectionError("Guard must be unconditional and precede all analytical cells")
    invalid, loaders, code_count = [], [], 0
    for index, cell in enumerate(cells):
        kind = cell.get("cell_type")
        if (kind not in {"code", "markdown", "raw"} or type(cell.get("index")) is not int
                or cell["index"] != index
                or set(cell) != ({"index", "cell_type", "source"} if kind == "code" else {"index", "cell_type"})):
            raise SourceProjectionError("Invalid cell order or extra retained content")
        if kind != "code":
            continue
        code_count += 1
        source = cell["source"]
        if type(source) is not str:
            raise SourceProjectionError("Invalid code source")
        reject_excluded(source)
        if re.search(r"\.(?:read_csv|glob|rglob)\s*\(", source):
            raise SourceProjectionError("Unchecked loader or broad discovery")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            invalid.append({"cell": index, "line": exc.lineno, "reason": "historical_non_python_code_cell"})
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name == "arff.loadarff":
                    if (len(node.args) != 1 or not isinstance(node.args[0], ast.Call)
                            or ast.unparse(node.args[0].func) != "verify_research_path"):
                        raise SourceProjectionError("Unchecked ARFF loader")
                    loaders.append({"cell": index, "loader": "arff.loadarff(verify_research_path(...))"})
                elif name == "read_research_csv":
                    loaders.append({"cell": index, "loader": name})
    return {"notebook": document["notebook"], "code_order_sha256": digest, "stage": stage,
            "cell_count": len(cells), "code_cell_count": code_count, "guard_verified": True,
            "checked_loaders": loaders, "historical_syntax_issues": invalid, "executed": False}

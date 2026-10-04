"""Small immutable JSON metadata helpers; no artifact or model persistence."""

import hashlib
import json
import math
from collections.abc import Mapping
from types import MappingProxyType


def freeze_json(value: object, depth: int = 0) -> object:
    if depth > 16:
        raise ValueError("Metadata nesting exceeds the supported limit")
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, Mapping):
        if any(type(k) is not str for k in value):
            raise ValueError("Metadata keys must be strings")
        return MappingProxyType({k: freeze_json(v, depth + 1) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(v, depth + 1) for v in value)
    raise ValueError("Metadata must contain finite JSON values")


def json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(v) for v in value]
    return value


def canonical_json(value: object) -> str:
    return json.dumps(json_value(freeze_json(value)), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require_text(value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError("Metadata identifier must be a nonempty string")

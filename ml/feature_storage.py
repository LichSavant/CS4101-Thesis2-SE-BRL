"""Immutable Mapping boundary for future sparse backends, without scipy dependency.

Feature names retain schema order; omitted sparse entries mean zero, never missing.
Unknown learned values must be explicit None entries. This is not a TF-IDF rewrite.
"""

from collections.abc import Iterator, Mapping
import math
from types import MappingProxyType


def validate_value(value: object) -> None:
    if value is not None and (type(value) not in (float, int) or not math.isfinite(value)):
        raise ValueError("Feature values must be finite numbers or explicit None")


class SparseFeatureValues(Mapping[str, float | None]):
    __slots__ = ("_names", "_values")

    def __init__(self, names: tuple[str, ...], nonzero_values: Mapping[str, float | None]) -> None:
        if (type(names) is not tuple or any(type(n) is not str or not n for n in names)
                or len(set(names)) != len(names) or not set(nonzero_values) <= set(names)):
            raise ValueError("Invalid sparse feature schema")
        for value in nonzero_values.values():
            validate_value(value)
        object.__setattr__(self, "_names", MappingProxyType(dict.fromkeys(names)))
        object.__setattr__(self, "_values", MappingProxyType({k: v for k, v in nonzero_values.items() if v != 0}))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Sparse feature storage is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Sparse feature storage is immutable")

    def __getitem__(self, key: str) -> float | None:
        if key not in self._names:
            raise KeyError(key)
        return self._values.get(key, 0.0)

    def __iter__(self) -> Iterator[str]:
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)

    @property
    def has_missing_values(self) -> bool:
        return any(value is None for value in self._values.values())

    def nonzero_items(self) -> tuple[tuple[str, float | None], ...]:
        return tuple(self._values.items())


class CombinedFeatureValues(Mapping[str, float | None]):
    __slots__ = ("_parts", "_owners")

    def __init__(self, parts: tuple[Mapping[str, float | None], ...]) -> None:
        frozen = tuple(part if isinstance(part, (SparseFeatureValues, CombinedFeatureValues))
                       else MappingProxyType(dict(part)) for part in parts)
        owners = {}
        for index, part in enumerate(frozen):
            if not isinstance(part, (SparseFeatureValues, CombinedFeatureValues)):
                for key, value in part.items():
                    if type(key) is not str or not key:
                        raise ValueError("Feature names must be nonempty strings")
                    validate_value(value)
            for name in part:
                if name in owners:
                    raise ValueError("Feature blocks have overlapping names")
                owners[name] = index
        object.__setattr__(self, "_parts", frozen)
        object.__setattr__(self, "_owners", MappingProxyType(owners))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Combined feature storage is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Combined feature storage is immutable")

    def __getitem__(self, key: str) -> float | None:
        return self._parts[self._owners[key]][key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._owners)

    def __len__(self) -> int:
        return len(self._owners)

    @property
    def has_missing_values(self) -> bool:
        return any(part.has_missing_values if isinstance(part, (SparseFeatureValues, CombinedFeatureValues))
                   else any(v is None for v in part.values()) for part in self._parts)

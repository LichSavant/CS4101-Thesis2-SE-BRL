"""Validate supplied grouping metadata against existing splits; never make splits."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from ml.features import SplitManifest
from ml.metadata import require_text


class GroupKind(Enum):
    DUPLICATE_CLUSTER = "duplicate_cluster"
    EMAIL_THREAD = "email_thread"
    CAMPAIGN = "campaign"
    DOMAIN_FAMILY = "domain_family"
    SOURCE_FAMILY = "source_family"


@dataclass(frozen=True, slots=True)
class GroupIdentifier:
    kind: GroupKind
    namespace: str
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, GroupKind):
            raise ValueError("Grouping requires an explicit group kind")
        require_text(self.namespace)
        require_text(self.value)


def validate_groups(groups: tuple[GroupIdentifier, ...]) -> None:
    if type(groups) is not tuple or any(not isinstance(g, GroupIdentifier) for g in groups):
        raise ValueError("Groups must be immutable typed identifiers")
    keys = [(g.kind, g.namespace) for g in groups]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate or contradictory group assignments")


@dataclass(frozen=True, slots=True)
class GroupAwareManifest:
    split: SplitManifest
    groups_by_record: Mapping[str, tuple[GroupIdentifier, ...]]
    protected_kinds: tuple[GroupKind, ...] = tuple(GroupKind)

    def __post_init__(self) -> None:
        if not isinstance(self.split, SplitManifest) or not isinstance(self.groups_by_record, Mapping):
            raise ValueError("Expected a split manifest and record group mapping")
        if (type(self.protected_kinds) is not tuple or not self.protected_kinds
                or any(not isinstance(k, GroupKind) for k in self.protected_kinds)
                or len(set(self.protected_kinds)) != len(self.protected_kinds)):
            raise ValueError("Invalid protected group kinds")
        partitions = {record: partition for partition, ids in (
            ("train", self.split.train_ids), ("validation", self.split.validation_ids), ("test", self.split.test_ids)
        ) for record in ids}
        if set(self.groups_by_record) != set(partitions):
            raise ValueError("Group metadata must cover exactly the split records; use empty tuples for unknown groups")
        owners: dict[GroupIdentifier, str] = {}
        for record, groups in self.groups_by_record.items():
            validate_groups(groups)
            for group in groups:
                if group.kind not in self.protected_kinds:
                    continue
                previous = owners.setdefault(group, partitions[record])
                if previous != partitions[record]:
                    raise ValueError("A protected group crosses split partitions")
        object.__setattr__(self, "groups_by_record", MappingProxyType(dict(self.groups_by_record)))

    @property
    def missing_group_metadata(self) -> tuple[tuple[str, GroupKind], ...]:
        return tuple((record, kind) for record in sorted(self.groups_by_record)
                     for kind in self.protected_kinds
                     if not any(g.kind == kind for g in self.groups_by_record[record]))

    def require_complete(self) -> None:
        if self.missing_group_metadata:
            raise ValueError("Grouping audit is incomplete; missing groups cannot prove isolation")

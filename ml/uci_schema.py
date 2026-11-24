"""UCI native-domain checks, not source authentication or scientific admission.

Domain facts are transcribed from the retained native-value audit and acceptance
packet. Numeric codes are preserved; this module assigns no semantic labels.
The generic handoff's existing nullable representation remains unchanged.
"""
import json
from pathlib import Path
from types import MappingProxyType

from ml.experiment_inputs import InputContractError


SCHEMA_PATH = Path(__file__).with_name("uci-native-schema.v1.json")
_schema = json.loads(SCHEMA_PATH.read_bytes())
NATIVE_DOMAINS = MappingProxyType({
    feature["name"]: frozenset(feature["native_domain"])
    for feature in _schema["features"]
})


def validate_native_feature(name, value):
    """Reject invented fields and out-of-domain codes before handoff creation.

    Run the existing numeric-type/finite validator first. None remains an
    explicit missing value, not zero or an approved missingness policy.
    """
    if name not in NATIVE_DOMAINS:
        raise InputContractError("uci_native_feature_required")
    if value is not None and value not in NATIVE_DOMAINS[name]:
        raise InputContractError("uci_native_feature_domain_mismatch")

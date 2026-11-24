
import math
from numbers import Real

def validate_vector(vector, approved_columns, expected_size):
    columns = tuple(approved_columns)

    if len(columns) != expected_size:
        raise ValueError("Unexpected feature count")

    if len(set(columns)) != len(columns):
        raise ValueError("Duplicate feature names")

    if set(vector) != set(columns):
        raise ValueError("Feature schema mismatch")

    for name, value in vector.items():
        if value is None:
            continue

        if not isinstance(value, Real):
            raise ValueError(f"Non-numeric feature: {name}")

        if not math.isfinite(float(value)):
            raise ValueError(f"Non-finite feature: {name}")

        if name.endswith(("_supported", "_support", "_available", "_availability")):
            if value not in (0, 1):
                raise ValueError(f"Invalid binary feature: {name}")

        if name.endswith(("_count", "_evidence_count")):
            if value < 0 or int(value) != value:
                raise ValueError(f"Invalid evidence count: {name}")

    return True

"""In-memory prospective UCI candidate construction for separately authorized use.

No filesystem/network loader or CLI. Tests use generated ARFF bytes only. This
does not authenticate access, approve a conflict policy or assign partitions.
"""
import hashlib
import re

from ml.experiment_inputs import InputContractError
from ml.metadata import fingerprint
from ml.research_protocol import prospective_id
from ml.uci_lineage import validate_prospective_uci_ledger
from ml.uci_schema import NATIVE_DOMAINS


def reconstruct_candidate(payload, *, expected_sha256, original_count, retained_count):
    if (type(original_count) is not int or type(retained_count) is not int
            or not 0 < retained_count <= original_count):
        raise InputContractError("explicit_positive_uci_processing_scope_required")
    if (type(payload) is not bytes or type(expected_sha256) is not str
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)
            or hashlib.sha256(payload).hexdigest() != expected_sha256):
        raise InputContractError("pinned_uci_source_bytes_required")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeError:
        raise InputContractError("uci_source_encoding_invalid") from None
    names = (*NATIVE_DOMAINS, "Result")
    domains = (*NATIVE_DOMAINS.values(), frozenset({-1, 1}))
    declared, records, relation, in_data = [], [], False, False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        if not in_data:
            if re.fullmatch(r"@relation\s+\S+", line, re.I) and not relation:
                relation = True
                continue
            if re.fullmatch(r"@data", line, re.I):
                if not relation or tuple(declared) != names:
                    raise InputContractError("exact_ordered_uci_source_schema_required")
                in_data = True
                continue
            match = re.fullmatch(r"@attribute\s+(?:'([^']+)'|\"([^\"]+)\"|(\S+))\s+\{([^}]+)\}", line, re.I)
            if not match or len(declared) >= 31:
                raise InputContractError("exact_ordered_uci_source_schema_required")
            name = next(x for x in match.groups()[:3] if x is not None)
            values = tuple(v.strip() for v in match[4].split(","))
            if (name != names[len(declared)] or len(values) != len(set(values))
                    or set(values) != {str(v) for v in domains[len(declared)]}):
                raise InputContractError("exact_ordered_uci_source_schema_required")
            declared.append(name)
        else:
            if len(records) >= original_count:
                raise InputContractError("uci_original_record_scope_exceeded")
            values = tuple(v.strip() for v in line.split(","))
            if (len(values) != 31 or any(v not in {str(n) for n in domain}
                                       for v, domain in zip(values, domains))):
                raise InputContractError("invalid_uci_native_record_abort_no_partial_output")
            records.append(tuple(int(v) for v in values))
    if not in_data:
        raise InputContractError("exact_ordered_uci_source_schema_required")
    ledger, retained, representatives = [], [], {}
    for position, values in enumerate(records):
        oid = prospective_id("UCI Phishing Websites", expected_sha256, "Training Dataset.arff", position)
        record_digest = fingerprint({"columns": names, "values": values})
        predictor_digest = fingerprint({"columns": names[:-1], "values": values[:-1]})
        duplicate = record_digest in representatives
        representative = representatives.setdefault(record_digest, oid)
        ledger.append(dict(source_row_id=position, observation_id=oid, native_label=values[-1],
                           record_sha256=record_digest, predictor_sha256=predictor_digest,
                           action="duplicate" if duplicate else "retain", representative_id=representative,
                           cleaned_position=None if duplicate else len(retained)))
        if not duplicate:
            retained.append({"observation_id": oid, "source_row_id": position,
                             "native_label": values[-1], "features": dict(zip(names[:-1], values[:-1]))})
    validation = validate_prospective_uci_ledger(ledger, snapshot_sha256=expected_sha256,
                                              original_count=original_count, retained_count=retained_count)
    return {"ledger": ledger, "retained_records": retained, "validation": validation,
            "source_sha256": expected_sha256, "target_labels_constructed": False,
            "partitions_generated": False, "protocol_approved": False,
            "note": "Prospective candidate only; native codes have not been assigned class meanings."}

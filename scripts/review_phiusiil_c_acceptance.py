"""Read-only independent-review aid: source comparison plus exact C receipt.

No writes, allocation or fitting. The reviewer must authenticate human response
provenance and supply its digest independently; this script cannot establish trust.
"""
import argparse
from datetime import date
import json
from pathlib import Path

from scripts.verify_phiusiil_c_acceptance import verify
from scripts.phiusiil_reconcile import digest
from ml.research_protocol import _read, _json, code_hashes
from ml.experiment_inputs import InputContractError


BASE = 'docs/research/2026-11-18_technical_admission/'


def check_receipt(receipt, specification, actual_code):
    """Same structural constraints as C plus exact packet-bound run identity."""
    if set(receipt) != set(specification['root_keys_exact']):
        raise ValueError('exact_C_receipt_keys_required')
    for key, value in specification['fixed_values'].items():
        if receipt[key] != value:
            raise ValueError('exact_packet_scope_required')
    authority = receipt['authority']
    if (not isinstance(authority, dict) or set(authority) != set(specification['authority_exact_keys'])
            or any(type(v) is not str or not v.strip() for v in authority.values())
            or authority['role'] not in {'researcher','adviser'}
            or date.fromisoformat(authority['date']) > date.today()
            or len(authority['response_text']) < 40):
        raise ValueError('actual_dated_authority_response_required')
    if receipt['input_sha256'] != specification['input_sha256_exact']:
        raise ValueError('exact_packet_input_hashes_required')
    if not actual_code or receipt['code_sha256'] != actual_code:
        raise ValueError('executed_code_map_changed')


def review(root, source_root, receipt_sha256):
    packet = json.loads((root/(BASE+'PHIUSIIL_C_ALLOCATION_ACCEPTANCE_PACKET.json')).read_bytes())
    specification = packet['exact_receipt_to_be_supplied']
    receipt_path = root/specification['path']
    receipt = _json(_read(receipt_path, receipt_sha256, 1_000_000))
    check_receipt(receipt, specification, code_hashes(root))
    if (root/'experiments/runs'/receipt['output_run_id']).exists():
        raise ValueError('allocation_output_namespace_already_exists')
    code_source = specification['code_sha256_source']
    if digest(root/code_source['path']) != code_source['file_sha256']:
        raise ValueError('preparation_checks_changed')
    bound = json.loads((root/code_source['path']).read_bytes())['code_sha256']
    if bound != receipt['code_sha256']:
        raise ValueError('receipt_code_map_not_bound_to_fourth_review_file')
    # Existing source verifier returns its report without writing any file.
    source_report = verify(root, source_root)
    return {'technical_review':'PASS','receipt_bytes_match_reviewer_supplied_digest':True,
        'exact_four_review_files_and_code':'PASS','source_comparison':source_report,
        'human_response_provenance_authenticated_by_script':False,
        'reviewer_obligation':'Personally authenticate response provenance, Vera confirmation where required, and trusted digest origin; structural PASS cannot establish these facts.',
        'files_written':0,'allocation_executed':False,'model_fits':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True, help='Actual receipt digest obtained through the reviewer trusted channel; never generated here')
    args = parser.parse_args()
    try:
        result = review(Path(__file__).resolve().parents[1], args.source_root, args.receipt_sha256)
    except (OSError, ValueError, KeyError, TypeError, InputContractError):
        print(json.dumps({'technical_review':'BLOCKED_OR_FAILED','reason':'Genuine receipt, supplied digest, exact packet inputs/code, source checks or unused output namespace unavailable/invalid','files_written':0,'allocation_executed':False,'model_fits':0}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

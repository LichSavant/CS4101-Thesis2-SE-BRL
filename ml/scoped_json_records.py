"""Opaque array framing and bounded selected-record reads; no partition guesses."""
import json
from pathlib import Path

from ml.experiment_inputs import InputContractError


def object_spans(path):
    """Offsets of top-level JSON-array objects, without decoding their contents."""
    offset=0;depth=0;quoted=False;escaped=False;start=None;opened=False;closed=False
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):
            for char in chunk:
                if quoted:
                    if escaped:escaped=False
                    elif char==92:escaped=True
                    elif char==34:quoted=False
                elif char==34:
                    if not depth:raise InputContractError('object_array_required')
                    quoted=True
                elif char==123:
                    if not opened or closed:raise InputContractError('object_array_required')
                    if depth==0:start=offset
                    depth+=1
                elif char==125:
                    depth-=1
                    if depth<0:raise InputContractError('invalid_object_framing')
                    if depth==0:yield start,offset-start+1
                elif depth==0:
                    if char==91 and not opened:opened=True
                    elif char==93 and opened and not closed:closed=True
                    elif char not in b' \r\n\t,':raise InputContractError('invalid_object_array_framing')
                offset+=1
    if not opened or not closed or depth or quoted:raise InputContractError('incomplete_object_array')


def selected_rows(path,index,ids):
    """Decode only requested IDs and reject redirected/incorrect byte locations."""
    with Path(path).open('rb') as stream:
        for oid in sorted(ids):
            offset,length=index[oid]
            if type(offset) is not int or type(length) is not int or offset<0 or not 0<length<1_000_000:
                raise InputContractError('invalid_selected_json_span')
            stream.seek(offset);body=stream.read(length)
            row=json.loads(body)
            if row.get('observation_id')!=oid:raise InputContractError('selected_json_identity_changed')
            yield row

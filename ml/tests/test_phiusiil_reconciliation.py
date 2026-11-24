"""Synthetic regression fixtures for the read-only historical adapter."""
import csv
import hashlib
import io

import pytest

from scripts.phiusiil_reconcile import canonical_fold, equivalent_cells, reconcile, selected_records


def test_selector_does_not_decode_reserved_rows_and_handles_quoted_records(tmp_path):
    path = tmp_path/'source.csv'
    path.write_bytes(b'a,b\r\n0,"multi\nline and ""quote"""\r\n\xff,reserved\r\n2,last')
    assert list(selected_records(path, {0,2})) == [(-1,['a','b']), (0,['0','multi\nline and "quote"']), (2,['2','last'])]


@pytest.mark.parametrize('value', ['0.0','6.0','1.5','1e0',' 1.0','NaN',''])
def test_fold_refuses_unsupplied_representations(value):
    with pytest.raises(ValueError, match='noncanonical'):
        canonical_fold(value)


def inputs(tmp_path):
    raw=tmp_path/'original.csv';clean=tmp_path/'clean.csv';manifest=tmp_path/'manifest.csv'
    text='Domain,label\n'+''.join(f'example-{i}.invalid,{i%2}\n' for i in range(10))
    raw.write_text(text,encoding='utf-8');clean.write_text(text,encoding='utf-8')
    output=io.StringIO(newline='')
    writer=csv.writer(output,lineterminator='\r\n')
    writer.writerow(['observation_id','source_dataset','target','group_id','partition','cv_fold'])
    for i in range(10):
        writer.writerow([f'PhiUSIIL::{i}','PhiUSIIL',str(1-i%2),f'g{i}','development',f'{i//2+1}.0'])
    manifest.write_bytes(output.getvalue().encode())
    expected={'original':hashlib.sha256(raw.read_bytes()).hexdigest(),
              'cleaned':hashlib.sha256(clean.read_bytes()).hexdigest(),
              'manifest':hashlib.sha256(manifest.read_bytes().replace(b'\r\n',b'\n')).hexdigest()}
    return raw,clean,manifest,expected


def test_reconciliation_preserves_inputs_and_never_claims_authentication(tmp_path):
    raw,clean,manifest,expected=inputs(tmp_path)
    before=[p.read_bytes() for p in (raw,clean,manifest)]
    out=tmp_path/'out'
    result=reconcile(raw,clean,manifest,out,expected)
    assert result['counts']=={'exact_cell_and_target_match':10}
    assert result['admission']=='BLOCKED' and result['fits']==0
    assert not result['independent_historical_lineage_authenticated']
    assert [p.read_bytes() for p in (raw,clean,manifest)]==before
    with (out/'development_assignments.normalized.csv').open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert {r['cv_fold'] for r in rows}=={'1','2','3','4','5'}
    with pytest.raises(FileExistsError):
        reconcile(raw,clean,manifest,out,expected)


def test_unmatched_cells_are_reported_without_coercion(tmp_path):
    raw,clean,manifest,expected=inputs(tmp_path)
    clean.write_bytes(clean.read_bytes().replace(b'example-0.invalid',b'changed.invalid'))
    expected['cleaned']=hashlib.sha256(clean.read_bytes()).hexdigest()
    result=reconcile(raw,clean,manifest,tmp_path/'out',expected)
    assert result['counts']['unresolved']==1 and result['counts']['cell_mismatch']==1
    assert result['counts']['exact_cell_and_target_match']==9


def test_wrong_source_hash_fails_before_output(tmp_path):
    raw,clean,manifest,expected=inputs(tmp_path)
    expected['original']='0'*64
    with pytest.raises(ValueError,match='source_hash_mismatch'):
        reconcile(raw,clean,manifest,tmp_path/'out',expected)
    assert not (tmp_path/'out').exists()


def test_numeric_representation_requires_exact_finite_equality_and_declared_type():
    assert equivalent_cells(['1.000'], ['1'], ['numeric'], {'numeric'})
    assert not equivalent_cells(['1.000'], ['1'], ['text'], {'numeric'})
    assert not equivalent_cells(['1.00000000000000001'], ['1'], ['numeric'], {'numeric'})
    assert not equivalent_cells(['NaN'], ['nan'], ['numeric'], {'numeric'})


def test_numeric_correspondence_is_distinct_from_exact_cells(tmp_path):
    raw,clean,manifest,expected=inputs(tmp_path)
    raw.write_bytes(raw.read_bytes().replace(b'invalid,0', b'invalid,0.0'))
    # Native labels are intentionally not coercible: this must remain unresolved.
    expected['original']=hashlib.sha256(raw.read_bytes()).hexdigest()
    result=reconcile(raw,clean,manifest,tmp_path/'out',expected,numeric_fields=())
    assert result['counts']['target_mismatch']==5
    assert result['counts']['unresolved']==5

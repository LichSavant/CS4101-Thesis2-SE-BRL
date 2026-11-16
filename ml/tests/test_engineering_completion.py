"""Synthetic mechanical contracts only; inert engines are not model evidence."""
from dataclasses import replace
import csv
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ml.experiment_inputs import InputContractError
from ml.metadata import canonical_json, fingerprint, freeze_json
from ml.research_protocol import audited_snapshots, verify_accepted_run, specification_record
from ml.tests.test_preparation_execution import packet
from ml.tests.test_research_protocol import fixture_packet
from ml.tests.test_source_controls import fixture
from ml.tests.test_experiment_engine import spec
from ml.source_controls import (prepare_source_controls, execute_source_controls,
    _execute_verified_controls, load_source_controls)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def phi_packet(root, change):
    from ml.research_protocol import prospective_id
    protocol, receipt, _, run_id, _ = packet(root)
    population = json.loads((protocol/'population.json').read_bytes())
    rows = json.loads((protocol.parent/'data/development/uci_records.json').read_bytes())
    assignments = list(csv.DictReader(io.StringIO((protocol/'assignments.csv').read_text())))
    mapping = {}
    for row in population['records']:
        old = row['observation_id']
        row.update(source_dataset='PhiUSIIL', source_file='fixture.csv', native_label=1-row['target'])
        row['observation_id'] = prospective_id(row['source_dataset'], row['snapshot_sha256'], row['source_file'], row['source_row_id'])
        mapping[old] = row['observation_id']
    for row in assignments:
        row.update(observation_id=mapping[row['observation_id']], source_dataset='PhiUSIIL')
    for row in rows:
        row.update(observation_id=mapping[row['observation_id']], source_dataset='PhiUSIIL', label=1-row['target'])
        del row['Result']
    if change.startswith('missing-'):
        role = change[8:]
        removed = {a['observation_id'] for a in assignments if a['partition'] == role}
        assignments = [a for a in assignments if a['observation_id'] not in removed]
        population['records'] = [r for r in population['records'] if r['observation_id'] not in removed]
    elif change.startswith('single-'):
        role = change[7:]
        ids = {a['observation_id'] for a in assignments if a['partition'] == role}
        for a in assignments:
            if a['observation_id'] in ids: a['target'] = '0'
        for r in population['records']:
            if r['observation_id'] in ids: r.update(target=0, native_label=1)
    elif change == 'crossing':
        assignments[-1]['group_id'] = assignments[0]['group_id']
    elif change == 'fold':
        assignments[0]['cv_fold'] = ''
    (protocol/'population.json').write_text(canonical_json(population))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=tuple(assignments[0]))
    writer.writeheader(); writer.writerows(assignments)
    (protocol/'assignments.csv').write_text(stream.getvalue(), newline='')
    dictionary = json.loads((protocol/'dictionary.json').read_bytes()); dictionary['dataset'] = 'PhiUSIIL'
    (protocol/'dictionary.json').write_text(canonical_json(dictionary))
    freeze = json.loads((protocol/'feature_freeze.json').read_bytes())
    freeze.update(assignment_sha256=sha(protocol/'assignments.csv'), dictionary_sha256=sha(protocol/'dictionary.json'))
    (protocol/'feature_freeze.json').write_text(canonical_json(freeze))
    data_name = 'data/development/phiusiil_records.json'
    (protocol.parent/data_name).write_text(canonical_json(rows))
    names = ['protocol/'+n for n in ('population.json','assignments.csv','dictionary.json','feature_freeze.json')] + [data_name]
    receipt.update(branch='PhiUSIIL', input_sha256={n:sha(protocol.parent/n) for n in names})
    (protocol/'feature_acceptance.json').write_text(canonical_json(receipt))
    return protocol, receipt, sha(protocol/'feature_acceptance.json'), run_id


@pytest.mark.parametrize('change', ['valid','missing-calibration','missing-test','single-calibration','single-test','crossing','fold'])
def test_phiusiil_stage_enforces_complete_metadata_before_export(tmp_path, change):
    from ml.preparation_execution import run_preparation
    protocol, receipt, digest, run_id = phi_packet(tmp_path, change)
    if change == 'valid':
        result = run_preparation(tmp_path, run_id, stage='D-features', expected_authorization_sha256=digest)
        assert result['model_fits'] == 0
    else:
        with pytest.raises(InputContractError):
            run_preparation(tmp_path, run_id, stage='D-features', expected_authorization_sha256=digest)
        assert not (protocol.parent.parent/receipt['output_run_id']).exists()


def test_audit_binding_preserves_source_file_pairs_and_order():
    entries = {'a.csv': {'source_dataset':'A','snapshot_sha256':'a'*64},
               'b.csv': {'source_dataset':'B','snapshot_sha256':'b'*64},
               'c.csv': {'source_dataset':'A','snapshot_sha256':'c'*64}}
    expected = {('A','a.csv'):'a'*64, ('B','b.csv'):'b'*64, ('A','c.csv'):'c'*64}
    assert audited_snapshots({'source_files': entries}) == expected
    assert audited_snapshots({'source_files': dict(reversed(list(entries.items())))}) == expected
    assert expected.get(('A','b.csv')) is None
    assert expected['A','a.csv'] != expected['B','b.csv']
    assert audited_snapshots({'dataset':'A','source_file':'a.csv','snapshot_sha256':'a'*64}) == {('A','a.csv'):'a'*64}


@pytest.mark.parametrize('field,value', [('dataset','different source'),('source_file','other.arff')])
def test_verifier_rejects_rehashed_wrong_audit_source_or_file(tmp_path, field, value):
    protocol, receipt, _, run_id, _, _ = fixture_packet(tmp_path)
    audit = json.loads((protocol/'source_audit.json').read_bytes()); audit[field] = value
    (protocol/'source_audit.json').write_text(canonical_json(audit))
    receipt['evidence_sha256']['source_audit.json'] = sha(protocol/'source_audit.json')
    for name in ('population.json','screening.json'):
        data = json.loads((protocol/name).read_bytes())
        data['source_audit_sha256'] = receipt['evidence_sha256']['source_audit.json']
        (protocol/name).write_text(canonical_json(data)); receipt['evidence_sha256'][name] = sha(protocol/name)
    (protocol/'acceptance.json').write_text(canonical_json(receipt))
    with pytest.raises(InputContractError, match='provenance_mismatch'):
        verify_accepted_run(tmp_path, run_id, expected_authorization_sha256=sha(protocol/'acceptance.json'))


@pytest.fixture(scope='module')
def verified_synthetic_context(tmp_path_factory):
    root = tmp_path_factory.mktemp('synthetic-authority')
    _, _, digest, run_id, _, _ = fixture_packet(root)
    return verify_accepted_run(root, run_id, expected_authorization_sha256=digest)[0]


def diagnostic_fixture(root, base):
    # Explicit synthetic test seam: derive inert contexts from a verified fixture.
    # These objects are never represented as genuine human research approval.
    original, normalized, sources = fixture()
    controls, receipt = prepare_source_controls(original, normalized, sources_by_id=sources, normalization_reference='synthetic:policy')
    specification = replace(spec(configs=('E1',)), protocol_reference='research:synthetic-contract-only')
    (root/'experiments/runs').mkdir(parents=True)
    contexts = {name:replace(base, authorization_sha256=fingerprint(name),
        input_fingerprint=receipt['input_fingerprints'][name],
        specification_fingerprint=fingerprint(specification_record(specification)),
        output_run_id='batch-'+name.replace('_','-'), branch='Email', sources_by_id=freeze_json(sources),
        _state={'boundary':'E-development-diagnostic-only','checkout_root':str(root.resolve())}) for name in controls}
    return controls, receipt, specification, contexts, root/'experiments/runs/batch'


@pytest.mark.parametrize('change', ['outside','traversal','run-id','scope','existing','child-existing','root','readback','redirect','redirect-resolution'])
def test_diagnostic_destinations_reject_before_engine_or_worker(tmp_path, verified_synthetic_context, monkeypatch, change):
    controls, receipt, specification, contexts, output = diagnostic_fixture(tmp_path, verified_synthetic_context)
    def forbidden(*a, **k): pytest.fail('Invalid destination reached worker')
    monkeypatch.setattr('subprocess.run', forbidden)
    if change == 'outside': output = tmp_path/'batch'
    elif change == 'traversal': output = output.parent/'x/../batch'
    elif change == 'run-id': contexts['baseline'] = replace(contexts['baseline'], output_run_id='other')
    elif change == 'scope': contexts['baseline']._state['boundary'] = 'E-development-fitting-only'
    elif change == 'existing': output.mkdir()
    elif change == 'child-existing': (output.parent/'batch-baseline').mkdir()
    elif change == 'root': contexts['baseline']._state['checkout_root'] = str(tmp_path/'other')
    elif change == 'readback': contexts['baseline']._state['readback_only'] = True
    elif change == 'redirect-resolution':
        original_resolve = Path.resolve
        monkeypatch.setattr(Path,'resolve',lambda p,*a,**k: tmp_path/'redirected' if p == output else original_resolve(p,*a,**k))
    else:
        target = tmp_path/'elsewhere'; target.mkdir()
        try: output.symlink_to(target, target_is_directory=True)
        except OSError: pytest.skip('Directory symlink permission unavailable')
    with pytest.raises(InputContractError):
        execute_source_controls(controls, receipt, specification=specification, contexts=contexts, output_directory=output)


def inert_bundle_seams(monkeypatch):
    calls = []
    monkeypatch.setattr('ml.experiment_engine.run_research_nested_cv', lambda *a, **k: ({}, ()))
    monkeypatch.setattr('ml.research_execution.research_summaries', lambda *a: {})
    def write(path, *a, **k):
        path.mkdir(); (path/'run_manifest.json').write_text('INERT CONTRACT FIXTURE; NOT MODEL STATE')
        return sha(path/'run_manifest.json')
    def load(path, *, expected_manifest_sha256, **k):
        assert sha(path/'run_manifest.json') == expected_manifest_sha256
        calls.append(path)
        return {}, ()
    monkeypatch.setattr('ml.experiment_artifacts.write_nested_bundle', write)
    monkeypatch.setattr('ml.experiment_artifacts.load_nested_bundle', load)
    return calls


@pytest.mark.parametrize('change', ['valid','missing','corrupt','mismatch','extra','reload-fails'])
def test_inert_diagnostic_completion_and_readback(tmp_path, verified_synthetic_context, monkeypatch, change):
    controls, receipt, specification, contexts, output = diagnostic_fixture(tmp_path, verified_synthetic_context)
    calls = inert_bundle_seams(monkeypatch)
    if change == 'reload-fails':
        def fail(*a, **k): raise InputContractError('inert reload failure')
        monkeypatch.setattr('ml.experiment_artifacts.load_nested_bundle', fail)
        with pytest.raises(InputContractError):
            _execute_verified_controls(controls, receipt, specification=specification, contexts=contexts, output_directory=output)
        assert not (output/'diagnostic_completion.json').exists()
        return
    _execute_verified_controls(controls, receipt, specification=specification, contexts=contexts, output_directory=output)
    assert len(calls) == 3
    marker = output/'diagnostic_completion.json'; digest = sha(marker)
    child = output.parent/'batch-baseline/run_manifest.json'
    if change == 'missing': child.unlink()
    elif change == 'corrupt': child.write_text('corrupt')
    elif change == 'mismatch': contexts['baseline'] = replace(contexts['baseline'], input_fingerprint='f'*64)
    elif change == 'extra': (output/'unexpected.txt').write_text('extra')
    if change == 'valid':
        for c in contexts.values(): c._state['readback_only'] = True
        assert load_source_controls(output, contexts=contexts, expected_sha256=digest)['controls']
        assert len(calls) == 6
    else:
        with pytest.raises((InputContractError, OSError, AssertionError)):
            load_source_controls(output, contexts=contexts, expected_sha256=digest)


@pytest.mark.parametrize('change', ['timeout','busy','failure','malformed'])
def test_bounded_diagnostic_worker_uses_inert_process(tmp_path, verified_synthetic_context, monkeypatch, change):
    import subprocess
    controls, receipt, specification, contexts, output = diagnostic_fixture(tmp_path, verified_synthetic_context)
    lock = output.parent/'batch.diagnostic-worker.lock'
    if change == 'busy': lock.write_text('another invocation')
    def process(*args, **kwargs):
        assert kwargs['timeout'] == min(c.budget['max_seconds'] for c in contexts.values())
        assert lock.exists() and kwargs['creationflags'] == getattr(subprocess,'CREATE_NO_WINDOW',0)
        if change == 'timeout': raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])
        return SimpleNamespace(returncode=1 if change == 'failure' else 0, stdout='invalid')
    monkeypatch.setattr(subprocess, 'run', process)
    with pytest.raises(InputContractError):
        execute_source_controls(controls, receipt, specification=specification, contexts=contexts, output_directory=output)
    assert lock.exists() == (change == 'busy')
    assert not output.exists()


def test_bounded_parent_reloads_successful_inert_worker(tmp_path, verified_synthetic_context, monkeypatch):
    import subprocess
    controls, receipt, specification, contexts, output = diagnostic_fixture(tmp_path, verified_synthetic_context)
    calls = inert_bundle_seams(monkeypatch)
    def process(*args, **kwargs):
        request = json.loads(kwargs['input'])
        assert request['root'] == str(tmp_path.resolve())
        _execute_verified_controls(controls, receipt, specification=specification, contexts=contexts, output_directory=output)
        return SimpleNamespace(returncode=0,stdout=json.dumps({'completion_sha256':sha(output/'diagnostic_completion.json')}))
    monkeypatch.setattr(subprocess,'run',process)
    assert execute_source_controls(controls,receipt,specification=specification,contexts=contexts,output_directory=output)['controls']
    assert len(calls) == 6
    assert not (output.parent/'batch.diagnostic-worker.lock').exists()


def test_fresh_diagnostic_readback_verifies_scope_without_fitting(tmp_path):
    """Real verifier on a synthetic Email dossier; no bundle fitting/loading."""
    import shutil
    from ml.branch_preparation import export_selected_handoff
    from ml.development_experiments import behavioral_columns, METADATA
    from ml.research_protocol import prospective_id
    protocol, receipt, _, _, dataset, experiment = fixture_packet(tmp_path)
    population = json.loads((protocol/'population.json').read_bytes())
    assignments = list(csv.DictReader(io.StringIO((protocol/'assignments.csv').read_text())))
    old = {r['observation_id']:dict(r) for r in population['records']}
    for row in population['records']:
        row.update(source_dataset='Nazario' if row['target'] else 'Enron', source_file='fixture.csv', native_label=row['target'])
        row['observation_id'] = prospective_id(row['source_dataset'], row['snapshot_sha256'], row['source_file'], row['source_row_id'])
    mapped = {oid:r for oid,r in zip(old, population['records'])}
    for row in assignments:
        p = mapped[row['observation_id']]
        row.update(observation_id=p['observation_id'], source_dataset=p['source_dataset'])
    run_id = 'synthetic-diagnostic-input'
    output_id = 'synthetic-diagnostic-output'
    new_root = protocol.parent.parent/run_id
    main, vectors = [], []
    for row in dataset.observations:
        p = mapped[row.observation_id]
        meta = dict(observation_id=p['observation_id'],target=row.target,group_id=row.group_id,partition='development',cv_fold=row.fold)
        main.append(dict(meta,source_dataset=p['source_dataset'],source_row_id=p['source_row_id'],label=row.target,
            subject='Synthetic subject',body='Synthetic body', URL_Length=row.conventional[0], Redirect=row.conventional[1]))
        vectors.append({**meta, **dict.fromkeys(behavioral_columns(),0)})
    export_selected_handoff(new_root, ('Email',), {'Email':main}, {'Email':vectors})
    new_protocol = new_root/'protocol'; shutil.copytree(protocol,new_protocol)
    def write(name,value): (new_protocol/name).write_text(canonical_json(value))
    audit = {'category':'ACTUAL SOURCE AUDIT; NOT A MODEL RESULT','model_fits':0,'source_records':len(assignments),
        'source_files':{s:{'dataset':s,'source_file':'fixture.csv','snapshot_sha256':'e'*64} for s in ('Nazario','Enron')}}
    # Multi-file keys are exact filenames; two sources may share a filename only
    # when entries explicitly name it, rather than guessing from a source key.
    audit['source_files'] = {s+'.csv':{**v,'source_file':s+'.csv'} for s,v in audit['source_files'].items()}
    for p in population['records']: p['source_file'] = p['source_dataset']+'.csv'
    # Recompute IDs after the explicit file names change, preserving positions.
    mapping = {}
    for p in population['records']:
        before = p['observation_id']; p['observation_id'] = prospective_id(p['source_dataset'],p['snapshot_sha256'],p['source_file'],p['source_row_id']); mapping[before]=p['observation_id']
    for rows in (main,vectors,assignments):
        for row in rows: row['observation_id'] = mapping[row['observation_id']]
    # The first export was a distinct fixture staging namespace; final delivery
    # is a fresh exclusive namespace, never a rewrite of existing handoff output.
    final_id = 'synthetic-diagnostic-final-input'
    final_root = protocol.parent.parent/final_id
    export_selected_handoff(final_root, ('Email',), {'Email':main}, {'Email':vectors})
    final_protocol = final_root/'protocol'; shutil.copytree(new_protocol,final_protocol); new_protocol=final_protocol; new_root=final_root;run_id=final_id
    write('source_audit.json',audit)
    population.update(branch='Email',source_audit_sha256=sha(new_protocol/'source_audit.json'),source_label_mappings=[
        dict(source_dataset=s,native=t,target=t,meaning='phishing' if t else 'ham',primary_source_reference='synthetic:meaning') for s,t in (('Nazario',1),('Enron',0))])
    write('population.json',population)
    write('screening.json',dict(source_audit_sha256=sha(new_protocol/'source_audit.json'),eligible_population_fingerprint=fingerprint(population['records']),excluded_by_primary_reason={}))
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=tuple(assignments[0]));writer.writeheader();writer.writerows(assignments)
    (new_protocol/'assignments.csv').write_text(stream.getvalue(),newline='')
    dictionary=json.loads((new_protocol/'dictionary.json').read_bytes());dictionary['dataset']='Email';write('dictionary.json',dictionary)
    freeze=json.loads((new_protocol/'feature_freeze.json').read_bytes());freeze.update(assignment_sha256=sha(new_protocol/'assignments.csv'),dictionary_sha256=sha(new_protocol/'dictionary.json'));write('feature_freeze.json',freeze)
    settings=replace(experiment,configurations=('E1',));write('experiment.json',specification_record(settings))
    selection=json.loads((new_protocol/'selection.json').read_bytes());selection['policy']['configuration']='E1';write('selection.json',selection)
    from ml.development_experiments import DevelopmentSpecification,load_development_dataset
    from ml.development_runner import dataset_fingerprint
    loaded=load_development_dataset(tmp_path,run_id,specification=replace(dataset.specification,dataset='Email'))
    receipt.update(boundary='E-development-diagnostic-only',branch='Email',input_run_id=run_id,output_run_id=output_id,input_fingerprint=dataset_fingerprint(loaded))
    for name in receipt['evidence_sha256']:
        path=new_root/'data/processed/features/development'/name if name=='development_input_manifest.json' else new_protocol/name
        receipt['evidence_sha256'][name]=sha(path)
    write('acceptance.json',receipt);digest=sha(new_protocol/'acceptance.json')
    context,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=digest,purpose='diagnostic')
    assert context._state['boundary']=='E-development-diagnostic-only'
    with pytest.raises(InputContractError): verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=digest)
    destination=protocol.parent.parent/output_id;destination.mkdir();(destination/'run_manifest.json').write_text('INERT existence marker; no model')
    readback,_,_=verify_accepted_run(tmp_path,run_id,expected_authorization_sha256=digest,purpose='diagnostic-readback')
    assert readback._state['readback_only']
    with pytest.raises(InputContractError,match='single_use'):readback.bind(loaded,settings)

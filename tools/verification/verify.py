"""Portable no-fit verification. All generated files stay in a new external workspace."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import zipfile
from email.parser import BytesParser

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)


def pins():
    return dict(line.strip().split('==') for line in (HERE / 'requirements.txt').read_text().splitlines()
                if line.strip() and not line.startswith('#'))


def clean_environment(workspace):
    env = dict(os.environ)
    for name in list(env):
        if name.startswith(('PYTHON', 'SEBRL_', 'ARTIFACT_', 'PIP_')) or name in {'VIRTUAL_ENV', 'DATABASE_URL'}:
            env.pop(name, None)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', DATABASE_URL='sqlite:///:memory:',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               TEMP=str(workspace), TMP=str(workspace), TMPDIR=str(workspace),
               PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_CACHE_DIR='1')
    return env


def command(workspace, label, argv, *, cwd, env, timeout=300):
    write(workspace / (label + '-command.json'), {'argv': list(map(str, argv)), 'cwd': str(cwd),
                                                'timeout_seconds': timeout})
    with (workspace / (label + '.txt')).open('x', encoding='utf-8') as log:
        try:
            result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    write(workspace / (label + '-result.json'), {'exit_code': code})
    print(label, 'exit', code, flush=True)
    if code:
        raise RuntimeError(label + ' failed; inspect external log')


def python_path(workspace):
    return workspace / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def setup(workspace, *, allow_download, wheelhouse):
    if sys.version_info[:2] != (3, 12):
        raise ValueError('Python 3.12 required; no dependency substitution permitted')
    if workspace == ROOT or workspace.is_relative_to(ROOT) or ROOT.is_relative_to(workspace):
        raise ValueError('Workspace must be separate from repository')
    if not allow_download and wheelhouse is None:
        raise ValueError('Offline wheelhouse required; no implicit network fallback')
    workspace.mkdir()  # Exclusive: never reuse/overwrite another verification.
    env = clean_environment(workspace)
    venv.EnvBuilder(with_pip=True).create(workspace / 'venv')
    python = python_path(workspace)
    wheels = workspace / 'wheels'
    if wheelhouse:
        shutil.copytree(wheelhouse, wheels)
    else:
        wheels.mkdir()
        command(workspace, 'download', [python, '-B', '-m', 'pip', '--isolated', 'download',
                '--index-url', 'https://pypi.org/simple', '--only-binary=:all:', '--no-deps',
                '--dest', wheels, '-r', HERE / 'requirements.txt'], cwd=workspace, env=env, timeout=600)
    expected = {n.lower().replace('_', '-'): v for n, v in pins().items()}
    observed = {}
    hashes = {}
    known_hashes = json.loads((HERE / 'known-wheel-hashes.json').read_text())
    for wheel in wheels.iterdir():
        if wheel.suffix != '.whl':
            raise ValueError('Wheelhouse must contain wheel files only')
        with zipfile.ZipFile(wheel) as archive:
            metadata = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
            if len(metadata) != 1:
                raise ValueError('Invalid wheel metadata')
            item = BytesParser().parsebytes(archive.read(metadata[0]))
        name = item['Name'].lower().replace('_', '-')
        if name in observed or expected.get(name) != item['Version']:
            raise ValueError('Unexpected or duplicate wheel/version')
        observed[name] = item['Version']
        hashes[name] = {'filename': wheel.name, 'sha256': digest(wheel)}
        if name in known_hashes and hashes[name]['sha256'] != known_hashes[name]:
            raise ValueError('Wheel differs from retained verified dependency hash')
    if observed != expected:
        raise ValueError('Incomplete wheelhouse; network fallback disabled')
    lock = workspace / 'requirements-hashed.txt'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(f'{n}=={v} --hash=sha256:{hashes[n]["sha256"]}' for n, v in sorted(expected.items())) + '\n')
    write(workspace / 'wheel-integrity.json', hashes)
    command(workspace, 'install', [python, '-B', '-m', 'pip', '--isolated', 'install', '--no-index',
            '--find-links', wheels, '--only-binary=:all:', '--no-deps', '--require-hashes',
            '--report', workspace / 'installation.json', '-r', lock], cwd=workspace, env=env)
    command(workspace, 'dependency-check', [python, '-B', '-m', 'pip', '--isolated', 'check'], cwd=workspace, env=env)
    write(workspace / 'setup.json', {'python': sys.version, 'requirements_sha256': digest(HERE / 'requirements.txt'),
                                    'pins': expected, 'network_download_authorized': allow_download})


def run(workspace, *, readback_root, receipt_sha256, frontend):
    if (workspace / 'run.json').exists() or (workspace / 'source').exists():
        raise ValueError('Run requires unused prepared workspace')
    setup_record = json.loads((workspace / 'setup.json').read_text())
    if setup_record['requirements_sha256'] != digest(HERE / 'requirements.txt'):
        raise ValueError('Setup requirements changed')
    source = workspace / 'source'
    source.mkdir()
    # Explicit software trees only. No datasets, research runs, .env, Git or venv.
    excluded = shutil.ignore_patterns('node_modules', 'dist', '__pycache__', '*.pyc', '*.tsbuildinfo', '.env', '.env.*')
    for name in ('ml', 'backend', 'apps', 'packages', 'tools'):
        shutil.copytree(ROOT / name, source / name, ignore=excluded)
    for name in ('package.json', 'package-lock.json', 'tsconfig.base.json', 'AGENTS.md'):
        if (ROOT / name).is_file():
            shutil.copy2(ROOT / name, source / name)
    destination = source / 'experiments/notebooks'
    destination.mkdir(parents=True)
    # Reviewed aggregation source and the source-only development companion.
    for name in ('04_feature_extraction.ipynb', '05_development_preparation.ipynb'):
        notebook = ROOT / 'experiments/notebooks' / name
        document = json.loads(notebook.read_text(encoding='utf-8'))
        for cell in document['cells']:
            if cell['cell_type'] == 'code':
                cell['outputs'] = []
                cell['execution_count'] = None
        write(destination / name, document)
    env = clean_environment(workspace)
    python = python_path(workspace)
    if (readback_root is None) != (receipt_sha256 is None):
        raise ValueError('Readback requires both named synthetic root and independent digest')
    if readback_root:
        receipt = readback_root / 'fixture_receipt.json'
        if digest(receipt) != receipt_sha256:
            raise ValueError('Synthetic receipt digest mismatch')
        metadata = json.loads(receipt.read_text())
        if metadata['category'] != 'SYNTHETIC RESULT' or set(metadata['bundles']) != {'Email', 'Web', 'UCI', 'PhiUSIIL'}:
            raise ValueError('Only exact synthetic fixture family readback permitted')
        target = workspace / 'synthetic-readback'
        target.mkdir()
        shutil.copy2(receipt, target / receipt.name)
        for name in ('email', 'web', 'uci', 'phiusiil'):
            shutil.copytree(readback_root / name, target / name)
        env.update(SEBRL_READBACK_ROOT=str(target), SEBRL_READBACK_RECEIPT_SHA256=receipt_sha256)
    # Strict version/import check runs inside the new interpreter, with no inherited paths.
    check = "import importlib.metadata as m,json,sys; p=json.load(open(sys.argv[1]))['pins']; assert all(m.version(n)==v for n,v in p.items()); import sklearn,xgboost,skops,datasketch,fastapi,pytest; print(json.dumps({n:m.version(n) for n in p},indent=2))"
    command(workspace, 'imports-versions', [python, '-B', '-c', check, workspace / 'setup.json'], cwd=source, env=env)
    for directory in ('ml', 'backend', 'tools'):
        for path in (source / directory).rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    selection = json.loads((HERE / 'selection.json').read_text())
    tests = list(selection['tests'])
    tests.append('tools/verification/test_portability.py')
    argv = [python, '-B', '-m', 'pytest', '-p', 'ml.tests.no_fit_guard', *tests]
    for node in selection['deselected']:
        argv.extend(['--deselect', node])
    argv.extend(['-q', '-ra', '-p', 'no:cacheprovider', '--basetemp', workspace / 'pytest'])
    command(workspace, 'python-tests', argv, cwd=source, env=env)
    if frontend:
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        if not npm:
            raise ValueError('npm unavailable')
        # Cache is only an offline download source; installs/build outputs are isolated.
        command(workspace, 'npm-install', [npm, 'ci', '--offline', '--ignore-scripts', '--no-audit', '--no-fund',
                '--logs-dir', workspace / 'npm-logs'], cwd=source, env=env)
        for label, script in [('frontend-tests', 'test'), ('typecheck', 'typecheck'), ('lint', 'lint'), ('build', 'build')]:
            command(workspace, label, [npm, 'run', script], cwd=source, env=env)
    write(workspace / 'run.json', {'status': 'PASS', 'source': str(source), 'readback_supplied': bool(readback_root),
                                  'frontend_verified': frontend, 'fitting_authorized': False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'run'])
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--allow-download', action='store_true')
    parser.add_argument('--wheelhouse', type=Path)
    parser.add_argument('--readback-root', type=Path)
    parser.add_argument('--receipt-sha256')
    parser.add_argument('--frontend', action='store_true')
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if workspace == ROOT or workspace.is_relative_to(ROOT) or ROOT.is_relative_to(workspace):
        parser.error('Workspace must be outside repository')
    try:
        if args.action == 'setup':
            setup(workspace, allow_download=args.allow_download, wheelhouse=args.wheelhouse)
        else:
            run(workspace, readback_root=args.readback_root, receipt_sha256=args.receipt_sha256, frontend=args.frontend)
    except (ValueError, RuntimeError, OSError) as error:
        print('BLOCKED_OR_FAILED:', str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

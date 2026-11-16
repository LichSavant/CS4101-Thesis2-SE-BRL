"""No-fit regressions for verifier isolation and fail-closed setup."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('portable_verifier', Path(__file__).with_name('verify.py'))
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_default_offline_setup_never_creates_environment(tmp_path):
    destination = tmp_path / 'unused'
    with pytest.raises(ValueError, match='Offline wheelhouse required'):
        verifier.setup(destination, allow_download=False, wheelhouse=None)
    assert not destination.exists()


def test_setup_cannot_target_application_checkout():
    with pytest.raises(ValueError, match='separate from repository'):
        verifier.setup(verifier.ROOT / 'forbidden', allow_download=True, wheelhouse=None)


def test_inherited_machine_paths_models_and_database_are_not_consumed(tmp_path, monkeypatch):
    for key in ['PYTHONPATH', 'PYTHONHOME', 'SEBRL_READBACK_ROOT', 'ARTIFACT_EMAIL_BUNDLE', 'VIRTUAL_ENV']:
        monkeypatch.setenv(key, 'DO_NOT_CONSUME')
    monkeypatch.setenv('DATABASE_URL', 'DO_NOT_OPEN')
    env = verifier.clean_environment(tmp_path)
    assert all('DO_NOT' not in value for value in env.values())
    assert env['DATABASE_URL'] == 'sqlite:///:memory:'
    assert env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
    assert env['PYTHONDONTWRITEBYTECODE'] == '1'

"""Synthetic identifier rejection only; no excluded dataset files or records."""
import pytest

from ml.experiment_inputs import DatasetIdentity, InputContractError, reject_excluded_source_identifiers
from ml.research_protocol import prospective_id
from ml.source_acquisition import acquire_zenodo


@pytest.mark.parametrize('identifier', ['SpaPhish', 'SpaFish', 'SPA-PHISH', 'spa_fish',
                                       'ＳｐａＰｈｉｓｈ', 'snapshot/SpaFish.csv'])
def test_excluded_alias_metadata_rejected_before_identity(identifier):
    with pytest.raises(InputContractError, match='^excluded_source_identifier$'):
        reject_excluded_source_identifiers(identifier)
    with pytest.raises(InputContractError, match='^excluded_source_identifier$'):
        DatasetIdentity(identifier, 'synthetic-v1', 'synthetic:provenance')
    with pytest.raises(InputContractError, match='^excluded_source_identifier$'):
        prospective_id('synthetic-source', 'a' * 64, identifier, 0)


def test_excluded_filename_rejected_before_metadata_file_io_or_network(tmp_path):
    # The path intentionally does not exist: rejection must precede reading it.
    with pytest.raises(InputContractError, match='^excluded_source_identifier$'):
        acquire_zenodo(tmp_path / 'nonexistent.json', expected_record_sha256='a' * 64,
                       record_id=8041387, filenames=('SpaFish.csv',), directory=tmp_path / 'unused',
                       max_total_bytes=1000, max_elapsed_seconds=1, authorization_reference='synthetic:access',
                       opener=lambda *_a, **_k: pytest.fail('Network must not run'))
    assert not (tmp_path / 'unused').exists()


def test_source_denial_does_not_reject_generic_phishing_research_names():
    reject_excluded_source_identifiers('synthetic phishing example', 'SpamAssassin', 'source.csv')

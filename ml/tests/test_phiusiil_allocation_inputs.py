"""Synthetic edge tests; never allocate research records or fit estimators."""
import pytest

from scripts.prepare_phiusiil_allocation_inputs import relationships


def test_domain_and_exact_url_components_preserve_mixed_groups():
    edges, report = relationships([
        ('a',' Example.invalid ','https://example.invalid/one',0,'historical-a'),
        ('b','example.invalid','https://example.invalid/two',1,'historical-a'),
        ('c','other.invalid','https://example.invalid/two',1,'historical-b'),
        ('d','unique.invalid','https://unique.invalid/',0,'historical-c'),
    ], 'synthetic accepted policy')
    assert report['observations']==4 and report['components']==2
    assert report['edge_counts']=={'domain':1,'exact_duplicate':1}
    assert report['mixed_native_label_components']==1
    assert report['components_merging_historical_groups']==1
    assert report['historical_groups_split']==0
    assert all(set(edge)=={'left','right','kind','evidence_reference'} for edge in edges)
    assert all('https://' not in str(edge) for edge in edges)


def test_wrong_domain_relationship_cannot_silently_split_historical_group():
    with pytest.raises(ValueError,match='historical_group_would_be_split'):
        relationships([('a','one.invalid','https://one.invalid/',0,'same'),
                       ('b','two.invalid','https://two.invalid/',1,'same')], 'synthetic policy')


def test_duplicate_ids_and_missing_source_keys_are_not_manufactured():
    with pytest.raises(ValueError,match='duplicate_id_or_missing'):
        relationships([('a','','https://one.invalid/',0,'same')], 'synthetic policy')
    with pytest.raises(ValueError,match='duplicate_id_or_missing'):
        relationships([('a','one.invalid','https://one.invalid/',0,'same'),
                       ('a','one.invalid','https://one.invalid/',0,'same')], 'synthetic policy')

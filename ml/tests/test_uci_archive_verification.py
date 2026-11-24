"""Generated release headers; no research-row or network access."""
import io
import pytest

from ml.uci_archive_verification import read_header_only, compare_header
from ml.tests.test_uci_reconstruction import payload


def test_header_reader_never_requests_data_region_bytes():
    header = payload().split(b"@data\n")[0] + b"@data\n"
    class BoundaryStream(io.BytesIO):
        def read(self, size=-1):
            assert size == 1 and self.tell() < len(header)
            return super().read(size)
    result = read_header_only(BoundaryStream(header + b"DO_NOT_READ_RESEARCH_ROWS"))
    assert result == header
    assert compare_header(result)["ordered_predictors"] == 30
    assert not compare_header(result)["native_result_meanings_established"]


@pytest.mark.parametrize("header", [b"@relation test\n", b"@relation test\n" * 2000])
def test_missing_boundary_or_overbudget_header_rejected(header):
    with pytest.raises(ValueError, match="bounded_arff_header"):
        read_header_only(io.BytesIO(header), max_bytes=100)


def test_source_domain_disagreement_does_not_get_normalized():
    header = read_header_only(io.BytesIO(payload()))
    with pytest.raises(ValueError, match="release_dictionary"):
        compare_header(header.replace(b"Redirect {0,1}", b"Redirect {-1,0,1}"))

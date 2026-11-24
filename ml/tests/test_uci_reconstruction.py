"""Generated native-code ARFF bytes; no research payloads or fitting."""
import hashlib
import io
from copy import deepcopy
import pytest

from ml.experiment_inputs import InputContractError
from ml.uci_schema import NATIVE_DOMAINS
from ml.uci_reconstruction import reconstruct_candidate
import ml.uci_snapshot as acquisition


def payload():
    vector = [min(domain) for domain in NATIVE_DOMAINS.values()]
    alternate = [max(domain) for domain in NATIVE_DOMAINS.values()]
    lines = ["@relation synthetic"]
    lines += ["@attribute " + name + " {" + ",".join(map(str, sorted(domain))) + "}"
              for name, domain in NATIVE_DOMAINS.items()]
    lines += ["@attribute Result {-1,1}", "@data", "% synthetic records"]
    lines += [",".join(map(str, values)) for values in
              [vector + [-1], vector + [-1], vector + [1], alternate + [1]]]
    return ("\n".join(lines) + "\n").encode()


def run(data, **changes):
    settings = dict(expected_sha256=hashlib.sha256(data).hexdigest(), original_count=4, retained_count=3)
    settings.update(changes)
    return reconstruct_candidate(data, **settings)


def test_pipeline_binds_prefilter_ids_and_preserves_conflicting_records():
    data = payload(); before = deepcopy(data)
    first = run(data)
    assert first == run(data) and data == before
    assert first["validation"]["removed_complete_duplicates"] == 1
    assert first["validation"]["mixed_native_label_groups"] == 1
    assert [row["source_row_id"] for row in first["retained_records"]] == [0, 2, 3]
    assert list(first["retained_records"][0]["features"]) == list(NATIVE_DOMAINS)
    assert all("Result" not in row["features"] and "target" not in row for row in first["retained_records"])
    assert not first["protocol_approved"] and not first["partitions_generated"]
    assert not first["target_labels_constructed"] and not first["validation"]["scientific_admission"]


@pytest.mark.parametrize("change", ["digest", "order", "extra", "domain", "code", "missing", "encoding", "count", "retained"])
def test_invalid_source_aborts_without_partial_output(change):
    data = payload(); settings = {}
    if change == "digest": settings["expected_sha256"] = "0" * 64
    elif change == "order": data = data.replace(b"@attribute URL_Length", b"@attribute url_length")
    elif change == "extra": data = data.replace(b"@data", b"@attribute unexpected {-1,1}\n@data")
    elif change == "domain": data = data.replace(b"@attribute Redirect {0,1}", b"@attribute Redirect {-1,0,1}")
    elif change == "code": data = data + b"0,1\n"
    elif change == "missing": data = data.replace(b"@data", b"@data\n?\n")
    elif change == "encoding": data += b"\xff"
    elif change == "count": settings["original_count"] = 5
    else: settings["retained_count"] = 4
    with pytest.raises(InputContractError): run(data, **settings)


@pytest.mark.parametrize("original,retained", [(True, 1), (4, True), (0, 0), (4, 5), (-1, 1)])
def test_invalid_processing_scope_rejected_before_payload_decode(original, retained):
    with pytest.raises(InputContractError, match="explicit_positive_uci_processing_scope_required"):
        reconstruct_candidate(b"not even ARFF", expected_sha256="0" * 64,
                              original_count=original, retained_count=retained)


def test_record_budget_stops_before_interpreting_an_extra_record():
    data = payload() + b"unpermitted extra record; must not be interpreted\n"
    with pytest.raises(InputContractError, match="uci_original_record_scope_exceeded"):
        run(data)


class Response(io.BytesIO):
    def geturl(self):
        return acquisition.URL


def test_opaque_acquisition_freezes_exact_bytes_and_refuses_reuse(tmp_path, monkeypatch):
    data = b"synthetic opaque archive; intentionally not a ZIP"
    monkeypatch.setattr(acquisition, "EXPECTED_SHA256", hashlib.sha256(data).hexdigest())
    result = acquisition.acquire_archive(tmp_path / "source", authorization_reference="synthetic:opaque-only",
                                         opener=lambda *a, **kw: Response(data))
    assert (tmp_path / "source/phishing-websites.zip").read_bytes() == data
    assert result["source_records_parsed"] == 0 and not result["archive_extracted"]
    assert not result["scientific_admission"]
    with pytest.raises(FileExistsError):
        acquisition.acquire_archive(tmp_path / "source", authorization_reference="synthetic:opaque-only")


@pytest.mark.parametrize("failure", ["digest", "size", "host"])
def test_failed_acquisition_rolls_back_only_new_output(tmp_path, failure):
    data = b"x" * (2_000_001 if failure == "size" else 10)
    class ChangedResponse(Response):
        def geturl(self):
            return "https://example.com/mirror.zip" if failure == "host" else acquisition.URL
    with pytest.raises(ValueError):
        acquisition.acquire_archive(tmp_path / "source", authorization_reference="synthetic:opaque-only",
                                     opener=lambda *a, **kw: ChangedResponse(data))
    assert not (tmp_path / "source").exists()

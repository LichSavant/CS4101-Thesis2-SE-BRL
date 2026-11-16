"""Complete synthetic demonstration, including fixed artifact replay."""
from ml.synthetic_demo import demonstrate
from ml.development_runner import verify_synthetic_bundle


def test_synthetic_demo_has_no_research_models_and_replayable_bundle(tmp_path):
    summary = demonstrate(tmp_path / "demo", code_reference="synthetic-test-code")
    assert summary["result_category"] == "SYNTHETIC RESULT"
    assert summary["oof_rows"] == 30 and summary["dimension_ablation_checks"] == 4
    assert summary["actual_research_models_fitted"] == 0 and summary["synthetic_stub_fit_calls"] == 40
    manifest = verify_synthetic_bundle(tmp_path / "demo")
    assert manifest["technical_u1_smoke"]["configurations"] == ["U1"]
    assert manifest["research_execution"] == "BLOCKED"


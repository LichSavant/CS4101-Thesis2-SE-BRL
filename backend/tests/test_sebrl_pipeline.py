"""The offline analytical branch reuses the unchanged, content-free API boundary."""

from backend.app.sebrl_adapter import to_sebrl_api_response
from ml.pipeline import PretrainingPipeline


def test_pipeline_envelope_remains_compatible_with_backend_contract():
    result = PretrainingPipeline().run({"kind": "email", "subject": "Submit your password immediately."})
    response = to_sebrl_api_response(result.envelope)
    assert response.overall_status == "not_evaluated"
    assert response.assessment_result.availability_mask == (1, 1, 0, 1)
    assert response.assessment_result.dimension_results[-1].evidence_state == "supported"
    assert "password" not in response.model_dump_json()
    assert all(c.status == "not_evaluated" for c in response.components[1:])

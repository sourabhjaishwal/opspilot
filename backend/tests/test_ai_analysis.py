from unittest.mock import MagicMock, patch
import pytest

from app.config import Settings
from app.schemas.ai import AIIncidentAnalysis
from app.schemas.service import ServiceCreate
from app.services.ai_service import build_incident_prompt
from app.services.service_service import create_service


@pytest.fixture()
def sample_incident(client, db):
    service = create_service(db, ServiceCreate(name="checkout-service", description="Handles checkout"))
    resp = client.post(
        "/incidents",
        json={
            "service_id": service.id,
            "severity": "critical",
            "title": "Checkout latency spiked",
            "description": "Database pool exhausted on checkout-service.",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_prompt_builder_contains_all_incident_fields():
    prompt = build_incident_prompt(
        service_name="payment-service",
        service_status="degraded",
        severity="high",
        title="Payment gateway timeout",
        description="Gateway times out after 30s.",
    )
    assert "payment-service" in prompt
    assert "degraded" in prompt
    assert "high" in prompt
    assert "Payment gateway timeout" in prompt
    assert "Gateway times out after 30s" in prompt
    assert "AI-generated recommendation" in prompt


def test_analyze_endpoint_requires_authentication(client, sample_incident):
    from app.main import app
    from app.routes.deps import get_current_user

    app.dependency_overrides.pop(get_current_user, None)
    response = client.post(f"/incidents/{sample_incident['id']}/analyze")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_analyze_nonexistent_incident_returns_404(client):
    response = client.post("/incidents/99999/analyze")
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_analyze_incident_missing_api_key_returns_503(client, sample_incident):
    with patch("app.services.ai_service.get_settings") as mock_settings:
        mock_settings.return_value = Settings(gemini_api_key=None)
        response = client.post(f"/incidents/{sample_incident['id']}/analyze")
        assert response.status_code == 503
        assert "Gemini API key is not configured" in response.json()["detail"]


def test_analyze_incident_success_with_mocked_gemini(client, sample_incident):
    mock_analysis = AIIncidentAnalysis(
        summary="Database pool exhaustion in checkout service (AI advisory).",
        possible_root_cause="Connection leak saturating connection pool.",
        recommended_checks=["Inspect active DB connections", "Check slow query logs"],
        suggested_resolution="Increase pool size and fix connection handles.",
    )

    with patch("app.services.ai_service.get_settings") as mock_settings, \
         patch("app.services.ai_service.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="test-key", gemini_model="gemini-3.6-flash")
        mock_response = MagicMock()
        mock_response.parsed = mock_analysis
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        response = client.post(f"/incidents/{sample_incident['id']}/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == mock_analysis.summary
        assert data["possible_root_cause"] == mock_analysis.possible_root_cause
        assert data["recommended_checks"] == mock_analysis.recommended_checks
        assert data["suggested_resolution"] == mock_analysis.suggested_resolution


def test_analyze_incident_gemini_failure_returns_502(client, sample_incident):
    with patch("app.services.ai_service.get_settings") as mock_settings, \
         patch("app.services.ai_service.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="test-key")
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("Rate limit reached")

        response = client.post(f"/incidents/{sample_incident['id']}/analyze")
        assert response.status_code == 502
        assert "AI analysis failed" in response.json()["detail"]


def test_analyze_incident_invalid_json_returns_502(client, sample_incident):
    with patch("app.services.ai_service.get_settings") as mock_settings, \
         patch("app.services.ai_service.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="test-key")
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.text = "NOT_JSON"
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        response = client.post(f"/incidents/{sample_incident['id']}/analyze")
        assert response.status_code == 502
        assert "Failed to parse AI response" in response.json()["detail"]
def test_analyze_incident_passes_rag_context_to_gemini(client, sample_incident):
    mock_analysis = AIIncidentAnalysis(
        summary="AI-generated summary with RAG context.",
        possible_root_cause="Connection leak root cause.",
        recommended_checks=["Check connection pool"],
        suggested_resolution="Increase pool max connections.",
    )

    with patch("app.services.ai_service.get_settings") as mock_settings, \
         patch("app.services.ai_service.genai.Client") as mock_genai_client:
        mock_settings.return_value = Settings(gemini_api_key="test-key", gemini_model="gemini-3.6-flash")
        mock_response = MagicMock()
        mock_response.parsed = mock_analysis
        mock_genai_client.return_value.models.generate_content.return_value = mock_response

        response = client.post(f"/incidents/{sample_incident['id']}/analyze")
        assert response.status_code == 200

        # Verify Gemini was called with a prompt containing knowledge context
        call_args = mock_genai_client.return_value.models.generate_content.call_args
        assert call_args is not None
        prompt_content = call_args.kwargs.get("contents") or call_args[1].get("contents")
        assert "Relevant Troubleshooting Knowledge" in prompt_content
        assert "Database" in prompt_content or "pool" in prompt_content.lower()
        assert response.json()["knowledge_used"] is True


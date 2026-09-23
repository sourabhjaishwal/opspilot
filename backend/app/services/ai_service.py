import json
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import get_settings
from app.exceptions import AIServiceConfigError, AIServiceError
from app.models.incident import Incident
from app.schemas.ai import AIIncidentAnalysis

logger = logging.getLogger(__name__)


def build_incident_prompt(
    service_name: str,
    service_status: str,
    severity: str,
    title: str,
    description: str,
) -> str:
    """Construct a clean, explicit prompt for Gemini incident root-cause analysis."""
    return f"""You are an expert site reliability and DevOps engineering assistant analyzing a reported operational incident.

Incident Details:
- Affected Service: {service_name}
- Current Service Health Status: {service_status}
- Severity Level: {severity}
- Incident Title: {title}
- Incident Description: {description}

Please analyze this incident and return a structured JSON response matching this schema:
{{
  "summary": "1 sentence concise summary of the incident. Explicitly include a disclaimer that this is an AI-generated recommendation.",
  "possible_root_cause": "1-2 sentence detailed analysis of probable root cause(s).",
  "recommended_checks": [
    "Short Diagnostic check 1",
    "Short Diagnostic check 2"
  ],
  "suggested_resolution": "1-2 sentence pragmatic, actionable steps for remediation or mitigation."
}}

Ensure your response is valid JSON adhering to this exact format. Keep the output extremely short, concise, and to the point. Limit explanations to 1-2 sentences max per field."""


def analyze_incident(incident: Incident) -> AIIncidentAnalysis:
    """Analyze an incident using the Gemini API and return a structured analysis."""
    settings = get_settings()
    if not settings.gemini_api_key or not settings.gemini_api_key.strip():
        raise AIServiceConfigError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment."
        )

    service_name = incident.service.name if incident.service is not None else "Unknown Service"
    service_status = incident.service.status if incident.service is not None else "Unknown"

    prompt = build_incident_prompt(
        service_name=service_name,
        service_status=service_status,
        severity=incident.severity,
        title=incident.title,
        description=incident.description,
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIIncidentAnalysis,
                temperature=0.2,
            ),
        )

        # 1. If google-genai structured output parsed the object directly
        if getattr(response, "parsed", None) is not None:
            if isinstance(response.parsed, AIIncidentAnalysis):
                return response.parsed
            if isinstance(response.parsed, dict):
                return AIIncidentAnalysis.model_validate(response.parsed)

        # 2. Fallback: Parse raw response text as JSON
        if hasattr(response, "text") and response.text:
            text = response.text.strip()
            # Strip markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            parsed_data = json.loads(text.strip())
            return AIIncidentAnalysis.model_validate(parsed_data)

        raise AIServiceError("Gemini returned an empty response.")
    except AIServiceConfigError:
        raise
    except APIError as exc:
        logger.error("Gemini API error during incident analysis: %s", exc)
        err_msg = str(exc).lower()
        if "429" in err_msg or "503" in err_msg or "quota" in err_msg or "exhausted" in err_msg:
            raise AIServiceError("The Gemini API is currently experiencing high demand. This demand spike is usually temporary. Please try again later.") from exc
        raise AIServiceError(f"Gemini API error: {exc.message if hasattr(exc, 'message') else str(exc)}") from exc
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini response as JSON: %s", exc)
        raise AIServiceError("Failed to parse AI response into structured format.") from exc
    except Exception as exc:
        logger.error("Unexpected error in AI service: %s", exc)
        if isinstance(exc, AIServiceError):
            raise
        raise AIServiceError(f"AI analysis failed: {str(exc)}") from exc

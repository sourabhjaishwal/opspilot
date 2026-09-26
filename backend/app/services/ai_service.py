import json
import logging
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import get_settings
from app.exceptions import AIServiceConfigError, AIServiceError
from app.models.incident import Incident
from app.schemas.ai import AIIncidentAnalysis
from app.services import rag_service

logger = logging.getLogger(__name__)

# Fallback models in case the configured model is experiencing high demand (503 / 429)
_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
]


def build_incident_prompt(
    service_name: str,
    service_status: str,
    severity: str,
    title: str,
    description: str,
    retrieved_context: str = "",
) -> str:
    """Construct a clean, explicit prompt for Gemini incident root-cause analysis.

    If retrieved_context is provided, it is injected as supporting knowledge
    from the local knowledge base. Gemini is instructed to treat it as context,
    not as a confirmed diagnosis.
    """
    if retrieved_context.strip():
        knowledge_block = (
            "\nRelevant Troubleshooting Knowledge (retrieved from internal knowledge base"
            " — use as supporting context only, NOT a confirmed diagnosis):\n"
            "---\n"
            f"{retrieved_context}\n"
            "---\n"
        )
    else:
        knowledge_block = (
            "\nNo pre-existing knowledge entries matched this incident."
            " Rely on your general SRE expertise.\n"
        )

    return f"""You are an expert site reliability and DevOps engineering assistant analyzing a reported operational incident.

Incident Details:
- Affected Service: {service_name}
- Current Service Health Status: {service_status}
- Severity Level: {severity}
- Incident Title: {title}
- Incident Description: {description}
{knowledge_block}
Important: Your response is an AI-generated recommendation, not a confirmed diagnosis. Verify findings before making production changes.

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


def _execute_gemini_call(client: genai.Client, model: str, prompt: str):
    """Execute generate_content call against a specific Gemini model."""
    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIIncidentAnalysis,
            temperature=0.2,
        ),
    )


def analyze_incident(incident: Incident) -> AIIncidentAnalysis:
    """Analyze an incident using the Gemini API and return a structured analysis.

    RAG flow:
    1. Retrieve relevant knowledge from the local knowledge base (keyword matching).
    2. Format retrieved knowledge into a prompt-ready string.
    3. Build the enriched Gemini prompt with incident details + knowledge context.
    4. Call Gemini and parse the response.
    5. Return the analysis with knowledge_used indicating whether RAG returned results.
    """
    settings = get_settings()
    if not settings.gemini_api_key or not settings.gemini_api_key.strip():
        raise AIServiceConfigError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment."
        )

    service_name = incident.service.name if incident.service is not None else "Unknown Service"
    service_status = incident.service.status if incident.service is not None else "Unknown"

    # Step 1: RAG retrieval — find relevant knowledge entries
    retrieved_entries = rag_service.retrieve_relevant_knowledge(
        title=incident.title,
        description=incident.description,
        service_name=service_name,
        severity=incident.severity,
    )
    knowledge_used = len(retrieved_entries) > 0

    # Step 2: Format knowledge entries into a readable string
    retrieved_context = rag_service.format_knowledge_for_prompt(retrieved_entries)

    # Step 3: Build the enriched prompt
    prompt = build_incident_prompt(
        service_name=service_name,
        service_status=service_status,
        severity=incident.severity,
        title=incident.title,
        description=incident.description,
        retrieved_context=retrieved_context,
    )

    client = genai.Client(api_key=settings.gemini_api_key)

    # Candidate models to try: configured model first, followed by fallbacks
    models_to_try = [settings.gemini_model]
    for fb in _FALLBACK_MODELS:
        if fb not in models_to_try:
            models_to_try.append(fb)

    response = None
    last_error: Exception | None = None

    for model_name in models_to_try:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(
                    "Attempting AI analysis with model '%s' (attempt %d/%d)...",
                    model_name,
                    attempt + 1,
                    max_retries,
                )
                response = _execute_gemini_call(client, model_name, prompt)
                last_error = None
                break
            except APIError as exc:
                last_error = exc
                err_msg = str(exc).lower()
                is_transient = any(
                    code in err_msg
                    for code in ("503", "429", "unavailable", "quota", "exhausted", "high demand")
                )
                if is_transient and attempt < max_retries - 1:
                    wait_time = 0.5 * (2 ** attempt)
                    logger.warning(
                        "Gemini model '%s' returned transient error (%s). Retrying in %.1fs...",
                        model_name,
                        exc,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        "Gemini model '%s' failed on attempt %d: %s",
                        model_name,
                        attempt + 1,
                        exc,
                    )
                    break
            except Exception as exc:
                last_error = exc
                logger.error("Non-API exception calling model '%s': %s", model_name, exc)
                break

        if response is not None:
            break

    if response is None:
        if last_error:
            err_msg = str(last_error).lower()
            if any(code in err_msg for code in ("503", "429", "unavailable", "quota", "exhausted", "high demand")):
                raise AIServiceError(
                    "The Gemini API is currently experiencing high demand. This demand spike is usually temporary. Please try again later."
                ) from last_error
            if isinstance(last_error, APIError):
                raise AIServiceError(
                    f"Gemini API error: {last_error.message if hasattr(last_error, 'message') else str(last_error)}"
                ) from last_error
            raise AIServiceError(f"AI analysis failed: {str(last_error)}") from last_error
        raise AIServiceError("Gemini returned an empty response.")

    try:
        parsed_data: dict = {}

        # 1. If google-genai structured output parsed the object directly
        if getattr(response, "parsed", None) is not None:
            if isinstance(response.parsed, AIIncidentAnalysis):
                parsed = response.parsed
                parsed.knowledge_used = knowledge_used
                return parsed
            if isinstance(response.parsed, dict):
                parsed_data = response.parsed

        # 2. Fallback: Parse raw response text as JSON
        if not parsed_data and hasattr(response, "text") and response.text:
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            parsed_data = json.loads(text.strip())

        if not parsed_data:
            raise AIServiceError("Gemini returned an empty response.")

        parsed_data["knowledge_used"] = knowledge_used
        return AIIncidentAnalysis.model_validate(parsed_data)

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini response as JSON: %s", exc)
        raise AIServiceError("Failed to parse AI response into structured format.") from exc
    except Exception as exc:
        logger.error("Unexpected error in AI service: %s", exc)
        if isinstance(exc, AIServiceError):
            raise
        raise AIServiceError(f"AI analysis failed: {str(exc)}") from exc

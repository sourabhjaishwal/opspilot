"""
RAG (Retrieval-Augmented Generation) service for OpsPilot.

This module implements a simple, local keyword-based retrieval system.
It searches a local JSON knowledge base using token matching and returns
the most relevant troubleshooting entries for a given incident.

How it works (interview-friendly explanation):
1. Load all knowledge entries from the local JSON knowledge base file.
2. Tokenize the incident text (title + description + service name + severity).
3. For each knowledge entry, count how many of its keywords appear in the
   incident tokens.
4. Rank entries by match count (highest first).
5. Return the top entries that have at least one keyword match.

No external dependencies, no embeddings, no vector databases.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the local knowledge base JSON file
_KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge" / "knowledge_base.json"

# Maximum number of knowledge entries to return per query
_MAX_RESULTS = 3

# Minimum keyword match count required to include an entry
_MIN_MATCH_THRESHOLD = 1


def _load_knowledge_base() -> list[dict]:
    """Load the knowledge base from the local JSON file."""
    try:
        with open(_KNOWLEDGE_BASE_PATH, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Knowledge base file not found at %s", _KNOWLEDGE_BASE_PATH)
        return []
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse knowledge base JSON: %s", exc)
        return []


def _tokenize(text: str) -> set[str]:
    """
    Convert a text string into a set of lowercased tokens.

    Splits on whitespace and non-alphanumeric characters, removes empty tokens.
    Example: "DB pool exhausted!" -> {"db", "pool", "exhausted"}
    """
    tokens = re.split(r"[\s\W]+", text.lower())
    return {t for t in tokens if t}


def retrieve_relevant_knowledge(
    title: str,
    description: str,
    service_name: str,
    severity: str,
) -> list[dict]:
    """
    Retrieve relevant knowledge base entries for an incident.

    This is the core RAG retrieval function. It performs keyword/token matching
    between the incident context and the knowledge base entries.

    Args:
        title: Incident title.
        description: Incident description.
        service_name: Name of the affected service.
        severity: Incident severity level.

    Returns:
        A list of matching knowledge entry dicts, ordered by relevance score,
        up to _MAX_RESULTS entries. Returns an empty list if no matches found.
    """
    # Step 1: Build the incident token set from all incident text fields
    incident_text = f"{title} {description} {service_name} {severity}"
    incident_tokens = _tokenize(incident_text)

    if not incident_tokens:
        return []

    # Step 2: Load the knowledge base
    knowledge_entries = _load_knowledge_base()

    # Step 3: Score each entry by counting keyword matches
    scored_entries: list[tuple[int, dict]] = []

    for entry in knowledge_entries:
        match_count = 0
        entry_keywords: list[str] = entry.get("keywords", [])

        for keyword in entry_keywords:
            # Check if the keyword (as a token set) is a subset of incident tokens
            # This allows multi-word keywords like "pool exhausted" to match
            keyword_tokens = _tokenize(keyword)
            if keyword_tokens and keyword_tokens.issubset(incident_tokens):
                match_count += 1

        if match_count >= _MIN_MATCH_THRESHOLD:
            scored_entries.append((match_count, entry))

    # Step 4: Sort by match count descending
    scored_entries.sort(key=lambda x: x[0], reverse=True)

    # Step 5: Return the top N entries (without the score)
    results = [entry for _, entry in scored_entries[:_MAX_RESULTS]]

    logger.info(
        "RAG retrieval: query='%s...' matched %d/%d knowledge entries",
        incident_text[:60],
        len(results),
        len(knowledge_entries),
    )

    return results


def format_knowledge_for_prompt(entries: list[dict]) -> str:
    """
    Format retrieved knowledge entries into a readable prompt section.

    Converts structured knowledge entries into a plain-text block that can
    be inserted directly into the Gemini prompt.

    Args:
        entries: List of knowledge entry dicts from retrieve_relevant_knowledge.

    Returns:
        A formatted string ready to be injected into the AI prompt,
        or an empty string if no entries provided.
    """
    if not entries:
        return ""

    sections = []
    for i, entry in enumerate(entries, start=1):
        lines = [f"[Knowledge Entry {i}: {entry.get('title', 'Unknown')}]"]

        if entry.get("possible_causes"):
            lines.append("Possible Causes:")
            for cause in entry["possible_causes"]:
                lines.append(f"  - {cause}")

        if entry.get("troubleshooting_steps"):
            lines.append("Troubleshooting Steps:")
            for step in entry["troubleshooting_steps"]:
                lines.append(f"  - {step}")

        if entry.get("resolution"):
            lines.append(f"Resolution Guidance: {entry['resolution']}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)

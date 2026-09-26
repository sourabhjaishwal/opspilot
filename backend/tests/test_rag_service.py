import pytest
from app.services.rag_service import (
    format_knowledge_for_prompt,
    retrieve_relevant_knowledge,
)


def test_api_500_incident_retrieves_relevant_knowledge():
    results = retrieve_relevant_knowledge(
        title="HTTP 500 Errors on Card Settlement Endpoint",
        description="The settlement API endpoint is throwing 500 Internal Server Error after recent deployment.",
        service_name="payment-service",
        severity="high",
    )
    assert len(results) >= 1
    titles = [entry["title"] for entry in results]
    assert any("500" in t or "Internal Server Error" in t for t in titles), (
        f"Expected a 500-related knowledge entry, got: {titles}"
    )


def test_database_incident_retrieves_db_knowledge():
    results = retrieve_relevant_knowledge(
        title="Failed Database Connections in Checkout Thread Pool",
        description="Order checkout workers threw pool timeout exceptions (QueuePool limit reached) during traffic surge.",
        service_name="order-management-api",
        severity="critical",
    )
    assert len(results) >= 1
    titles = [entry["title"] for entry in results]
    assert any("Database" in t or "Connection" in t for t in titles), (
        f"Expected a database-related entry, got: {titles}"
    )


def test_unrelated_incident_does_not_retrieve_every_entry():
    results = retrieve_relevant_knowledge(
        title="UI rendering glitch on settings page",
        description="The settings page sometimes flickers on Safari browser when switching tabs.",
        service_name="frontend-app",
        severity="low",
    )
    assert len(results) < 5, (
        f"Expected fewer than 5 results for unrelated incident, got {len(results)}"
    )


def test_no_match_returns_empty_list():
    results = retrieve_relevant_knowledge(
        title="zzyxx quantum flux capacitor misalignment",
        description="The xyzzy module produced an unexpected quasar emission coefficient divergence.",
        service_name="xyzzy-service",
        severity="low",
    )
    assert results == [], f"Expected empty list for no-match query, got: {results}"


def test_auth_incident_retrieves_auth_knowledge():
    results = retrieve_relevant_knowledge(
        title="Intermittent HTTP 401 Unauthorized Errors on Token Validation",
        description="Auth proxy returning 401 Unauthorized for valid JWT bearer tokens due to clock skew.",
        service_name="user-management-api",
        severity="high",
    )
    assert len(results) >= 1
    titles = [entry["title"] for entry in results]
    assert any("Auth" in t or "401" in t or "Token" in t for t in titles), (
        f"Expected an auth-related entry, got: {titles}"
    )


def test_notification_incident_retrieves_notification_knowledge():
    results = retrieve_relevant_knowledge(
        title="Delayed Transactional Email Dispatch",
        description="Transactional email delivery delayed by 30 minutes for order confirmations.",
        service_name="notification-service",
        severity="medium",
    )
    assert len(results) >= 1
    titles = [entry["title"] for entry in results]
    assert any("Notification" in t or "Email" in t for t in titles), (
        f"Expected a notification-related entry, got: {titles}"
    )


def test_order_incident_retrieves_order_knowledge():
    results = retrieve_relevant_knowledge(
        title="Orders Stuck in Pending Processing State",
        description="Checkout completion events failing to transition order status from pending to confirmed.",
        service_name="order-management-api",
        severity="high",
    )
    assert len(results) >= 1
    titles = [entry["title"] for entry in results]
    assert any("Order" in t or "order" in t for t in titles), (
        f"Expected an order-related entry, got: {titles}"
    )


def test_format_knowledge_for_prompt_returns_empty_string_on_no_entries():
    result = format_knowledge_for_prompt([])
    assert result == ""


def test_format_knowledge_for_prompt_includes_entry_title():
    entries = retrieve_relevant_knowledge(
        title="Database connection pool exhausted",
        description="QueuePool limit reached causing connection timeout errors.",
        service_name="checkout-service",
        severity="critical",
    )
    if entries:
        formatted = format_knowledge_for_prompt(entries)
        assert len(formatted) > 0
        assert entries[0]["title"] in formatted


def test_format_knowledge_for_prompt_contains_troubleshooting_steps():
    entries = retrieve_relevant_knowledge(
        title="HTTP 500 Internal Server Error on payment endpoint",
        description="Settlement API returning 500 errors after deployment.",
        service_name="payment-api",
        severity="high",
    )
    if entries:
        formatted = format_knowledge_for_prompt(entries)
        assert "Troubleshooting" in formatted or "troubleshooting" in formatted.lower()

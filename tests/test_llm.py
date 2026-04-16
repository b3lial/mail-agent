from unittest.mock import MagicMock, patch

import pytest

from mail_agent.llm import LLMClient, _extract_json
from mail_agent.models import AgentAction

INSTRUCTIONS = "- Delete spam\n- Move invoices to INBOX.Invoices\n- Mark the rest as read"


def _make_client(llm_response: str) -> LLMClient:
    """Create an LLMClient with a mocked Ollama backend."""
    with patch("mail_agent.llm.ollama.Client") as mock_cls:
        mock_ollama = MagicMock()
        mock_cls.return_value = mock_ollama
        mock_ollama.chat.return_value.message.content = llm_response
        client = LLMClient(model="llama3.2", base_url="http://localhost:11434")
        # Keep the mock attached so it's active during the test
        client._client = mock_ollama
    return client


# ---------------------------------------------------------------------------
# _extract_json helper
# ---------------------------------------------------------------------------

def test_extract_json_plain():
    raw = '{"action": "delete", "reason": "Spam"}'
    result = _extract_json(raw)
    assert result["action"] == "delete"


def test_extract_json_with_markdown_fence():
    raw = '```json\n{"action": "move", "target_folder": "INBOX.Invoices", "reason": "Invoice"}\n```'
    result = _extract_json(raw)
    assert result["action"] == "move"
    assert result["target_folder"] == "INBOX.Invoices"


def test_extract_json_with_plain_fence():
    raw = '```\n{"action": "mark_read", "reason": "Normal"}\n```'
    result = _extract_json(raw)
    assert result["action"] == "mark_read"


# ---------------------------------------------------------------------------
# decide_action
# ---------------------------------------------------------------------------

def test_decide_action_mark_read():
    client = _make_client('{"action": "mark_read", "reason": "Normal email"}')

    action = client.decide_action(
        subject="Hello",
        sender="friend@example.com",
        date="2024-01-01T12:00:00",
        body="Just checking in.",
        instructions=INSTRUCTIONS,
    )

    assert action.action == "mark_read"
    assert action.reason == "Normal email"


def test_decide_action_move():
    client = _make_client(
        '{"action": "move", "target_folder": "INBOX.Invoices", "reason": "Contains invoice"}'
    )

    action = client.decide_action(
        subject="Invoice #42",
        sender="billing@vendor.com",
        date="2024-01-01T12:00:00",
        body="Please find your invoice attached.",
        instructions=INSTRUCTIONS,
    )

    assert action.action == "move"
    assert action.target_folder == "INBOX.Invoices"


def test_decide_action_delete():
    client = _make_client('{"action": "delete", "reason": "Lead generation spam"}')

    action = client.decide_action(
        subject="Boost your sales!",
        sender="leads@spamco.com",
        date="2024-01-01T12:00:00",
        body="We can get you 100 new leads per month.",
        instructions=INSTRUCTIONS,
    )

    assert action.action == "delete"


def test_decide_action_fallback_on_invalid_json():
    client = _make_client("Sorry, I am unable to decide.")

    action = client.decide_action(
        subject="Test",
        sender="test@example.com",
        date="2024-01-01T12:00:00",
        body="Body text.",
        instructions=INSTRUCTIONS,
    )

    assert action.action == "mark_read"
    assert "fallback" in (action.reason or "").lower()


def test_decide_action_fallback_on_empty_response():
    client = _make_client("")

    action = client.decide_action(
        subject="Test",
        sender="test@example.com",
        date="2024-01-01T12:00:00",
        body=None,
        instructions=INSTRUCTIONS,
    )

    assert action.action == "mark_read"

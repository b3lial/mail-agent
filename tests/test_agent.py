import os
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from mail_agent.agent import Agent
from mail_agent.config import AgentConfig, Config, LLMConfig, ProxyConfig
from mail_agent.models import AgentAction, EmailDetail, EmailSummary

os.environ.setdefault("MAIL_PROXY_API_KEY", "test-key")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_config(folder=None) -> Config:
    return Config(
        proxy=ProxyConfig(base_url="http://127.0.0.1:8080"),
        llm=LLMConfig(model="llama3.2", base_url="http://localhost:11434"),
        agent=AgentConfig(instructions="- Mark all as read", folder=folder),
    )


SUMMARY = EmailSummary(
    uid=42,
    message_id="<msg42@test.com>",
    subject="Invoice #123",
    sender="billing@vendor.com",
    date=datetime(2024, 1, 1, 12, 0),
    is_read=False,
    folder="INBOX",
)

DETAIL = EmailDetail(
    uid=42,
    message_id="<msg42@test.com>",
    subject="Invoice #123",
    sender="billing@vendor.com",
    date=datetime(2024, 1, 1, 12, 0),
    is_read=False,
    folder="INBOX",
    body_text="Please find the invoice attached.",
    body_html=None,
    attachments=[],
)


def make_agent_with_mocks(action: AgentAction, folder=None):
    """Build an Agent with mocked ProxyClient and LLMClient, return (agent, proxy_mock)."""
    with patch("mail_agent.agent.ProxyClient") as mock_proxy_cls, \
         patch("mail_agent.agent.LLMClient") as mock_llm_cls:

        mock_proxy = MagicMock()
        mock_proxy.list_unread.return_value = [SUMMARY]
        mock_proxy.get_email.return_value = DETAIL
        mock_proxy_cls.return_value = mock_proxy

        mock_llm = MagicMock()
        mock_llm.decide_action.return_value = action
        mock_llm_cls.return_value = mock_llm

        agent = Agent(make_config(folder=folder))

    return agent, mock_proxy


# ---------------------------------------------------------------------------
# run_once
# ---------------------------------------------------------------------------

@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_run_once_no_emails_returns_zero(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = []
    mock_proxy_cls.return_value = mock_proxy

    agent = Agent(make_config())
    count = agent.run_once()

    assert count == 0
    mock_proxy.list_unread.assert_called_once_with(folder=None)


@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_run_once_returns_email_count(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY, SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(action="mark_read")
    mock_llm_cls.return_value = mock_llm

    agent = Agent(make_config())
    count = agent.run_once()

    assert count == 2


# ---------------------------------------------------------------------------
# Action execution
# ---------------------------------------------------------------------------

@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_action_mark_read(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(action="mark_read", reason="Normal")
    mock_llm_cls.return_value = mock_llm

    Agent(make_config()).run_once()

    mock_proxy.mark_as_read.assert_called_once_with(42, folder=None)


@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_action_move(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(
        action="move", target_folder="INBOX.Invoices", reason="Invoice"
    )
    mock_llm_cls.return_value = mock_llm

    Agent(make_config()).run_once()

    mock_proxy.move.assert_called_once_with(42, "INBOX.Invoices", folder=None)
    mock_proxy.mark_as_read.assert_not_called()


@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_action_delete(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(action="delete", reason="Spam")
    mock_llm_cls.return_value = mock_llm

    Agent(make_config()).run_once()

    mock_proxy.delete.assert_called_once_with(42, folder=None)


@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_action_reply_falls_back_to_mark_read(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(action="reply", reason="Needs response")
    mock_llm_cls.return_value = mock_llm

    Agent(make_config()).run_once()

    mock_proxy.mark_as_read.assert_called_once_with(42, folder=None)
    mock_proxy.move.assert_not_called()


@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_action_move_without_target_folder_falls_back(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(action="move")  # missing target_folder
    mock_llm_cls.return_value = mock_llm

    Agent(make_config()).run_once()

    mock_proxy.mark_as_read.assert_called_once_with(42, folder=None)
    mock_proxy.move.assert_not_called()


@patch("mail_agent.agent.LLMClient")
@patch("mail_agent.agent.ProxyClient")
def test_folder_passed_through_to_proxy(mock_proxy_cls, mock_llm_cls):
    mock_proxy = MagicMock()
    mock_proxy.list_unread.return_value = [SUMMARY]
    mock_proxy.get_email.return_value = DETAIL
    mock_proxy_cls.return_value = mock_proxy

    mock_llm = MagicMock()
    mock_llm.decide_action.return_value = AgentAction(action="mark_read")
    mock_llm_cls.return_value = mock_llm

    Agent(make_config(folder="INBOX.Pending")).run_once()

    mock_proxy.list_unread.assert_called_once_with(folder="INBOX.Pending")
    mock_proxy.get_email.assert_called_once_with(42, folder="INBOX.Pending")
    mock_proxy.mark_as_read.assert_called_once_with(42, folder="INBOX.Pending")

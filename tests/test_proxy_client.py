import os
from unittest.mock import MagicMock

import pytest

from mail_agent.models import EmailDetail, EmailSummary, StatusResponse
from mail_agent.proxy_client import ProxyClient

BASE_URL = "http://127.0.0.1:8080"

os.environ.setdefault("MAIL_PROXY_API_KEY", "test-key")

SUMMARY_DATA = {
    "uid": 1,
    "message_id": "<msg1@test.com>",
    "subject": "Test Subject",
    "sender": "sender@example.com",
    "date": "2024-01-01T12:00:00",
    "is_read": False,
    "folder": "INBOX",
}

DETAIL_DATA = {
    **SUMMARY_DATA,
    "body_text": "Hello world",
    "body_html": None,
    "attachments": [],
}


def _mock_response(data, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def client() -> ProxyClient:
    c = ProxyClient(BASE_URL, os.environ["MAIL_PROXY_API_KEY"])
    c._client = MagicMock()  # replace the httpx.Client instance with a mock
    return c


def test_list_unread_returns_summaries(client):
    client._client.get.return_value = _mock_response([SUMMARY_DATA])

    result = client.list_unread()

    assert len(result) == 1
    assert isinstance(result[0], EmailSummary)
    assert result[0].uid == 1
    assert result[0].subject == "Test Subject"


def test_list_unread_with_folder(client):
    client._client.get.return_value = _mock_response([])

    client.list_unread(folder="INBOX.Pending")

    _, kwargs = client._client.get.call_args
    assert kwargs["params"] == {"folder": "INBOX.Pending"}


def test_get_email_returns_detail(client):
    client._client.get.return_value = _mock_response(DETAIL_DATA)

    result = client.get_email(1)

    assert isinstance(result, EmailDetail)
    assert result.uid == 1
    assert result.body_text == "Hello world"


def test_mark_as_read(client):
    client._client.post.return_value = _mock_response({"status": "ok"})

    result = client.mark_as_read(1)

    assert isinstance(result, StatusResponse)
    assert result.status == "ok"
    client._client.post.assert_called_once()


def test_move_sends_correct_body(client):
    client._client.post.return_value = _mock_response({"status": "ok"})

    result = client.move(1, "INBOX.Invoices")

    assert result.status == "ok"
    _, kwargs = client._client.post.call_args
    assert kwargs["json"] == {"target_folder": "INBOX.Invoices"}


def test_delete(client):
    client._client.delete.return_value = _mock_response({"status": "ok"})

    result = client.delete(1)

    assert result.status == "ok"
    client._client.delete.assert_called_once()


def test_list_folders(client):
    client._client.get.return_value = _mock_response(["INBOX", "INBOX.Invoices", "Trash"])

    result = client.list_folders()

    assert result == ["INBOX", "INBOX.Invoices", "Trash"]

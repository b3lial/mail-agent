import logging
from typing import Optional

import httpx

from .models import EmailDetail, EmailSummary, StatusResponse

logger = logging.getLogger(__name__)


class ProxyClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def list_unread(self, folder: Optional[str] = None) -> list[EmailSummary]:
        params = {"folder": folder} if folder else {}
        logger.debug("GET /mails params=%s", params)
        response = self._client.get(f"{self._base_url}/mails", params=params)
        response.raise_for_status()
        return [EmailSummary(**item) for item in response.json()]

    def get_email(self, uid: int, folder: Optional[str] = None) -> EmailDetail:
        params = {"folder": folder} if folder else {}
        logger.debug("GET /mails/%d params=%s", uid, params)
        response = self._client.get(f"{self._base_url}/mails/{uid}", params=params)
        response.raise_for_status()
        return EmailDetail(**response.json())

    def mark_as_read(self, uid: int, folder: Optional[str] = None) -> StatusResponse:
        params = {"folder": folder} if folder else {}
        logger.debug("POST /mails/%d/read", uid)
        response = self._client.post(f"{self._base_url}/mails/{uid}/read", params=params)
        response.raise_for_status()
        return StatusResponse(**response.json())

    def move(self, uid: int, target_folder: str, folder: Optional[str] = None) -> StatusResponse:
        params = {"folder": folder} if folder else {}
        logger.debug("POST /mails/%d/move -> %s", uid, target_folder)
        response = self._client.post(
            f"{self._base_url}/mails/{uid}/move",
            params=params,
            json={"target_folder": target_folder},
        )
        response.raise_for_status()
        return StatusResponse(**response.json())

    def delete(self, uid: int, folder: Optional[str] = None) -> StatusResponse:
        params = {"folder": folder} if folder else {}
        logger.debug("DELETE /mails/%d", uid)
        response = self._client.delete(f"{self._base_url}/mails/{uid}", params=params)
        response.raise_for_status()
        return StatusResponse(**response.json())

    def list_folders(self) -> list[str]:
        logger.debug("GET /folders")
        response = self._client.get(f"{self._base_url}/folders")
        response.raise_for_status()
        return response.json()

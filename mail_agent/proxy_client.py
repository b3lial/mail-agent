import logging
from typing import Optional

import httpx

from .models import EmailDetail, EmailSummary, StatusResponse

logger = logging.getLogger(__name__)


class ProxyClient:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def list_unread(self, folder: Optional[str] = None) -> list[EmailSummary]:
        params = {"folder": folder} if folder else {}
        logger.debug("GET /mails params=%s", params)
        response = httpx.get(
            f"{self._base_url}/mails",
            headers=self._headers,
            params=params,
        )
        response.raise_for_status()
        return [EmailSummary(**item) for item in response.json()]

    def get_email(self, uid: int, folder: Optional[str] = None) -> EmailDetail:
        params = {"folder": folder} if folder else {}
        logger.debug("GET /mails/%d params=%s", uid, params)
        response = httpx.get(
            f"{self._base_url}/mails/{uid}",
            headers=self._headers,
            params=params,
        )
        response.raise_for_status()
        return EmailDetail(**response.json())

    def mark_as_read(self, uid: int, folder: Optional[str] = None) -> StatusResponse:
        params = {"folder": folder} if folder else {}
        logger.debug("POST /mails/%d/read", uid)
        response = httpx.post(
            f"{self._base_url}/mails/{uid}/read",
            headers=self._headers,
            params=params,
        )
        response.raise_for_status()
        return StatusResponse(**response.json())

    def move(self, uid: int, target_folder: str, folder: Optional[str] = None) -> StatusResponse:
        params = {"folder": folder} if folder else {}
        logger.debug("POST /mails/%d/move -> %s", uid, target_folder)
        response = httpx.post(
            f"{self._base_url}/mails/{uid}/move",
            headers=self._headers,
            params=params,
            json={"target_folder": target_folder},
        )
        response.raise_for_status()
        return StatusResponse(**response.json())

    def delete(self, uid: int, folder: Optional[str] = None) -> StatusResponse:
        params = {"folder": folder} if folder else {}
        logger.debug("DELETE /mails/%d", uid)
        response = httpx.delete(
            f"{self._base_url}/mails/{uid}",
            headers=self._headers,
            params=params,
        )
        response.raise_for_status()
        return StatusResponse(**response.json())

    def list_folders(self) -> list[str]:
        logger.debug("GET /folders")
        response = httpx.get(
            f"{self._base_url}/folders",
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

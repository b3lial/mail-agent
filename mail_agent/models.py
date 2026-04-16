from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EmailSummary(BaseModel):
    uid: int
    message_id: str
    subject: str
    sender: str
    date: Optional[datetime]
    is_read: bool
    folder: str


class EmailDetail(BaseModel):
    uid: int
    message_id: str
    subject: str
    sender: str
    date: Optional[datetime]
    is_read: bool
    folder: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: list[str] = []


class StatusResponse(BaseModel):
    status: str = "ok"


class AgentAction(BaseModel):
    action: str  # mark_read | move | delete | reply
    target_folder: Optional[str] = None
    reason: Optional[str] = None

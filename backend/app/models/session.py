"""Session state model for managing conversation state across turns."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .citizen import CitizenProfile


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    citizen_profile: CitizenProfile = Field(default_factory=CitizenProfile)
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    language: str = "fr"  # "fr" or "en"
    demo_mode: bool = False
    aids_computed: list[dict] = Field(default_factory=list)
    computed_report: object = None  # EntitlementReport or None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, role: str, content: str, **kwargs):
        self.conversation_history.append(
            ChatMessage(role=role, content=content, **kwargs)
        )
        self.updated_at = datetime.now(timezone.utc)

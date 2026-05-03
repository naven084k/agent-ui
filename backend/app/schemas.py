from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant", "tool"]


class ToolEvent(BaseModel):
    id: str
    name: str
    status: Literal["running", "completed", "failed"]
    input: dict[str, Any] = Field(default_factory=dict)
    output: str = ""


class AttachmentRef(BaseModel):
    file_id: str
    name: str


class Message(BaseModel):
    id: str
    chat_id: str
    role: Role
    content: str
    tool_events: list[ToolEvent] = Field(default_factory=list)
    attachments: list[AttachmentRef] = Field(default_factory=list)
    created_at: datetime


class ChatSummary(BaseModel):
    id: str
    title: str
    model: str
    system_prompt: str | None = None
    pinned: bool = False
    created_at: datetime
    updated_at: datetime
    last_message: str = ""


class ChatDetail(ChatSummary):
    messages: list[Message] = Field(default_factory=list)


class CreateChatRequest(BaseModel):
    title: str = "New chat"
    model: str
    system_prompt: str | None = None


class UpdateChatRequest(BaseModel):
    title: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    pinned: bool | None = None


class ChatMessageInput(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    attachments: list[str] = Field(default_factory=list)


class ChatStreamRequest(BaseModel):
    chat_id: str
    model: str
    system_prompt: str | None = None
    messages: list[ChatMessageInput]
    use_tools: bool = True


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None

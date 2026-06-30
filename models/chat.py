from pydantic import BaseModel, EmailStr, Field
from typing import Annotated, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class NewSessionRequest(BaseModel):
    email: EmailStr
    model_config = {"extra": "forbid"}


class SendMessageRequest(BaseModel):
    message: Annotated[str, Field(min_length=1, max_length=4000)]
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}


class SendMessageResponse(BaseModel):
    session_id: str
    reply: str
    usage: dict[str, int]


class SessionListItem(BaseModel):
    session_id: str
    title: str
    preview: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class SessionResponse(BaseModel):
    session_id: str
    email: str
    title: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime


class NewSessionResponse(BaseModel):
    session_id: str
    message: str


class UpdateSessionTitleRequest(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200, strip_whitespace=True)]
    model_config = {"extra": "forbid"}

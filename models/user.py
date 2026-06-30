from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Annotated, Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100, strip_whitespace=True)]
    email: EmailStr
    age: Annotated[int, Field(ge=0, le=150)]
    phone: Annotated[str, Field(pattern=r"^\+?[1-9]\d{7,14}$")]
    is_active: bool = True

    model_config = {"str_strip_whitespace": True, "extra": "forbid"}


class UserUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None, min_length=1, max_length=100)]
    email: Optional[EmailStr] = None
    age: Annotated[Optional[int], Field(default=None, ge=0, le=150)]
    phone: Annotated[Optional[str], Field(default=None, pattern=r"^\+?[1-9]\d{7,14}$")]
    is_active: Optional[bool] = None

    model_config = {"str_strip_whitespace": True, "extra": "forbid"}


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    age: int
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

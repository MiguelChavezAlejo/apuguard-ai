from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(
        min_length=3,
        max_length=120,
        examples=["Miguel Chavez"],
    )

    email: EmailStr = Field(
        examples=["miguel@example.com"],
    )

    password: str = Field(
        min_length=10,
        max_length=72,
        examples=["ApuGuard#2026"],
    )


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
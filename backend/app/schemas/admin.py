from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminProjectResponse(BaseModel):
    id: int
    name: str
    target_url: str
    description: str | None
    owner_id: int
    owner_name: str
    owner_email: EmailStr
    created_at: datetime
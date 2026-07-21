from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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

class UserProfileUpdate(BaseModel):
    full_name: str = Field(
        min_length=3,
        max_length=120,
        examples=["Miguel Ángel Chávez Alejo"],
    )


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=72,
    )

    new_password: str = Field(
        min_length=10,
        max_length=72,
        examples=["NuevaClave#2026"],
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not any(character.islower() for character in value):
            raise ValueError(
                "La contraseña debe contener una letra minúscula."
            )

        if not any(character.isupper() for character in value):
            raise ValueError(
                "La contraseña debe contener una letra mayúscula."
            )

        if not any(character.isdigit() for character in value):
            raise ValueError(
                "La contraseña debe contener un número."
            )

        if not any(
            not character.isalnum()
            for character in value
        ):
            raise ValueError(
                "La contraseña debe contener un símbolo."
            )

        return value
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
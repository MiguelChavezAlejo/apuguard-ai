from pydantic import BaseModel, EmailStr, Field, field_validator


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=200,
    )

    new_password: str = Field(
        min_length=10,
        max_length=72,
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


class PasswordResetMessage(BaseModel):
    message: str
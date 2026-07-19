from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import create_user, get_user_by_email
from app.schemas.user import UserCreate
from app.security.password import hash_password


def register_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    normalized_email = user_data.email.lower().strip()
    normalized_name = user_data.full_name.strip()

    existing_user = get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya se encuentra registrado.",
        )

    password_hash = hash_password(user_data.password)

    return create_user(
        db,
        full_name=normalized_name,
        email=normalized_email,
        password_hash=password_hash,
    )
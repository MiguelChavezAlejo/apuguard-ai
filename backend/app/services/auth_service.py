from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import get_user_by_email, save_user
from app.security.jwt import create_access_token
from app.security.password import verify_password


INVALID_CREDENTIALS_MESSAGE = "Correo o contraseña incorrectos."


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> tuple[User, str, int]:
    normalized_email = email.lower().strip()

    user = get_user_by_email(db, normalized_email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_time = datetime.now(timezone.utc)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta se encuentra desactivada.",
        )

    if user.locked_until is not None:
        locked_until = user.locked_until

        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)

        if locked_until > current_time:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="La cuenta está bloqueada temporalmente.",
            )

        user.locked_until = None
        user.failed_login_attempts = 0
        save_user(db, user)

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= settings.max_login_attempts:
            user.locked_until = current_time + timedelta(
                minutes=settings.login_lock_minutes
            )

        save_user(db, user)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    save_user(db, user)

    access_token, expires_in = create_access_token(user)

    return user, access_token, expires_in
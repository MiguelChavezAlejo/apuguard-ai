import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.security.password import hash_password


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_password_reset_token(
    db: Session,
    user: User,
) -> str:
    now = datetime.now(timezone.utc)

    active_tokens = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .all()
    )

    for stored_token in active_tokens:
        stored_token.used_at = now

    plain_token = secrets.token_urlsafe(48)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(plain_token),
        expires_at=now
        + timedelta(
            minutes=settings.password_reset_expire_minutes
        ),
    )

    db.add(reset_token)
    db.commit()

    return plain_token


def reset_user_password(
    db: Session,
    plain_token: str,
    new_password: str,
) -> None:
    now = datetime.now(timezone.utc)
    token_hash = hash_reset_token(plain_token)

    stored_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
        )
        .first()
    )

    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación no es válido.",
        )

    if stored_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación ya fue utilizado.",
        )

    expires_at = stored_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación ha expirado.",
        )

    user = (
        db.query(User)
        .filter(User.id == stored_token.user_id)
        .first()
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fue posible restablecer la contraseña.",
        )

    user.password_hash = hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    stored_token.used_at = now

    db.add(user)
    db.add(stored_token)
    db.commit()
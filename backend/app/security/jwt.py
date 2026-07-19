from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.models.user import User


def create_access_token(user: User) -> tuple[str, int]:
    expires_in_seconds = settings.access_token_expire_minutes * 60

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role.value,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }

    encoded_token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_token, expires_in_seconds
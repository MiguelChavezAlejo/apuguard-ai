from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email)

    return db.scalar(statement)


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    statement = select(User).where(User.id == user_id)

    return db.scalar(statement)


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password_hash: str,
    role: UserRole = UserRole.ANALYST,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def save_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
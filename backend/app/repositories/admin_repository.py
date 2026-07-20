from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User


class AdminRepository:
    @staticmethod
    def list_users(db: Session) -> list[User]:
        statement = select(User).order_by(User.created_at.desc())

        return list(db.scalars(statement).all())

    @staticmethod
    def get_user(
        db: Session,
        *,
        user_id: int,
    ) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def save_user(
        db: Session,
        *,
        user: User,
    ) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(
        db: Session,
        *,
        user: User,
    ) -> None:
        db.delete(user)
        db.commit()

    @staticmethod
    def list_projects(
        db: Session,
    ) -> list[dict]:
        statement = (
            select(
                Project,
                User.full_name,
                User.email,
            )
            .join(User, User.id == Project.owner_id)
            .order_by(Project.created_at.desc())
        )

        rows = db.execute(statement).all()

        return [
            {
                "id": project.id,
                "name": project.name,
                "target_url": project.target_url,
                "description": project.description,
                "owner_id": project.owner_id,
                "owner_name": owner_name,
                "owner_email": owner_email,
                "created_at": project.created_at,
            }
            for project, owner_name, owner_email in rows
        ]

    @staticmethod
    def get_project(
        db: Session,
        *,
        project_id: int,
    ) -> Project | None:
        return db.get(Project, project_id)

    @staticmethod
    def delete_project(
        db: Session,
        *,
        project: Project,
    ) -> None:
        db.delete(project)
        db.commit()
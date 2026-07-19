from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    @staticmethod
    def create(
        db: Session,
        *,
        name: str,
        target_url: str,
        description: str | None,
        owner_id: int,
    ) -> Project:
        project = Project(
            name=name,
            target_url=target_url,
            description=description,
            owner_id=owner_id,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def get_by_id_and_owner(
        db: Session,
        *,
        project_id: int,
        owner_id: int,
    ) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.owner_id == owner_id,
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_owner(
        db: Session,
        *,
        owner_id: int,
    ) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def update(
        db: Session,
        *,
        project: Project,
        name: str | None = None,
        target_url: str | None = None,
        description: str | None = None,
        update_description: bool = False,
    ) -> Project:
        if name is not None:
            project.name = name

        if target_url is not None:
            project.target_url = target_url

        if update_description:
            project.description = description

        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def delete(
        db: Session,
        *,
        project: Project,
    ) -> None:
        db.delete(project)
        db.commit()
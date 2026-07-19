from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    @staticmethod
    def create_project(
        db: Session,
        *,
        data: ProjectCreate,
        owner_id: int,
    ) -> Project:
        return ProjectRepository.create(
            db,
            name=data.name.strip(),
            target_url=str(data.target_url),
            description=data.description.strip() if data.description else None,
            owner_id=owner_id,
        )

    @staticmethod
    def list_projects(
        db: Session,
        *,
        owner_id: int,
    ) -> list[Project]:
        return ProjectRepository.list_by_owner(
            db,
            owner_id=owner_id,
        )

    @staticmethod
    def get_project(
        db: Session,
        *,
        project_id: int,
        owner_id: int,
    ) -> Project:
        project = ProjectRepository.get_by_id_and_owner(
            db,
            project_id=project_id,
            owner_id=owner_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado.",
            )

        return project

    @staticmethod
    def update_project(
        db: Session,
        *,
        project_id: int,
        owner_id: int,
        data: ProjectUpdate,
    ) -> Project:
        project = ProjectService.get_project(
            db,
            project_id=project_id,
            owner_id=owner_id,
        )

        fields_set = data.model_fields_set

        return ProjectRepository.update(
            db,
            project=project,
            name=data.name.strip() if data.name is not None else None,
            target_url=(
                str(data.target_url)
                if data.target_url is not None
                else None
            ),
            description=(
                data.description.strip()
                if data.description
                else None
            ),
            update_description="description" in fields_set,
        )

    @staticmethod
    def delete_project(
        db: Session,
        *,
        project_id: int,
        owner_id: int,
    ) -> None:
        project = ProjectService.get_project(
            db,
            project_id=project_id,
            owner_id=owner_id,
        )

        ProjectRepository.delete(
            db,
            project=project,
        )
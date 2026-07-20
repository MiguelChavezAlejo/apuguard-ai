from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User, UserRole
from app.repositories.admin_repository import AdminRepository


class AdminService:
    @staticmethod
    def list_users(db: Session) -> list[User]:
        return AdminRepository.list_users(db)

    @staticmethod
    def update_user_status(
        db: Session,
        *,
        user_id: int,
        is_active: bool,
        current_admin_id: int,
    ) -> User:
        user = AdminRepository.get_user(
            db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        if user.id == current_admin_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El administrador no puede desactivar "
                    "su propia cuenta."
                ),
            )

        user.is_active = is_active

        return AdminRepository.save_user(
            db,
            user=user,
        )

    @staticmethod
    def delete_user(
        db: Session,
        *,
        user_id: int,
        current_admin_id: int,
    ) -> None:
        user = AdminRepository.get_user(
            db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        if user.id == current_admin_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El administrador no puede eliminar "
                    "su propia cuenta."
                ),
            )

        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No se permite eliminar otra cuenta "
                    "administrativa desde este panel."
                ),
            )

        AdminRepository.delete_user(
            db,
            user=user,
        )

    @staticmethod
    def list_projects(db: Session) -> list[dict]:
        return AdminRepository.list_projects(db)

    @staticmethod
    def delete_project(
        db: Session,
        *,
        project_id: int,
    ) -> None:
        project = AdminRepository.get_project(
            db,
            project_id=project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado.",
            )

        AdminRepository.delete_project(
            db,
            project=project,
        )
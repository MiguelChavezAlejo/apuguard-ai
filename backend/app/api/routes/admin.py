from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminProjectResponse,
    AdminUserResponse,
    AdminUserStatusUpdate,
)
from app.security.dependencies import require_admin
from app.services.admin_service import AdminService


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[User]:
    return AdminService.list_users(db)


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserResponse,
)
def update_user_status(
    user_id: int,
    data: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> User:
    return AdminService.update_user_status(
        db,
        user_id=user_id,
        is_active=data.is_active,
        current_admin_id=current_admin.id,
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> Response:
    AdminService.delete_user(
        db,
        user_id=user_id,
        current_admin_id=current_admin.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/projects",
    response_model=list[AdminProjectResponse],
)
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    return AdminService.list_projects(db)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Response:
    AdminService.delete_project(
        db,
        project_id=project_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
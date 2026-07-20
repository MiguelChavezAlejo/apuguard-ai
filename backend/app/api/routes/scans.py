from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanResponse
from app.security.dependencies import get_current_user
from app.services.scan_service import ScanService
from app.schemas.scan import ScanResponse, ScanStartRequest

router = APIRouter(
    prefix="/scans",
    tags=["Security Scans"],
)


@router.post(
    "/projects/{project_id}",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_project_scan(
    project_id: int,
    request_data: ScanStartRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Scan:
    authorization_confirmed = (
        request_data.authorization_confirmed
        if request_data is not None
        else False
    )

    return ScanService.start_scan(
        db,
        project_id=project_id,
        owner_id=current_user.id,
        authorization_confirmed=authorization_confirmed,
    )


@router.get(
    "/projects/{project_id}",
    response_model=list[ScanResponse],
)
def list_project_scans(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Scan]:
    return ScanService.list_project_scans(
        db,
        project_id=project_id,
        owner_id=current_user.id,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Scan:
    return ScanService.get_scan(
        db,
        scan_id=scan_id,
        owner_id=current_user.id,
    )
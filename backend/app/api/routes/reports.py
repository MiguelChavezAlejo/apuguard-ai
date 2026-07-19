from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.report import SecurityReportResponse
from app.security.dependencies import get_current_user
from app.services.pdf_service import PdfService
from app.services.report_service import ReportService


router = APIRouter(
    prefix="/reports",
    tags=["AI Security Reports"],
)


@router.post(
    "/scans/{scan_id}/generate",
    response_model=SecurityReportResponse,
)
def generate_security_report(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SecurityReportResponse:
    return ReportService.generate_report(
        db,
        scan_id=scan_id,
        owner_id=current_user.id,
    )
@router.get(
    "/scans/{scan_id}/pdf",
    responses={
        200: {
            "content": {
                "application/pdf": {}
            },
            "description": "Reporte PDF generado correctamente.",
        }
    },
)
def download_security_report_pdf(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    report = ReportService.generate_report(
        db,
        scan_id=scan_id,
        owner_id=current_user.id,
    )

    pdf_content = PdfService.generate_pdf(report)

    safe_project_name = "".join(
        character
        if character.isalnum() or character in {"-", "_"}
        else "_"
        for character in report.project_name
    )

    filename = (
        f"ApuGuard_AI_{safe_project_name}_Scan_{scan_id}.pdf"
    )

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )
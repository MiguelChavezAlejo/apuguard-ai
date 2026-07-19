from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.scan import Scan, ScanStatus
from app.models.vulnerability import Vulnerability


class ScanRepository:
    @staticmethod
    def create(
        db: Session,
        *,
        project_id: int,
    ) -> Scan:
        scan = Scan(
            project_id=project_id,
            status=ScanStatus.PENDING,
        )

        db.add(scan)
        db.commit()
        db.refresh(scan)

        return scan

    @staticmethod
    def get_by_id(
        db: Session,
        *,
        scan_id: int,
    ) -> Scan | None:
        statement = (
            select(Scan)
            .options(selectinload(Scan.vulnerabilities))
            .where(Scan.id == scan_id)
        )

        return db.scalar(statement)

    @staticmethod
    def list_by_project(
        db: Session,
        *,
        project_id: int,
    ) -> list[Scan]:
        statement = (
            select(Scan)
            .options(selectinload(Scan.vulnerabilities))
            .where(Scan.project_id == project_id)
            .order_by(Scan.created_at.desc())
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def save(
        db: Session,
        *,
        scan: Scan,
    ) -> Scan:
        db.add(scan)
        db.commit()
        db.refresh(scan)

        return scan

    @staticmethod
    def add_vulnerabilities(
        db: Session,
        *,
        vulnerabilities: list[Vulnerability],
    ) -> None:
        db.add_all(vulnerabilities)
        db.commit()
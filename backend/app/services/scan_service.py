from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.scan import Scan, ScanStatus
from app.models.vulnerability import SeverityLevel, Vulnerability
from app.repositories.scan_repository import ScanRepository
from app.services.project_service import ProjectService
from app.services.zap_service import ZapService


class ScanService:
    @staticmethod
    def _map_severity(alert: dict[str, Any]) -> SeverityLevel:
        risk = str(
            alert.get("risk")
            or alert.get("riskdesc")
            or ""
        ).upper()

        if "CRITICAL" in risk:
            return SeverityLevel.CRITICAL

        if "HIGH" in risk:
            return SeverityLevel.HIGH

        if "MEDIUM" in risk:
            return SeverityLevel.MEDIUM

        if "LOW" in risk:
            return SeverityLevel.LOW

        return SeverityLevel.INFORMATIONAL

    @staticmethod
    def _parse_cwe_id(alert: dict[str, Any]) -> int | None:
        raw_value = alert.get("cweid")

        if raw_value in (None, "", "-1"):
            return None

        try:
            value = int(raw_value)
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _map_owasp_category(
        alert: dict[str, Any],
    ) -> str | None:
        tags = alert.get("tags")

        if isinstance(tags, dict):
            for key in tags:
                normalized = str(key).upper()

                if "OWASP_2021_A01" in normalized:
                    return "A01:2021 - Broken Access Control"
                if "OWASP_2021_A02" in normalized:
                    return "A02:2021 - Cryptographic Failures"
                if "OWASP_2021_A03" in normalized:
                    return "A03:2021 - Injection"
                if "OWASP_2021_A04" in normalized:
                    return "A04:2021 - Insecure Design"
                if "OWASP_2021_A05" in normalized:
                    return "A05:2021 - Security Misconfiguration"
                if "OWASP_2021_A06" in normalized:
                    return "A06:2021 - Vulnerable and Outdated Components"
                if "OWASP_2021_A07" in normalized:
                    return "A07:2021 - Identification and Authentication Failures"
                if "OWASP_2021_A08" in normalized:
                    return "A08:2021 - Software and Data Integrity Failures"
                if "OWASP_2021_A09" in normalized:
                    return "A09:2021 - Security Logging and Monitoring Failures"
                if "OWASP_2021_A10" in normalized:
                    return "A10:2021 - Server-Side Request Forgery"

        name = str(alert.get("name", "")).lower()

        if "injection" in name:
            return "A03:2021 - Injection"

        if "cross site scripting" in name or "xss" in name:
            return "A03:2021 - Injection"

        if "header" in name or "configuration" in name:
            return "A05:2021 - Security Misconfiguration"

        if "cookie" in name or "authentication" in name:
            return "A07:2021 - Identification and Authentication Failures"

        return None

    @staticmethod
    def _build_vulnerability(
        *,
        scan_id: int,
        alert: dict[str, Any],
    ) -> Vulnerability:
        return Vulnerability(
            scan_id=scan_id,
            name=str(
                alert.get("name")
                or alert.get("alert")
                or "Hallazgo sin nombre"
            ),
            severity=ScanService._map_severity(alert),
            description=alert.get("description"),
            solution=alert.get("solution"),
            evidence=alert.get("evidence"),
            affected_url=alert.get("url"),
            parameter=alert.get("param"),
            cwe_id=ScanService._parse_cwe_id(alert),
            owasp_category=ScanService._map_owasp_category(alert),
        )

    @staticmethod
    def start_scan(
        db: Session,
        *,
        project_id: int,
        owner_id: int,
    ) -> Scan:
        project = ProjectService.get_project(
            db,
            project_id=project_id,
            owner_id=owner_id,
        )

        scan = ScanRepository.create(
            db,
            project_id=project.id,
        )

        try:
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.now(timezone.utc)
            ScanRepository.save(db, scan=scan)

            zap_service = ZapService()

            target_url = project.target_url

            # Por ahora ejecutamos Spider + análisis pasivo.
            zap_service.validate_target_url(target_url)
            zap_service.check_health()
            zap_service.access_url(target_url)

            spider_id = zap_service.start_spider(target_url)
            zap_service.wait_for_spider(spider_id)
            zap_service.wait_for_passive_scan()

            alerts = zap_service.get_alerts(target_url)

            vulnerabilities = [
                ScanService._build_vulnerability(
                    scan_id=scan.id,
                    alert=alert,
                )
                for alert in alerts
            ]

            if vulnerabilities:
                ScanRepository.add_vulnerabilities(
                    db,
                    vulnerabilities=vulnerabilities,
                )

            scan.status = ScanStatus.COMPLETED
            scan.total_alerts = len(vulnerabilities)
            scan.summary = (
                f"Escaneo completado correctamente. "
                f"Se identificaron {len(vulnerabilities)} hallazgos."
            )
            scan.completed_at = datetime.now(timezone.utc)

            ScanRepository.save(db, scan=scan)

            completed_scan = ScanRepository.get_by_id(
                db,
                scan_id=scan.id,
            )

            if completed_scan is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No fue posible recuperar el escaneo completado.",
                )

            return completed_scan

        except HTTPException:
            scan.status = ScanStatus.FAILED
            scan.summary = "El escaneo no pudo completarse."
            scan.completed_at = datetime.now(timezone.utc)
            ScanRepository.save(db, scan=scan)
            raise

        except Exception as exc:
            scan.status = ScanStatus.FAILED
            scan.summary = f"Error interno durante el escaneo: {exc}"
            scan.completed_at = datetime.now(timezone.utc)
            ScanRepository.save(db, scan=scan)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error inesperado durante el escaneo.",
            ) from exc

    @staticmethod
    def get_scan(
        db: Session,
        *,
        scan_id: int,
        owner_id: int,
    ) -> Scan:
        scan = ScanRepository.get_by_id(
            db,
            scan_id=scan_id,
        )

        if scan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Escaneo no encontrado.",
            )

        ProjectService.get_project(
            db,
            project_id=scan.project_id,
            owner_id=owner_id,
        )

        return scan

    @staticmethod
    def list_project_scans(
        db: Session,
        *,
        project_id: int,
        owner_id: int,
    ) -> list[Scan]:
        ProjectService.get_project(
            db,
            project_id=project_id,
            owner_id=owner_id,
        )

        return ScanRepository.list_by_project(
            db,
            project_id=project_id,
        )
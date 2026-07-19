import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.scan import ScanStatus
from app.models.vulnerability import SeverityLevel, Vulnerability
from app.schemas.report import (
    FindingSummary,
    RiskDistribution,
    SecurityReportResponse,
)
from app.services.project_service import ProjectService
from app.services.scan_service import ScanService


class ReportService:
    SEVERITY_WEIGHT = {
        SeverityLevel.CRITICAL: 5,
        SeverityLevel.HIGH: 4,
        SeverityLevel.MEDIUM: 3,
        SeverityLevel.LOW: 2,
        SeverityLevel.INFORMATIONAL: 1,
    }

    @staticmethod
    def _group_findings(
        vulnerabilities: list[Vulnerability],
    ) -> list[FindingSummary]:
        grouped: dict[
            tuple[str, SeverityLevel, int | None, str | None],
            list[Vulnerability],
        ] = defaultdict(list)

        for vulnerability in vulnerabilities:
            key = (
                vulnerability.name,
                vulnerability.severity,
                vulnerability.cwe_id,
                vulnerability.owasp_category,
            )
            grouped[key].append(vulnerability)

        findings: list[FindingSummary] = []

        sorted_groups = sorted(
            grouped.items(),
            key=lambda item: (
                -ReportService.SEVERITY_WEIGHT[item[0][1]],
                -len(item[1]),
                item[0][0],
            ),
        )

        for (
            name,
            severity,
            cwe_id,
            owasp_category,
        ), occurrences in sorted_groups:
            first = occurrences[0]

            urls: list[str] = []
            seen_urls: set[str] = set()

            for occurrence in occurrences:
                url = occurrence.affected_url

                if url and url not in seen_urls:
                    seen_urls.add(url)
                    urls.append(url)

                if len(urls) >= 5:
                    break

            findings.append(
                FindingSummary(
                    name=name,
                    severity=severity.value,
                    cwe_id=cwe_id,
                    owasp_category=owasp_category,
                    occurrences=len(occurrences),
                    affected_urls=urls,
                    description=first.description,
                    recommendation=first.solution,
                )
            )

        return findings

    @staticmethod
    def _risk_distribution(
        vulnerabilities: list[Vulnerability],
    ) -> RiskDistribution:
        counter = Counter(
            vulnerability.severity.value
            for vulnerability in vulnerabilities
        )

        return RiskDistribution(
            critical=counter.get("CRITICAL", 0),
            high=counter.get("HIGH", 0),
            medium=counter.get("MEDIUM", 0),
            low=counter.get("LOW", 0),
            informational=counter.get("INFORMATIONAL", 0),
        )

    @staticmethod
    def _calculate_overall_risk(
        distribution: RiskDistribution,
    ) -> str:
        if distribution.critical > 0:
            return "CRITICAL"

        if distribution.high > 0:
            return "HIGH"

        if distribution.medium >= 5:
            return "HIGH"

        if distribution.medium > 0:
            return "MEDIUM"

        if distribution.low > 0:
            return "LOW"

        return "INFORMATIONAL"

    @staticmethod
    def _build_local_content(
        *,
        project_name: str,
        target_url: str,
        distribution: RiskDistribution,
        findings: list[FindingSummary],
        overall_risk: str,
    ) -> dict[str, Any]:
        principal_findings = findings[:5]

        finding_names = ", ".join(
            finding.name
            for finding in principal_findings
        )

        executive_summary = (
            f"El análisis de seguridad realizado sobre {project_name} "
            f"({target_url}) determinó un nivel de riesgo general "
            f"{overall_risk}. Se registraron "
            f"{distribution.critical} hallazgos críticos, "
            f"{distribution.high} altos, "
            f"{distribution.medium} medios, "
            f"{distribution.low} bajos y "
            f"{distribution.informational} informativos. "
            "Los resultados requieren priorizar las vulnerabilidades "
            "que puedan afectar la confidencialidad, integridad o "
            "disponibilidad del sistema."
        )

        technical_summary = (
            "OWASP ZAP realizó la exploración automatizada del objetivo "
            "y detectó configuraciones y comportamientos potencialmente "
            "inseguros. Los hallazgos fueron agrupados para eliminar "
            "duplicados y facilitar su análisis. "
            f"Entre los principales hallazgos se encuentran: "
            f"{finding_names or 'sin hallazgos relevantes'}."
        )

        actions: list[str] = []

        for finding in principal_findings:
            recommendation = (
                finding.recommendation
                or "Revisar y corregir la configuración afectada."
            )

            actions.append(
                f"[{finding.severity}] {finding.name}: "
                f"{recommendation[:300]}"
            )

        if not actions:
            actions.append(
                "Mantener monitoreo continuo y repetir el análisis "
                "después de cada cambio relevante."
            )

        conclusions = (
            "El análisis automatizado constituye una evaluación inicial "
            "y debe complementarse con revisión manual. Se recomienda "
            "corregir primero los hallazgos críticos y altos, validar las "
            "remediaciones y ejecutar un nuevo escaneo para confirmar "
            "que los riesgos fueron mitigados."
        )

        return {
            "executive_summary": executive_summary,
            "technical_summary": technical_summary,
            "prioritized_actions": actions,
            "conclusions": conclusions,
        }

    @staticmethod
    def _build_ai_input(
        *,
        project_name: str,
        target_url: str,
        overall_risk: str,
        distribution: RiskDistribution,
        findings: list[FindingSummary],
    ) -> str:
        reduced_findings = [
            {
                "name": finding.name,
                "severity": finding.severity,
                "cwe_id": finding.cwe_id,
                "owasp_category": finding.owasp_category,
                "occurrences": finding.occurrences,
                "description": (
                    finding.description[:600]
                    if finding.description
                    else None
                ),
                "recommendation": (
                    finding.recommendation[:600]
                    if finding.recommendation
                    else None
                ),
            }
            for finding in findings[:20]
        ]

        payload = {
            "project_name": project_name,
            "target_url": target_url,
            "overall_risk": overall_risk,
            "risk_distribution": distribution.model_dump(),
            "findings": reduced_findings,
        }

        return (
            "Actúa como especialista en ciberseguridad y OWASP. "
            "Genera un reporte profesional en español basado únicamente "
            "en los datos proporcionados. No inventes vulnerabilidades. "
            "Devuelve solamente JSON válido con esta estructura exacta: "
            '{"executive_summary":"...",'
            '"technical_summary":"...",'
            '"prioritized_actions":["..."],'
            '"conclusions":"..."}. '
            "Las recomendaciones deben ser concretas, priorizadas y "
            "comprensibles para personal técnico y gerencial.\n\n"
            f"DATOS:\n{json.dumps(payload, ensure_ascii=False)}"
        )

    @staticmethod
    def _extract_openai_text(
        response_data: dict[str, Any],
    ) -> str:
        direct_text = response_data.get("output_text")

        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text.strip()

        for output_item in response_data.get("output", []):
            for content_item in output_item.get("content", []):
                text = content_item.get("text")

                if isinstance(text, str) and text.strip():
                    return text.strip()

        raise ValueError("La respuesta de IA no contiene texto.")

    @staticmethod
    def _generate_with_openai(
        prompt: str,
    ) -> dict[str, Any]:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no está configurada.")

        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "input": prompt,
            },
            timeout=settings.openai_timeout_seconds,
        )

        response.raise_for_status()

        raw_text = ReportService._extract_openai_text(
            response.json()
        )

        cleaned_text = raw_text.strip()

        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.replace(
                "```json",
                "",
                1,
            )
            cleaned_text = cleaned_text.replace(
                "```",
                "",
            ).strip()

        parsed = json.loads(cleaned_text)

        required_fields = {
            "executive_summary",
            "technical_summary",
            "prioritized_actions",
            "conclusions",
        }

        if not required_fields.issubset(parsed):
            raise ValueError(
                "La IA no devolvió todos los campos requeridos."
            )

        return parsed

    @staticmethod
    def generate_report(
        db: Session,
        *,
        scan_id: int,
        owner_id: int,
    ) -> SecurityReportResponse:
        scan = ScanService.get_scan(
            db,
            scan_id=scan_id,
            owner_id=owner_id,
        )

        if scan.status != ScanStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El reporte solo puede generarse para un "
                    "escaneo completado."
                ),
            )

        project = ProjectService.get_project(
            db,
            project_id=scan.project_id,
            owner_id=owner_id,
        )

        vulnerabilities = list(scan.vulnerabilities)
        findings = ReportService._group_findings(
            vulnerabilities
        )
        distribution = ReportService._risk_distribution(
            vulnerabilities
        )
        overall_risk = ReportService._calculate_overall_risk(
            distribution
        )

        local_content = ReportService._build_local_content(
            project_name=project.name,
            target_url=project.target_url,
            distribution=distribution,
            findings=findings,
            overall_risk=overall_risk,
        )

        provider_used = "local"

        if settings.ai_provider.lower() == "openai":
            try:
                prompt = ReportService._build_ai_input(
                    project_name=project.name,
                    target_url=project.target_url,
                    overall_risk=overall_risk,
                    distribution=distribution,
                    findings=findings,
                )

                local_content = (
                    ReportService._generate_with_openai(prompt)
                )
                provider_used = "openai"

            except (
                httpx.HTTPError,
                ValueError,
                json.JSONDecodeError,
            ):
                provider_used = "local-fallback"

        return SecurityReportResponse(
            scan_id=scan.id,
            project_id=project.id,
            project_name=project.name,
            target_url=project.target_url,
            generated_at=datetime.now(timezone.utc),
            ai_provider=provider_used,
            overall_risk=overall_risk,
            executive_summary=local_content[
                "executive_summary"
            ],
            technical_summary=local_content[
                "technical_summary"
            ],
            risk_distribution=distribution,
            prioritized_actions=local_content[
                "prioritized_actions"
            ],
            conclusions=local_content["conclusions"],
            findings=findings,
        )
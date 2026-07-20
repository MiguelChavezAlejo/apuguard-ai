from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.scan import ScanStatus
from app.models.vulnerability import SeverityLevel
from pydantic import BaseModel, ConfigDict, Field


class ScanStartRequest(BaseModel):
    authorization_confirmed: bool = Field(
        default=False,
        description=(
            "Confirma que el usuario cuenta con autorización expresa "
            "para evaluar el objetivo indicado."
        ),
    )

class VulnerabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    severity: SeverityLevel
    description: str | None
    solution: str | None
    evidence: str | None
    affected_url: str | None
    parameter: str | None
    cwe_id: int | None
    owasp_category: str | None
    created_at: datetime


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: ScanStatus
    total_alerts: int
    summary: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    vulnerabilities: list[VulnerabilityResponse] = []
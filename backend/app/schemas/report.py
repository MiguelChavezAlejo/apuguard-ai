from datetime import datetime

from pydantic import BaseModel, Field


class FindingSummary(BaseModel):
    name: str
    severity: str
    cwe_id: int | None
    owasp_category: str | None
    occurrences: int
    affected_urls: list[str] = Field(default_factory=list)
    description: str | None
    recommendation: str | None


class RiskDistribution(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0


class SecurityReportResponse(BaseModel):
    scan_id: int
    project_id: int
    project_name: str
    target_url: str
    generated_at: datetime
    ai_provider: str
    overall_risk: str
    executive_summary: str
    technical_summary: str
    risk_distribution: RiskDistribution
    prioritized_actions: list[str] = Field(default_factory=list)
    conclusions: str
    findings: list[FindingSummary] = Field(default_factory=list)
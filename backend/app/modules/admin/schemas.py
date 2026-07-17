from pydantic import BaseModel, Field


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaConfirmCommand(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class AdminOverview(BaseModel):
    users: int
    active_sessions: int
    pending_reports: int
    published_reports: int
    rejected_reports: int


class AuditIntegrityResponse(BaseModel):
    valid: bool
    records_checked: int

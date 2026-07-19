"""Validated privacy HTTP contracts."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.privacy.domain import ConsentPurpose


class ConsentCommand(BaseModel):
    granted: bool


class ConsentResponse(BaseModel):
    purpose: ConsentPurpose
    policy_version: str
    granted: bool
    occurred_at: str


class DataExportResponse(BaseModel):
    request_id: str
    generated_at: str
    policy_version: str
    data: dict[str, Any]


class AccountDeletionCommand(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirmation: Literal["DELETE MY PARKSHIELD ACCOUNT"]
    mfa_code: str | None = Field(default=None, pattern=r"^[0-9]{6}$")

"""Strict product-analytics API contracts."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.observability.domain import ProductEventName
from app.modules.observability.ports import Scalar
from app.modules.observability.redaction import is_prohibited_field


class ProductEventCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProductEventName
    properties: dict[str, Scalar] = Field(default_factory=dict, max_length=8)

    @field_validator("properties")
    @classmethod
    def reject_sensitive_keys(cls, value: dict[str, Scalar]) -> dict[str, Scalar]:
        if any(is_prohibited_field(key) for key in value):
            raise ValueError("analytics properties contain a prohibited field")
        return value


class ProductEventResponse(BaseModel):
    accepted: bool

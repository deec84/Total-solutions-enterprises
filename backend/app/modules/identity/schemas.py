"""Identity API/application contracts."""

from pydantic import BaseModel, Field, field_validator

from app.modules.identity.domain import Role


class RegisterCommand(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized.count("@") != 1 or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("invalid email address")
        return normalized


class LoginCommand(BaseModel):
    email: str
    password: str


class RefreshCommand(BaseModel):
    refresh_token: str = Field(
        description="Opaque refresh credential. A successful refresh rotates it immediately."
    )


class LogoutCommand(BaseModel):
    refresh_token: str = Field(
        description=(
            "Opaque refresh credential. Logout is idempotent for a structurally valid payload."
        )
    )


class VerifyEmailCommand(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128)


class MessageResponse(BaseModel):
    message: str


class SessionResponse(BaseModel):
    id: str
    created_at: str
    expires_at: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: Role
    is_verified: bool


class TokenPair(BaseModel):
    access_token: str = Field(description="Opaque access credential.")
    refresh_token: str = Field(
        description=(
            "Opaque refresh credential. Each successful refresh rotates this value; "
            "the prior value becomes unusable immediately. The configured TTL is 30 days "
            "by default."
        )
    )
    token_type: str = Field(
        default="bearer", description="Authorization scheme for access_token."
    )
    expires_in: int = Field(
        description=(
            "Lifetime in seconds of access_token; 900 seconds with the default configuration."
        )
    )

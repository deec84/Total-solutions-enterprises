"""Privacy application service with fail-closed account deletion."""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.identity.domain import Role, User
from app.modules.identity.mfa import verify_totp
from app.modules.identity.security import PasswordManager
from app.modules.privacy.domain import (
    ConsentDecision,
    ConsentPurpose,
    DataRequestStatus,
    DataRequestType,
    DataRightsRequest,
    PrivacyRepository,
    PrivateMediaStore,
)

ACCOUNT_DELETION_CONFIRMATION = "DELETE MY PARKSHIELD ACCOUNT"


class PrivacyRequestError(ValueError):
    """A safe client error for invalid data-rights requests."""


class ExternalDataDeletionError(RuntimeError):
    """External private data could not be confirmed deleted."""


@dataclass(frozen=True, slots=True)
class DataExport:
    request_id: UUID
    generated_at: datetime
    policy_version: str
    data: dict[str, object]


class PrivacyService:
    def __init__(
        self,
        repository: PrivacyRepository,
        passwords: PasswordManager,
        subject_secret: str,
        policy_version: str,
        media_store: PrivateMediaStore | None = None,
    ) -> None:
        self._repository = repository
        self._passwords = passwords
        self._subject_secret = subject_secret
        self._policy_version = policy_version
        self._media_store = media_store

    async def consents(self, user_id: UUID) -> tuple[ConsentDecision, ...]:
        return await self._repository.latest_consents(user_id)

    async def decide_consent(
        self, user_id: UUID, purpose: ConsentPurpose, granted: bool
    ) -> ConsentDecision:
        decision = ConsentDecision(
            uuid4(),
            user_id,
            purpose,
            self._policy_version,
            granted,
            datetime.now(UTC),
        )
        await self._repository.record_consent(decision)
        return decision

    async def export(self, user_id: UUID) -> DataExport:
        requested_at = datetime.now(UTC)
        request = self._request(user_id, DataRequestType.EXPORT, requested_at)
        await self._repository.add_request(request)
        data = await self._repository.export_for_user(user_id)
        completed_at = datetime.now(UTC)
        await self._repository.complete_request(request.id, completed_at)
        return DataExport(request.id, completed_at, self._policy_version, data)

    async def delete_account(
        self,
        user: User,
        password: str,
        confirmation: str,
        mfa_code: str | None = None,
    ) -> UUID:
        if user.role is not Role.USER:
            raise PrivacyRequestError(
                "privileged accounts require controlled administrative offboarding"
            )
        if confirmation != ACCOUNT_DELETION_CONFIRMATION:
            raise PrivacyRequestError("account deletion confirmation does not match")
        if not self._passwords.verify(password, user.password_hash):
            raise PrivacyRequestError("account deletion credentials are invalid")
        if user.mfa_enabled and (
            not user.mfa_secret or mfa_code is None or not verify_totp(user.mfa_secret, mfa_code)
        ):
            raise PrivacyRequestError("a valid MFA code is required")

        requested_at = datetime.now(UTC)
        request = self._request(user.id, DataRequestType.DELETION, requested_at)
        await self._repository.add_request(request)
        media_keys = await self._repository.active_media_keys(user.id)
        media_store = self._media_store
        if media_keys and media_store is None:
            raise ExternalDataDeletionError(
                "private media storage is unavailable; account was not deleted"
            )
        if media_store is not None:
            for key in media_keys:
                try:
                    await media_store.delete(key)
                except Exception as error:
                    raise ExternalDataDeletionError(
                        "private media deletion could not be confirmed; account was not deleted"
                    ) from error

        completed_at = datetime.now(UTC)
        await self._repository.complete_request(request.id, completed_at)
        if not await self._repository.delete_account(user.id):
            raise PrivacyRequestError("account no longer exists")
        return request.id

    def _request(
        self, user_id: UUID, request_type: DataRequestType, requested_at: datetime
    ) -> DataRightsRequest:
        reference = hmac.new(
            self._subject_secret.encode(), user_id.bytes, hashlib.sha256
        ).hexdigest()
        return DataRightsRequest(
            uuid4(),
            user_id,
            reference,
            request_type,
            DataRequestStatus.PROCESSING,
            requested_at,
        )

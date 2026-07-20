"""Private S3 adapter for transient community evidence."""

import asyncio
import base64
from abc import abstractmethod
from datetime import datetime
from importlib import import_module
from typing import Protocol, cast
from urllib.parse import urlparse

from app.modules.community.media import MediaStorageError
from app.modules.observability.redaction import log_integration_failure


class S3Client(Protocol):
    @abstractmethod
    def put_object(self, **kwargs: object) -> object:
        """Upload one object through the provider client."""

    @abstractmethod
    def delete_object(self, **kwargs: object) -> object:
        """Delete one object through the provider client."""

    @abstractmethod
    def generate_presigned_url(
        self,
        client_method: str,
        *,
        Params: dict[str, str],
        ExpiresIn: int,
    ) -> str:
        """Sign one short-lived provider request."""


class S3CommunityMediaStore:
    """Use the ECS task role and bucket-default KMS encryption; never public URLs."""

    def __init__(self, bucket: str, client: S3Client | None = None) -> None:
        if not bucket.strip():
            raise ValueError("media bucket must not be empty")
        self._bucket = bucket.strip()
        if client is None:
            boto3 = import_module("boto3")
            client = cast(S3Client, boto3.client("s3"))
        self._client = client

    async def put(
        self,
        *,
        key: str,
        payload: bytes,
        content_type: str,
        checksum_sha256: str,
        retained_until: datetime,
    ) -> None:
        if not key.startswith("community-reports/") or ".." in key:
            raise ValueError("invalid community media object key")
        checksum = base64.b64encode(bytes.fromhex(checksum_sha256)).decode("ascii")

        def write() -> None:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=payload,
                ContentType=content_type,
                CacheControl="private, no-store",
                ChecksumSHA256=checksum,
                Metadata={
                    "sha256": checksum_sha256,
                    "retained-until": retained_until.isoformat(),
                },
            )

        try:
            await asyncio.to_thread(write)
        except Exception as error:
            log_integration_failure("community_media", "upload", error)
            raise MediaStorageError("community media storage failed") from error

    async def delete(self, key: str) -> None:
        if not key.startswith("community-reports/") or ".." in key:
            raise ValueError("invalid community media object key")

        def remove() -> None:
            self._client.delete_object(Bucket=self._bucket, Key=key)

        try:
            await asyncio.to_thread(remove)
        except Exception as error:
            log_integration_failure("community_media", "delete", error)
            raise MediaStorageError("community media deletion failed") from error

    async def create_read_url(self, key: str, expires_seconds: int) -> str:
        if not key.startswith("community-reports/") or ".." in key:
            raise ValueError("invalid community media object key")

        def sign() -> str:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )

        try:
            url = await asyncio.to_thread(sign)
        except Exception as error:
            log_integration_failure("community_media", "create_read_url", error)
            raise MediaStorageError("community media access failed") from error
        if urlparse(url).scheme != "https":
            raise MediaStorageError("community media access URL is not HTTPS")
        return url

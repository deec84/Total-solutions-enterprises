"""Push-provider adapters; production uses an authenticated gateway."""

import httpx

from app.modules.notifications.domain import PushDevice
from app.modules.observability.redaction import log_integration_failure


class HttpPushProvider:
    def __init__(self, endpoint: str, bearer_token: str) -> None:
        self._endpoint = endpoint
        self._bearer_token = bearer_token

    async def send(
        self, device: PushDevice, title: str, body: str, data: dict[str, str]
    ) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self._endpoint,
                    headers={"Authorization": f"Bearer {self._bearer_token}"},
                    json={
                        "token": device.token,
                        "platform": device.platform,
                        "notification": {"title": title, "body": body},
                        "data": data,
                    },
                )
        except httpx.HTTPError as error:
            log_integration_failure("push_gateway", "send_notification", error)
            return False
        delivered = 200 <= response.status_code < 300
        if not delivered:
            log_integration_failure(
                "push_gateway",
                "send_notification",
                RuntimeError("provider returned a non-success status"),
            )
        return delivered


class DisabledPushProvider:
    async def send(
        self, device: PushDevice, title: str, body: str, data: dict[str, str]
    ) -> bool:
        return False

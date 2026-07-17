"""Push-provider adapters; production uses an authenticated gateway."""

import httpx

from app.modules.notifications.domain import PushDevice


class HttpPushProvider:
    def __init__(self, endpoint: str, bearer_token: str) -> None:
        self._endpoint = endpoint
        self._bearer_token = bearer_token

    async def send(
        self, device: PushDevice, title: str, body: str, data: dict[str, str]
    ) -> bool:
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
        return 200 <= response.status_code < 300


class DisabledPushProvider:
    async def send(
        self, device: PushDevice, title: str, body: str, data: dict[str, str]
    ) -> bool:
        return False

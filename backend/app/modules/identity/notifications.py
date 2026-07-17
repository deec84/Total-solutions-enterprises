"""Production notification adapters for identity lifecycle messages."""

from email.message import EmailMessage
from urllib.parse import urlencode

import aiosmtplib


class SmtpVerificationNotifier:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        link_scheme: str = "parkshield",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._link_scheme = link_scheme

    async def send_email_verification(self, email: str, token: str) -> None:
        link = self._link("verify-email", token)
        await self._send(
            email,
            "Verify your ParkShield AI account",
            f"Verify your account using this secure link:\n\n{link}\n\n"
            "This link expires in 24 hours.",
        )

    async def send_password_reset(self, email: str, token: str) -> None:
        link = self._link("reset-password", token)
        await self._send(
            email,
            "Reset your ParkShield AI password",
            f"Reset your password using this secure link:\n\n{link}\n\n"
            "This link expires in 30 minutes.",
        )

    def _link(self, host: str, token: str) -> str:
        return f"{self._link_scheme}://{host}?{urlencode({'token': token})}"

    async def _send(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            start_tls=True,
            timeout=10,
        )

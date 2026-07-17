"""SMTP notification content tests without external network access."""

import asyncio
from email.message import EmailMessage
from unittest.mock import AsyncMock

import aiosmtplib
import pytest

from app.modules.identity.notifications import SmtpVerificationNotifier


def test_smtp_notifier_builds_safe_deep_links(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = AsyncMock()
    monkeypatch.setattr(aiosmtplib, "send", sent)
    notifier = SmtpVerificationNotifier(
        host="smtp.example.com",
        port=587,
        username="user",
        password="secret",
        sender="no-reply@parkshield.ai",
    )

    async def scenario() -> None:
        await notifier.send_email_verification("person@example.com", "a token")
        await notifier.send_password_reset("person@example.com", "reset token")

    asyncio.run(scenario())

    assert sent.await_count == 2
    messages = [call.args[0] for call in sent.await_args_list]
    assert all(isinstance(message, EmailMessage) for message in messages)
    assert "parkshield://verify-email?token=a+token" in messages[0].get_content()
    assert "parkshield://reset-password?token=reset+token" in messages[1].get_content()
    assert sent.await_args_list[0].kwargs["start_tls"] is True

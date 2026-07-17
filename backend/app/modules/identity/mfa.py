"""RFC 6238 compatible TOTP primitives."""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def provisioning_uri(secret: str, email: str) -> str:
    label = quote(f"ParkShield AI:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer=ParkShield%20AI&digits=6&period=30"


def totp(secret: str, timestamp: int | None = None) -> str:
    moment = int(time.time()) if timestamp is None else timestamp
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", moment // 30), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def verify_totp(secret: str, code: str, timestamp: int | None = None) -> bool:
    moment = int(time.time()) if timestamp is None else timestamp
    if len(code) != 6 or not code.isdigit():
        return False
    return any(
        hmac.compare_digest(totp(secret, moment + drift * 30), code)
        for drift in (-1, 0, 1)
    )


def _fernet(application_secret: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(application_secret.encode()).digest())
    return Fernet(key)


def encrypt_secret(secret: str, application_secret: str) -> str:
    return _fernet(application_secret).encrypt(secret.encode()).decode()


def decrypt_secret(ciphertext: str, application_secret: str) -> str:
    try:
        return _fernet(application_secret).decrypt(ciphertext.encode()).decode()
    except InvalidToken as error:
        raise ValueError("invalid encrypted MFA secret") from error

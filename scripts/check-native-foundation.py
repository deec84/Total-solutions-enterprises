"""Verify that the native foundation consumes only safe, versioned contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERROR_FIELDS = {"version", "code", "message", "correlation_id", "details"}
ALLOWED_DETAIL_CODES = {"MISSING_FIELD", "INVALID_FIELD"}
CORRELATION_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"native-foundation: {message}", file=sys.stderr)
    raise SystemExit(1)


def verify_fixture(path: Path) -> None:
    fixture = read_json(path)
    if set(fixture) - ERROR_FIELDS:
        fail(f"unexpected public error field in {path.relative_to(ROOT)}")
    if fixture.get("version") != "1" or not isinstance(fixture.get("code"), str):
        fail(f"invalid v1 error fixture {path.relative_to(ROOT)}")
    correlation_id = fixture.get("correlation_id")
    if not isinstance(correlation_id, str) or not CORRELATION_ID.fullmatch(
        correlation_id
    ):
        fail(f"invalid correlation_id in {path.relative_to(ROOT)}")
    for detail in fixture.get("details", []):
        if (
            not isinstance(detail, dict)
            or detail.get("code") not in ALLOWED_DETAIL_CODES
        ):
            fail(f"non-allowlisted error detail in {path.relative_to(ROOT)}")


def main() -> None:
    required = [
        ROOT / "contracts/openapi/parkshield-api.v1.json",
        ROOT / "contracts/design-tokens/parkshield-mobile.v1.json",
        ROOT
        / "apps/android/app/src/main/kotlin/ai/parkshield/android/core/network/ApiError.kt",
        ROOT / "apps/ios/Sources/ParkShieldFoundation/Core/Network/APIError.swift",
        ROOT / "apps/ios/Package.swift",
        ROOT / "apps/ios/ParkShield.xcodeproj/project.pbxproj",
    ]
    missing = [path.relative_to(ROOT) for path in required if not path.is_file()]
    if missing:
        fail(f"missing required foundation files: {', '.join(map(str, missing))}")

    for fixture in sorted((ROOT / "contracts/fixtures/errors").glob("*.json")):
        verify_fixture(fixture)

    login_fixture = read_json(ROOT / "contracts/fixtures/auth/login-success.v1.json")
    if not all(
        isinstance(login_fixture.get(name), str)
        and str(login_fixture[name]).startswith("synthetic-")
        for name in ("access_token", "refresh_token")
    ):
        fail("authentication fixture must contain synthetic placeholder tokens")
    profile_fixture = read_json(ROOT / "contracts/fixtures/auth/profile.v1.json")
    if not isinstance(profile_fixture.get("email"), str) or not str(
        profile_fixture["email"]
    ).endswith(".test"):
        fail("profile fixture must use a synthetic .test email address")

    for source_root in (ROOT / "apps/android", ROOT / "apps/ios"):
        for source in source_root.rglob("*"):
            if (
                source.suffix in {".kt", ".swift"}
                and "flutter" in source.read_text(encoding="utf-8").lower()
            ):
                fail(f"Flutter reference in native source: {source.relative_to(ROOT)}")

    print("Native mobile foundation contracts and architecture checks passed.")


if __name__ == "__main__":
    main()

"""Verify that the native foundation consumes safe, versioned, layered contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERROR_FIELDS = {"version", "code", "message", "correlation_id", "details"}
ALLOWED_DETAIL_CODES = {"MISSING_FIELD", "INVALID_FIELD"}
CORRELATION_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
LAYERS = frozenset({"presentation", "domain", "data", "core"})
ALLOWED_LAYER_DEPENDENCIES = {
    "presentation": frozenset({"presentation", "domain", "core"}),
    "domain": frozenset({"domain"}),
    "data": frozenset({"data", "domain", "core"}),
    "core": frozenset({"core"}),
}
KOTLIN_LAYER_REFERENCE = re.compile(
    r"\bfeature\.[A-Za-z0-9_]+\.(presentation|domain|data|core)\b"
)
SWIFT_LAYER_REFERENCE = re.compile(
    r"\b(?:Feature/[A-Za-z0-9_]+/(Presentation|Domain|Data|Core)|"
    r"ParkShield[A-Za-z0-9_]+(Presentation|Domain|Data|Core))\b"
)


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


def layer_for_source(path: Path) -> str | None:
    """Return a normalized feature layer for the Android and iOS source layouts."""
    parts = path.parts
    for index, part in enumerate(parts[:-1]):
        normalized = part.lower()
        if normalized == "feature" and index + 2 < len(parts):
            candidate = parts[index + 2].lower()
            return candidate if candidate in LAYERS else None
    return "core" if "core" in {part.lower() for part in parts} else None


def referenced_layers(source: str, suffix: str) -> set[str]:
    if suffix == ".kt":
        return set(KOTLIN_LAYER_REFERENCE.findall(source))
    if suffix == ".swift":
        matches = SWIFT_LAYER_REFERENCE.findall(source)
        return {next(value for value in match if value).lower() for match in matches}
    return set()


def layer_violations(path: Path, source: str) -> set[str]:
    """Return forbidden feature-layer references made by one source file."""
    source_layer = layer_for_source(path)
    if source_layer is None:
        return set()
    allowed = ALLOWED_LAYER_DEPENDENCIES[source_layer]
    return referenced_layers(source, path.suffix) - allowed


def verify_layer_dependencies(source_root: Path) -> None:
    for source in source_root.rglob("*"):
        if source.suffix not in {".kt", ".swift"}:
            continue
        violations = layer_violations(source, source.read_text(encoding="utf-8"))
        if violations:
            layers = ", ".join(sorted(violations))
            fail(f"forbidden layer dependency from {source.relative_to(ROOT)} to {layers}")


def ios_signing_violations(project: str) -> set[str]:
    forbidden = {
        "CODE_SIGN_STYLE",
        "CODE_SIGN_IDENTITY",
        "DEVELOPMENT_TEAM",
        "PROVISIONING_PROFILE",
        "PROVISIONING_PROFILE_SPECIFIER",
    }
    violations = {setting for setting in forbidden if setting in project}
    for setting in ("CODE_SIGNING_ALLOWED = NO", "CODE_SIGNING_REQUIRED = NO"):
        if setting not in project:
            violations.add(setting)
    return violations


def verify_ios_signing_configuration(project_path: Path) -> None:
    violations = ios_signing_violations(project_path.read_text(encoding="utf-8"))
    if violations:
        settings = ", ".join(sorted(violations))
        fail(f"iOS signing is not disabled in {project_path.relative_to(ROOT)}: {settings}")


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

    verify_ios_signing_configuration(ROOT / "apps/ios/ParkShield.xcodeproj/project.pbxproj")

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
        verify_layer_dependencies(source_root)

    print("Native mobile foundation contracts and architecture checks passed.")


if __name__ == "__main__":
    main()

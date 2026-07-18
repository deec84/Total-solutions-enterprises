#!/usr/bin/env python3
"""Fail closed when mobile catalogs or native locale metadata drift."""

from __future__ import annotations

import json
from pathlib import Path
from plistlib import load


ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"
LOCALES = {"en", "es"}
PRIVACY_KEYS = {
    "CFBundleDisplayName",
    "NSCameraUsageDescription",
    "NSPhotoLibraryUsageDescription",
    "NSLocationWhenInUseUsageDescription",
    "NSLocationAlwaysAndWhenInUseUsageDescription",
}


def catalog_keys(path: Path) -> set[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("@@locale") not in LOCALES:
        raise SystemExit(f"Unsupported or missing @@locale in {path}")
    return {key for key in document if not key.startswith("@")}


def strings_keys(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return {
        line.split("=", 1)[0].strip().strip('"')
        for line in lines
        if "=" in line and not line.lstrip().startswith("//")
    }


def main() -> None:
    english = catalog_keys(MOBILE / "lib/l10n/app_en.arb")
    spanish = catalog_keys(MOBILE / "lib/l10n/app_es.arb")
    if english != spanish:
        missing_es = sorted(english - spanish)
        missing_en = sorted(spanish - english)
        raise SystemExit(
            f"ARB catalogs differ; missing es={missing_es}, missing en={missing_en}"
        )

    with (MOBILE / "ios/Runner/Info.plist").open("rb") as plist_file:
        info = load(plist_file)
    if set(info.get("CFBundleLocalizations", [])) != LOCALES:
        raise SystemExit("Info.plist must declare exactly en and es localizations")

    for locale in LOCALES:
        path = MOBILE / f"ios/Runner/{locale}.lproj/InfoPlist.strings"
        missing = PRIVACY_KEYS - strings_keys(path)
        if missing:
            raise SystemExit(f"Missing native privacy strings in {path}: {sorted(missing)}")

    project = (MOBILE / "ios/Runner.xcodeproj/project.pbxproj").read_text(
        encoding="utf-8"
    )
    if "InfoPlist.strings in Resources" not in project or "name = es;" not in project:
        raise SystemExit("Localized InfoPlist.strings are not included in the iOS target")

    manifest = (MOBILE / "android/app/src/main/AndroidManifest.xml").read_text(
        encoding="utf-8"
    )
    if 'android:label="@string/app_name"' not in manifest:
        raise SystemExit("Android application label must use a localized resource")
    if 'android.permission.INTERNET' not in manifest:
        raise SystemExit("Android release manifest is missing INTERNET permission")
    for locale_path in ("values/strings.xml", "values-es/strings.xml"):
        path = MOBILE / "android/app/src/main/res" / locale_path
        if '<string name="app_name">ParkShield AI</string>' not in path.read_text(
            encoding="utf-8"
        ):
            raise SystemExit(f"Missing Android app_name in {path}")

    print(f"Mobile localization checks passed ({len(english)} messages; en, es).")


if __name__ == "__main__":
    main()

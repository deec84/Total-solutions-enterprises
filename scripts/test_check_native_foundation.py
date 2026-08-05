"""Unit tests for the native foundation layer-dependency guard."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check-native-foundation.py")
SPEC = importlib.util.spec_from_file_location("native_foundation_check", SCRIPT)
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class LayerDependencyTests(unittest.TestCase):
    def test_allows_presentation_to_domain_and_core(self) -> None:
        path = Path("apps/android/app/src/main/kotlin/ai/parkshield/android/feature/auth/presentation/Login.kt")
        source = "import ai.parkshield.android.feature.auth.domain.LoginUseCase\nimport ai.parkshield.android.feature.auth.core.Analytics"
        self.assertEqual(CHECK.layer_violations(path, source), set())

    def test_allows_data_to_domain_and_core(self) -> None:
        path = Path("apps/ios/Sources/ParkShieldFoundation/Feature/Auth/Data/AuthRepository.swift")
        source = "import ParkShieldAuthDomain\nimport ParkShieldAuthCore"
        self.assertEqual(CHECK.layer_violations(path, source), set())

    def test_rejects_presentation_to_data(self) -> None:
        path = Path("apps/android/app/src/main/kotlin/ai/parkshield/android/feature/auth/presentation/Login.kt")
        source = "import ai.parkshield.android.feature.auth.data.AuthRepository"
        self.assertEqual(CHECK.layer_violations(path, source), {"data"})

    def test_rejects_domain_to_core(self) -> None:
        path = Path("apps/ios/Sources/ParkShieldFoundation/Feature/Auth/Domain/Session.swift")
        source = "import ParkShieldAuthCore"
        self.assertEqual(CHECK.layer_violations(path, source), {"core"})

    def test_accepts_explicitly_disabled_ios_signing(self) -> None:
        project = "CODE_SIGNING_ALLOWED = NO; CODE_SIGNING_REQUIRED = NO;"
        self.assertEqual(CHECK.ios_signing_violations(project), set())

    def test_rejects_automatic_ios_signing(self) -> None:
        project = "CODE_SIGN_STYLE = Automatic; CODE_SIGNING_ALLOWED = NO; CODE_SIGNING_REQUIRED = NO;"
        self.assertEqual(CHECK.ios_signing_violations(project), {"CODE_SIGN_STYLE"})


if __name__ == "__main__":
    unittest.main()

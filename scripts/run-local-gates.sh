#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TOOLCHAINS="$REPOSITORY_ROOT/work/toolchains"

resolve_executable() {
  preferred_path=$1
  executable_name=$2
  if [ -x "$preferred_path" ]; then
    printf '%s\n' "$preferred_path"
    return
  fi
  if resolved_path=$(command -v "$executable_name" 2>/dev/null); then
    printf '%s\n' "$resolved_path"
    return
  fi
  printf 'Required tool is missing: %s\n' "$executable_name" >&2
  exit 1
}

PYTHON=$(resolve_executable "$REPOSITORY_ROOT/backend/.venv/bin/python" python3)
FLUTTER=$(resolve_executable "$TOOLCHAINS/flutter/bin/flutter" flutter)
DART=$(resolve_executable "$TOOLCHAINS/flutter/bin/dart" dart)
TERRAFORM=$(resolve_executable "$TOOLCHAINS/terraform-bin/terraform" terraform)
TRIVY=$(resolve_executable "$TOOLCHAINS/trivy/trivy" trivy)
ACTIONLINT=$(resolve_executable "$TOOLCHAINS/actionlint/actionlint" actionlint)

mkdir -p \
  "$TOOLCHAINS/config/flutter" \
  "$TOOLCHAINS/cache" \
  "$TOOLCHAINS/pub-cache" \
  "$TOOLCHAINS/gradle-cache" \
  "$TOOLCHAINS/android-user-home"

local_java_home="$TOOLCHAINS/jdk17/jdk-17.0.19+10/Contents/Home"
if [ -x "$local_java_home/bin/java" ]; then
  JAVA_HOME="$local_java_home"
  export JAVA_HOME
fi

local_android_sdk="$TOOLCHAINS/android-sdk"
if [ -d "$local_android_sdk" ]; then
  ANDROID_SDK_ROOT="$local_android_sdk"
  ANDROID_HOME="$local_android_sdk"
  export ANDROID_SDK_ROOT ANDROID_HOME
fi

export ANDROID_USER_HOME="$TOOLCHAINS/android-user-home"
export GRADLE_USER_HOME="$TOOLCHAINS/gradle-cache"
export XDG_CONFIG_HOME="$TOOLCHAINS/config"
export XDG_CACHE_HOME="$TOOLCHAINS/cache"
export PUB_CACHE="$TOOLCHAINS/pub-cache"
export PATH="$TOOLCHAINS/bin:$TOOLCHAINS/flutter/bin:$PATH"

printf '\nRepository onboarding and secret-exclusion gate\n'
"$REPOSITORY_ROOT/scripts/check-repository-readiness.sh"
"$PYTHON" "$REPOSITORY_ROOT/scripts/check-mobile-localizations.py"
"$PYTHON" "$REPOSITORY_ROOT/scripts/check-observability-contracts.py"

printf '\nBackend static, security, authentication, and coverage gates\n'
cd "$REPOSITORY_ROOT/backend"
"$PYTHON" -m ruff check .
"$PYTHON" -m mypy app
"$PYTHON" -m bandit -r app -ll
"$PYTHON" -m pip_audit --cache-dir "$TOOLCHAINS/pip-audit-cache"

# The focused fixture regression is intentionally run without partial-suite
# coverage. The immediately following full suite enforces the unchanged 90% gate.
"$PYTHON" -m pytest tests/test_auth.py -q --no-cov
"$PYTHON" -m pytest -q
"$PYTHON" -m alembic heads
"$PYTHON" -m alembic upgrade head --sql >/dev/null

printf '\nFlutter analysis, rendering tests, coverage, and Android build\n'
cd "$REPOSITORY_ROOT/mobile"
"$FLUTTER" pub get
"$FLUTTER" gen-l10n
git diff --exit-code -- lib/l10n/generated
"$DART" format --output=none --set-exit-if-changed lib test
"$FLUTTER" analyze --fatal-infos
"$FLUTTER" test --coverage
"$REPOSITORY_ROOT/scripts/check-flutter-coverage.sh" coverage/lcov.info 75
"$FLUTTER" build apk --debug

printf '\nInfrastructure and workflow gates\n'
cd "$REPOSITORY_ROOT/infrastructure/terraform"
"$TERRAFORM" fmt -check -recursive
"$TERRAFORM" init -backend=false -input=false
"$TERRAFORM" validate
"$TRIVY" config \
  --severity HIGH,CRITICAL \
  --exit-code 1 \
  --cache-dir "$TOOLCHAINS/trivy-cache" \
  .

cd "$REPOSITORY_ROOT"
"$ACTIONLINT" -no-color .github/workflows/*.yml
"$PYTHON" - <<'PY'
from pathlib import Path
from plistlib import load

with Path("mobile/ios/ExportOptions.plist").open("rb") as plist_file:
    load(plist_file)
print("mobile/ios/ExportOptions.plist: OK")
PY

printf '\nAll locally executable ParkShield gates passed.\n'
printf '%s\n' 'Hosted PostGIS, container, iOS, CodeQL, secret-scan, cloud, and signed-release gates remain mandatory.'

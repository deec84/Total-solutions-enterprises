#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

required_files='
.env.example
.gitattributes
.gitignore
README.md
SECURITY.md
backend/Dockerfile
docker-compose.yml
docs/environment-variables.md
docs/external-services.md
docs/installation.md
docs/repository-onboarding.md
infrastructure/terraform/.terraform.lock.hcl
infrastructure/terraform/production.tfvars.example
mobile/android/gradle/wrapper/gradle-wrapper.jar
mobile/android/gradle/wrapper/gradle-wrapper.properties
mobile/android/gradlew
mobile/android/gradlew.bat
mobile/android/app/src/main/res/values/strings.xml
mobile/android/app/src/main/res/values-es/strings.xml
mobile/ios/Runner/en.lproj/InfoPlist.strings
mobile/ios/Runner/es.lproj/InfoPlist.strings
mobile/lib/l10n/app_en.arb
mobile/lib/l10n/app_es.arb
mobile/pubspec.lock
'

for relative_path in $required_files; do
  if [ ! -f "$REPOSITORY_ROOT/$relative_path" ]; then
    printf 'Required repository file is missing: %s\n' "$relative_path" >&2
    exit 1
  fi
done

temporary_git_directory=$(mktemp -d)
cleanup() {
  rm -rf "$temporary_git_directory"
}
trap cleanup EXIT HUP INT TERM

git --git-dir="$temporary_git_directory" init --bare -q

must_be_ignored='
.env
.env.local
.env.production
backend/.env
infrastructure/terraform/staging.tfvars
infrastructure/terraform/production.tfvars
infrastructure/terraform/staging.tfplan
infrastructure/terraform/terraform.tfstate
mobile/android/key.properties
mobile/android/app/upload-keystore.jks
mobile/ios/distribution.p12
mobile/ios/profile.mobileprovision
mobile/android/app/google-services.json
mobile/ios/Runner/GoogleService-Info.plist
firebase-adminsdk-service-account.json
mobile/build/app-release.aab
outputs/release.apk
work/toolchains/flutter/bin/flutter
'

for relative_path in $must_be_ignored; do
  if ! git --git-dir="$temporary_git_directory" \
    --work-tree="$REPOSITORY_ROOT" \
    check-ignore --no-index -q "$relative_path"
  then
    printf 'Sensitive or generated path is not ignored: %s\n' "$relative_path" >&2
    exit 1
  fi
done

must_be_trackable='
.env.example
.gitattributes
.github/workflows/quality.yml
docker-compose.yml
infrastructure/terraform/.terraform.lock.hcl
mobile/android/gradle/wrapper/gradle-wrapper.jar
mobile/android/gradlew
mobile/pubspec.lock
'

for relative_path in $must_be_trackable; do
  if git --git-dir="$temporary_git_directory" \
    --work-tree="$REPOSITORY_ROOT" \
    check-ignore --no-index -q "$relative_path"
  then
    printf 'Required source file is unexpectedly ignored: %s\n' "$relative_path" >&2
    exit 1
  fi
done

git --git-dir="$temporary_git_directory" \
  --work-tree="$REPOSITORY_ROOT" \
  add --all
git --git-dir="$temporary_git_directory" \
  --work-tree="$REPOSITORY_ROOT" \
  diff --cached --check

if git --git-dir="$temporary_git_directory" \
  --work-tree="$REPOSITORY_ROOT" \
  grep --cached -I -n -E \
  '(AKIA|ASIA)[A-Z0-9]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{20,}|AIza[0-9A-Za-z_-]{30,}'
then
  printf 'A trackable file contains a high-confidence credential pattern.\n' >&2
  exit 1
fi

git --git-dir="$temporary_git_directory" \
  --work-tree="$REPOSITORY_ROOT" \
  ls-files |
while IFS= read -r relative_path; do
  byte_count=$(wc -c < "$REPOSITORY_ROOT/$relative_path" | tr -d ' ')
  if [ "$byte_count" -gt 50000000 ]; then
    printf 'Trackable file exceeds the 50 MB repository limit: %s (%s bytes)\n' \
      "$relative_path" "$byte_count" >&2
    exit 1
  fi
done

printf 'Repository readiness checks passed.\n'

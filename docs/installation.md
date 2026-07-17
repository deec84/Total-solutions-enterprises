# Installation and local development

## Supported tools

Use these baselines for a clean clone:

- Git 2.39 or newer.
- Docker Engine/Desktop 24 or newer with Docker Compose v2.
- Python 3.12 for native backend development.
- Flutter 3.44.6 with its bundled Dart SDK.
- JDK 17 and an Android SDK with target/API 36 for Android builds.
- Full Xcode on macOS for iOS builds. The project uses Flutter's Swift Package Manager integration; CocoaPods is not required by the checked-in iOS project.
- Terraform 1.12.2, Trivy, and Actionlint for the complete local gate set.

Only Docker and Compose are required to run the backend and PostGIS stack. Native mobile and infrastructure work require their corresponding tools.

## Configure local values

From the repository root:

```sh
cp .env.example .env
```

Generate distinct local values for the database password and JWT signing key. This command prints values for manual insertion into `.env`; it does not modify a file:

```sh
python3 - <<'PY'
import secrets

print("database password:", secrets.token_urlsafe(24))
print("JWT secret:", secrets.token_urlsafe(48))
PY
```

Replace both occurrences of the database-password placeholder with the same generated value. Replace the JWT placeholder with the other value. `.env` is ignored by Git; verify that before any commit.

Local SMTP, push, and tow-provider values may remain empty. Staging and production reject missing provider configuration.

## Start PostgreSQL/PostGIS and the API

Validate the rendered configuration, build the API image, apply Alembic migrations, and start the stack:

```sh
docker compose config --quiet
make up
make verify-stack
```

The `migrate` service must complete successfully before the API starts. Migration `0001_identity_schema` creates the PostGIS extension, and subsequent migrations create the application schema.

Local endpoints:

- API: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- Liveness: `http://127.0.0.1:8000/api/v1/health/live`
- Readiness: `http://127.0.0.1:8000/api/v1/health/ready`
- PostgreSQL: `127.0.0.1:5432`

Both published ports bind to loopback only. Change the host ports in `.env` if they conflict with another local service.

Useful commands:

```sh
make logs
make verify-stack
make down
```

`make down` preserves the named database volume. `docker compose down --volumes` permanently deletes the local database and should be used only when that deletion is intentional.

## Run the backend natively

Keep the Compose PostgreSQL service running, then use a native virtual environment:

```sh
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
export PARKSHIELD_DATABASE_URL='postgresql+asyncpg://parkshield:<LOCAL_DB_PASSWORD>@127.0.0.1:5432/parkshield'
alembic upgrade head
uvicorn app.main:create_app --factory --reload
```

Do not paste a shared, staging, or production password into shell history. The inline value above is only a named placeholder for a local credential.

## Run the Flutter application

```sh
cd mobile
flutter pub get
flutter analyze --fatal-infos
flutter test --coverage
../scripts/check-flutter-coverage.sh coverage/lcov.info 75
```

For an iOS simulator or desktop-local target:

```sh
flutter run \
  --dart-define=PARKSHIELD_API_BASE_URL=http://127.0.0.1:8000
```

For the standard Android emulator, use `http://10.0.2.2:8000` because emulator loopback does not address the host. A physical device requires a development HTTPS endpoint or an explicitly secured local-network setup.

The public OpenStreetMap tile template is development-only. Release builds fail validation unless an HTTPS contracted tile template is supplied.

## Run the complete local gates

Create the backend virtual environment and install the tools listed above, then run:

```sh
make repository-check
make validate
```

The validation script uses pinned tools under ignored `work/toolchains/` when present and otherwise resolves tools from the system `PATH`. Hosted PostGIS integration, Compose smoke, container, iOS, CodeQL, Gitleaks, cloud, and signed-release jobs remain mandatory even when local gates pass.

## Troubleshooting

- If the API stays unhealthy, inspect `docker compose logs migrate api postgres`.
- If PostGIS is missing, confirm that the image is `postgis/postgis:16-3.4-alpine` and rerun migrations; do not substitute plain PostgreSQL.
- If Android cannot reach the API, verify the emulator URL and that host port 8000 is available.
- If a production-like configuration fails startup, read the validation error and fix the corresponding provider or TLS value; do not change the fail-closed validator to bypass it.

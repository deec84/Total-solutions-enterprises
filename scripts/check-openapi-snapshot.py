"""Fail when the checked-in public OpenAPI contract drifts from the backend."""

import json
from pathlib import Path

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "contracts" / "openapi" / "parkshield-api.v1.json"


def main() -> int:
    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    actual = create_app().openapi()
    if actual != expected:
        print("OpenAPI snapshot drift detected. Run scripts/export-openapi.py and review the diff.")
        return 1
    print("OpenAPI snapshot matches the public API contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

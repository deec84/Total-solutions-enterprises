"""Export the versioned public OpenAPI snapshot without starting the service."""

from __future__ import annotations

import json
from pathlib import Path

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "contracts" / "openapi" / "parkshield-api.v1.json"


def main() -> None:
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(
        json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

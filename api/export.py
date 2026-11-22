"""Write the OpenAPI document to api/openapi.json:  python -m api.export

The file is committed, and a test fails when it no longer matches the code, so the
published API reference can never quietly drift from the real API.
"""
import json
from pathlib import Path

from api.main import create_app

OPENAPI_PATH = Path(__file__).parent / "openapi.json"


def openapi_text():
    return json.dumps(create_app().openapi(), indent=2, ensure_ascii=False) + "\n"


def main():
    OPENAPI_PATH.write_text(openapi_text(), encoding="utf-8")
    print(f"wrote {OPENAPI_PATH.name}")


if __name__ == "__main__":
    main()

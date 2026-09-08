#!/usr/bin/env python3
"""Small, defensive client for the local CM generation API."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


class CMApiError(RuntimeError):
    """Raised when the local CM API is unavailable or returns invalid data."""


def fetch_cm_data(api_url: str, date: str, background: str | None = None) -> dict[str, Any]:
    """Generate a CM and return a validated JSON response."""
    try:
        response = requests.post(
            api_url,
            json={"date": date, "background": background},
            timeout=130,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        raise CMApiError(f"[HTTPエラー] サーバーがHTTP {error.response.status_code}を返しました。") from error
    except requests.exceptions.RequestException as error:
        raise CMApiError(
            "[通信エラー] local_server.py が起動していない可能性があります。"
        ) from error

    content_type = response.headers.get("Content-Type", "").lower()
    body = response.text.strip()
    if "application/json" not in content_type and not body.startswith("{"):
        raise CMApiError(
            "[エラー] サーバーから不正なデータ（HTML等）が返されました。"
            " local_server.py の起動状態とURLを確認してください。"
        )

    try:
        result = response.json()
    except (ValueError, json.JSONDecodeError) as error:
        raise CMApiError(
            "[エラー] 受信したデータが正しいJSON形式ではありません。"
        ) from error
    if not isinstance(result, dict):
        raise CMApiError("[エラー] APIのJSON応答がオブジェクト形式ではありません。")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Call the local CM generation API.")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/generate")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--background", default="cm_space_planets.jpeg", help="Bundled background filename")
    args = parser.parse_args()
    try:
        print(json.dumps(fetch_cm_data(args.url, args.date, args.background), ensure_ascii=False, indent=2))
    except CMApiError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json


class Web2MDError(Exception):
    """An error from the Web2MD API, the RapidAPI gateway, or the network."""

    def __init__(self, code: str, message: str, status: int | None) -> None:
        super().__init__(f"{code} ({status}): {message}" if status else f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status


def _gateway_code(status: int) -> str:
    if status in (401, 403):
        return "rapidapi_auth"
    if status == 429:
        return "rapidapi_rate_limited"
    return "http_error"


def error_from_response(status: int, body_text: str) -> Web2MDError:
    try:
        data = json.loads(body_text) if body_text else None
    except ValueError:
        data = None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            return Web2MDError(
                str(err.get("code") or "unknown_error"), str(err.get("message") or ""), status
            )
        if isinstance(data.get("message"), str):
            return Web2MDError(_gateway_code(status), data["message"], status)
    return Web2MDError(_gateway_code(status), body_text.strip()[:300] or f"HTTP {status}", status)

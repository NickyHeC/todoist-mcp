# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Todoist REST request dispatch and response helpers.

Todoist uses a standard REST API with JSON request/response bodies.
All endpoints live under ``/api/v1/`` (included in the Connection base_url).

Functions:
  api_request(method, path, ...)  -- dispatch REST request via Dedalus enclave

Coercion helpers (safe extraction from untyped API dicts):
  _str(val, default)         -- coerce to str
  _int(val, default)         -- coerce to int
  _opt_str(val)              -- coerce to str | None
  _bool(val, *, default)     -- coerce to bool
  _list_str(val)             -- coerce to list[str]
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from dedalus_mcp import HttpMethod, HttpRequest, get_context

from todoist.config import todoist
from todoist.types import TodoistResult


# --- REST dispatch ---


async def api_request(
    method: HttpMethod,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> TodoistResult:
    """Execute a Todoist REST request via the Dedalus enclave.

    All Todoist API interaction goes through this single function.
    Query parameters are URL-encoded and appended to the path.
    Error responses (JSON with ``error`` key) are surfaced as
    ``TodoistResult(success=False)``.

    Args:
        method: HTTP method (GET, POST, DELETE).
        path: API path relative to the connection base_url.
        body: Optional JSON body for POST requests.
        params: Optional query parameters. None values are filtered out.

    Returns:
        TodoistResult wrapping the response data or error.

    """
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            path = f"{path}?{urlencode(clean)}"

    ctx = get_context()
    req = HttpRequest(method=method, path=path, body=body)
    resp = await ctx.dispatch(todoist, req)

    if resp.success and resp.response is not None:
        resp_body = resp.response.body
        if isinstance(resp_body, dict) and "error" in resp_body:
            return TodoistResult(
                success=False,
                error=str(resp_body.get("error", "API error")),
            )
        return TodoistResult(success=True, data=resp_body)

    error = resp.error.message if resp.error else "Request failed"
    return TodoistResult(success=False, error=error)


# --- Coercion helpers (safe extraction from untyped API dicts) ---


def _str(val: Any, default: str = "") -> str:  # noqa: ANN401 — raw JSON extraction
    """Safely coerce to string."""
    return str(val) if val is not None else default


def _int(val: Any, default: int = 0) -> int:  # noqa: ANN401 — raw JSON extraction
    """Safely coerce to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _opt_str(val: Any) -> str | None:  # noqa: ANN401 — raw JSON extraction
    """Safely coerce to optional string."""
    return str(val) if val is not None else None


def _bool(val: Any, *, default: bool = False) -> bool:  # noqa: ANN401 — raw JSON extraction
    """Safely coerce to bool."""
    return bool(val) if val is not None else default


def _list_str(val: Any) -> list[str]:  # noqa: ANN401 — raw JSON extraction
    """Safely coerce to list of strings."""
    if isinstance(val, list):
        return [str(item) for item in val if item is not None]
    return []

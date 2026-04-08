# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Label tools.

Tools:
  todoist_get_labels     -- list all personal labels
  todoist_create_label   -- create a new personal label
  todoist_search_labels  -- search labels by name
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from todoist.request import _bool, _int, _opt_str, _str, api_request
from todoist.types import JSONObject, LabelInfo, TodoistResult


# --- Helpers ---


def _parse_label(raw: JSONObject) -> LabelInfo:
    """Parse a raw label dict into a LabelInfo.

    Args:
        raw: Untyped label object from the REST response.

    Returns:
        Parsed LabelInfo with coerced fields.

    """
    return LabelInfo(
        id=_str(raw.get("id")),
        name=_str(raw.get("name")),
        color=_opt_str(raw.get("color")),
        order=_int(raw.get("order")),
        is_favorite=_bool(raw.get("is_favorite")),
    )


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_labels(
    limit: int = 50,
    cursor: str | None = None,
) -> list[LabelInfo] | str:
    """List all personal labels.

    Args:
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of LabelInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {"limit": limit, "cursor": cursor}
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/labels", params=params,
    )
    if not response.success:
        return response.error or "Failed to fetch labels"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_label(item) for item in results if isinstance(item, dict)]


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_create_label(
    name: str,
    color: str | None = None,
    order: int | None = None,
    is_favorite: bool | None = None,
) -> LabelInfo | str:
    """Create a new personal label.

    Args:
        name: Label name.
        color: Color name (e.g. ``berry_red``, ``blue``). Optional.
        order: Sort order among labels. Optional.
        is_favorite: Pin to favorites. Optional.

    Returns:
        Created LabelInfo, or an error string on failure.

    """
    body: dict[str, Any] = {"name": name}
    if color is not None:
        body["color"] = color
    if order is not None:
        body["order"] = order
    if is_favorite is not None:
        body["is_favorite"] = is_favorite

    response: TodoistResult = await api_request(
        HttpMethod.POST, "/labels", body=body,
    )
    if not response.success:
        return response.error or "Failed to create label"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_label(data)


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_search_labels(query: str) -> list[LabelInfo] | str:
    """Search labels by name.

    Supports wildcard matching with ``*`` character.

    Args:
        query: Search query with optional wildcards (e.g. ``"work*"``).

    Returns:
        List of matching LabelInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {"query": query}
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/labels/search", params=params,
    )
    if not response.success:
        return response.error or "Failed to search labels"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_label(item) for item in results if isinstance(item, dict)]


label_tools = [
    todoist_get_labels,
    todoist_create_label,
    todoist_search_labels,
]

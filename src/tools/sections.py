# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Section tools.

Tools:
  todoist_get_sections    -- list sections, optionally filtered by project
  todoist_create_section  -- create a new section in a project
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from todoist.request import _int, _str, api_request
from todoist.types import JSONObject, SectionInfo, TodoistResult


# --- Helpers ---


def _parse_section(raw: JSONObject) -> SectionInfo:
    """Parse a raw section dict into a SectionInfo.

    Args:
        raw: Untyped section object from the REST response.

    Returns:
        Parsed SectionInfo with coerced fields.

    """
    return SectionInfo(
        id=_str(raw.get("id")),
        name=_str(raw.get("name")),
        project_id=_str(raw.get("project_id")),
        order=_int(raw.get("order")),
    )


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_sections(
    project_id: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> list[SectionInfo] | str:
    """List sections, optionally filtered by project.

    Args:
        project_id: Filter by project ID. Optional.
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of SectionInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {
        "project_id": project_id,
        "limit": limit,
        "cursor": cursor,
    }
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/sections", params=params,
    )
    if not response.success:
        return response.error or "Failed to fetch sections"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_section(item) for item in results if isinstance(item, dict)]


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_create_section(
    name: str,
    project_id: str,
    order: int | None = None,
) -> SectionInfo | str:
    """Create a new section in a project.

    Args:
        name: Section name.
        project_id: Project ID to add the section to.
        order: Position within the project. Optional.

    Returns:
        Created SectionInfo, or an error string on failure.

    """
    body: dict[str, Any] = {"name": name, "project_id": project_id}
    if order is not None:
        body["order"] = order

    response: TodoistResult = await api_request(
        HttpMethod.POST, "/sections", body=body,
    )
    if not response.success:
        return response.error or "Failed to create section"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_section(data)


section_tools = [
    todoist_get_sections,
    todoist_create_section,
]

# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Project tools.

Tools:
  todoist_get_projects     -- list all active projects
  todoist_get_project      -- get a single project by ID
  todoist_create_project   -- create a new project
  todoist_update_project   -- update an existing project
  todoist_delete_project   -- delete a project
  todoist_search_projects  -- search projects by name
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from todoist.request import _bool, _opt_str, _str, api_request
from todoist.types import JSONObject, ProjectInfo, TodoistResult


# --- Helpers ---


def _parse_project(raw: JSONObject) -> ProjectInfo:
    """Parse a raw project dict into a ProjectInfo.

    Args:
        raw: Untyped project object from the REST response.

    Returns:
        Parsed ProjectInfo with coerced fields.

    """
    return ProjectInfo(
        id=_str(raw.get("id")),
        name=_str(raw.get("name")),
        color=_opt_str(raw.get("color")),
        is_shared=_bool(raw.get("is_shared")),
        is_favorite=_bool(raw.get("is_favorite")),
        is_inbox_project=_bool(raw.get("is_inbox_project")),
        view_style=_opt_str(raw.get("view_style")),
    )


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_projects(
    limit: int = 50,
    cursor: str | None = None,
) -> list[ProjectInfo] | str:
    """List all active projects.

    Returns a paginated list of all projects the user has access to.

    Args:
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of ProjectInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {"limit": limit, "cursor": cursor}
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/projects", params=params,
    )
    if not response.success:
        return response.error or "Failed to fetch projects"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_project(item) for item in results if isinstance(item, dict)]


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_project(project_id: str) -> ProjectInfo | str:
    """Get a single project by ID.

    Args:
        project_id: The project ID.

    Returns:
        ProjectInfo with full detail, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.GET, f"/projects/{project_id}",
    )
    if not response.success:
        return response.error or "Failed to fetch project"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_project(data)


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_create_project(
    name: str,
    color: str | None = None,
    is_favorite: bool | None = None,
    view_style: str | None = None,
    parent_id: str | None = None,
) -> ProjectInfo | str:
    """Create a new project.

    Args:
        name: Project name.
        color: Color name (e.g. ``berry_red``, ``blue``). Optional.
        is_favorite: Pin to favorites. Optional.
        view_style: Layout — ``list`` or ``board``. Optional.
        parent_id: Parent project ID to create as sub-project. Optional.

    Returns:
        Created ProjectInfo, or an error string on failure.

    """
    body: dict[str, Any] = {"name": name}
    if color is not None:
        body["color"] = color
    if is_favorite is not None:
        body["is_favorite"] = is_favorite
    if view_style is not None:
        body["view_style"] = view_style
    if parent_id is not None:
        body["parent_id"] = parent_id

    response: TodoistResult = await api_request(
        HttpMethod.POST, "/projects", body=body,
    )
    if not response.success:
        return response.error or "Failed to create project"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_project(data)


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_update_project(
    project_id: str,
    name: str | None = None,
    color: str | None = None,
    is_favorite: bool | None = None,
    view_style: str | None = None,
) -> ProjectInfo | str:
    """Update an existing project.

    Only provided fields are modified; omitted fields are left unchanged.

    Args:
        project_id: The project ID to update.
        name: New project name. Optional.
        color: New color name. Optional.
        is_favorite: Pin/unpin from favorites. Optional.
        view_style: New layout — ``list`` or ``board``. Optional.

    Returns:
        Updated ProjectInfo, or an error string on failure.

    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if color is not None:
        body["color"] = color
    if is_favorite is not None:
        body["is_favorite"] = is_favorite
    if view_style is not None:
        body["view_style"] = view_style

    if not body:
        return "No fields to update"

    response: TodoistResult = await api_request(
        HttpMethod.POST, f"/projects/{project_id}", body=body,
    )
    if not response.success:
        return response.error or "Failed to update project"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_project(data)


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_delete_project(project_id: str) -> str:
    """Delete a project and all its tasks.

    This action cannot be undone. All tasks, sections, and comments
    within the project are permanently deleted.

    Args:
        project_id: The project ID to delete.

    Returns:
        Confirmation message, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.DELETE, f"/projects/{project_id}",
    )
    if not response.success:
        return response.error or "Failed to delete project"
    return "Project deleted successfully"


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_search_projects(query: str) -> list[ProjectInfo] | str:
    """Search projects by name.

    Supports wildcard matching with ``*`` character.

    Args:
        query: Search query with optional wildcards (e.g. ``"Work*"``).

    Returns:
        List of matching ProjectInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {"query": query}
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/projects/search", params=params,
    )
    if not response.success:
        return response.error or "Failed to search projects"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_project(item) for item in results if isinstance(item, dict)]


project_tools = [
    todoist_get_projects,
    todoist_get_project,
    todoist_create_project,
    todoist_update_project,
    todoist_delete_project,
    todoist_search_projects,
]

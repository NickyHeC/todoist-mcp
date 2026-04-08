# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Comment tools.

Tools:
  todoist_get_comments    -- list comments for a task or project
  todoist_create_comment  -- add a comment to a task or project
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from todoist.request import _opt_str, _str, api_request
from todoist.types import CommentInfo, JSONObject, TodoistResult


# --- Helpers ---


def _parse_comment(raw: JSONObject) -> CommentInfo:
    """Parse a raw comment dict into a CommentInfo.

    Args:
        raw: Untyped comment object from the REST response.

    Returns:
        Parsed CommentInfo with coerced fields.

    """
    return CommentInfo(
        id=_str(raw.get("id")),
        content=_str(raw.get("content")),
        task_id=_opt_str(raw.get("task_id")),
        project_id=_opt_str(raw.get("project_id")),
        posted_at=_opt_str(raw.get("posted_at")),
    )


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_comments(
    task_id: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> list[CommentInfo] | str:
    """List comments for a task or project.

    Exactly one of ``task_id`` or ``project_id`` must be provided.

    Args:
        task_id: Task ID to fetch comments for. Optional.
        project_id: Project ID to fetch comments for. Optional.
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of CommentInfo objects, or an error string on failure.

    """
    if not task_id and not project_id:
        return "Either task_id or project_id is required"

    params: dict[str, Any] = {
        "task_id": task_id,
        "project_id": project_id,
        "limit": limit,
        "cursor": cursor,
    }
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/comments", params=params,
    )
    if not response.success:
        return response.error or "Failed to fetch comments"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_comment(item) for item in results if isinstance(item, dict)]


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_create_comment(
    content: str,
    task_id: str | None = None,
    project_id: str | None = None,
) -> CommentInfo | str:
    """Add a comment to a task or project.

    Exactly one of ``task_id`` or ``project_id`` must be provided.
    Content supports markdown formatting.

    Args:
        content: Comment body in markdown.
        task_id: Task ID to comment on. Optional.
        project_id: Project ID to comment on. Optional.

    Returns:
        Created CommentInfo, or an error string on failure.

    """
    if not task_id and not project_id:
        return "Either task_id or project_id is required"

    body: dict[str, Any] = {"content": content}
    if task_id is not None:
        body["task_id"] = task_id
    if project_id is not None:
        body["project_id"] = project_id

    response: TodoistResult = await api_request(
        HttpMethod.POST, "/comments", body=body,
    )
    if not response.success:
        return response.error or "Failed to create comment"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_comment(data)


comment_tools = [
    todoist_get_comments,
    todoist_create_comment,
]

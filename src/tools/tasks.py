# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Task tools.

Tools:
  todoist_get_tasks            -- list active tasks with optional filters
  todoist_get_task             -- get a single task by ID
  todoist_create_task          -- create a new task
  todoist_update_task          -- update an existing task
  todoist_close_task           -- complete a task
  todoist_reopen_task          -- reopen a completed task
  todoist_delete_task          -- delete a task
  todoist_move_task            -- move task to another project/section/parent
  todoist_quick_add_task       -- add task using natural language Quick Add syntax
  todoist_get_tasks_by_filter  -- get tasks matching a Todoist filter query
  todoist_get_completed_tasks  -- get completed tasks by completion date range
"""

from __future__ import annotations

from typing import Any

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from todoist.request import _bool, _int, _list_str, _opt_str, _str, api_request
from todoist.types import (
    DeadlineInfo,
    DueInfo,
    JSONObject,
    TaskInfo,
    TodoistResult,
)


# --- Helpers ---


def _parse_due(raw: Any) -> DueInfo | None:  # noqa: ANN401 — raw JSON extraction
    """Parse a due date object from the API response."""
    if not isinstance(raw, dict):
        return None
    return DueInfo(
        date=_str(raw.get("date")),
        string=_opt_str(raw.get("string")),
        is_recurring=_bool(raw.get("is_recurring")),
        timezone=_opt_str(raw.get("timezone")),
        lang=_opt_str(raw.get("lang")),
    )


def _parse_deadline(raw: Any) -> DeadlineInfo | None:  # noqa: ANN401 — raw JSON extraction
    """Parse a deadline object from the API response."""
    if not isinstance(raw, dict):
        return None
    return DeadlineInfo(
        date=_str(raw.get("date")),
        lang=_opt_str(raw.get("lang")),
    )


def _parse_task(raw: JSONObject) -> TaskInfo:
    """Parse a raw task dict into a TaskInfo.

    Args:
        raw: Untyped task object from the REST response.

    Returns:
        Parsed TaskInfo with coerced fields.

    """
    return TaskInfo(
        id=_str(raw.get("id")),
        content=_str(raw.get("content")),
        project_id=_str(raw.get("project_id")),
        description=_opt_str(raw.get("description")),
        section_id=_opt_str(raw.get("section_id")),
        parent_id=_opt_str(raw.get("parent_id")),
        labels=_list_str(raw.get("labels")),
        priority=_int(raw.get("priority"), default=1),
        due=_parse_due(raw.get("due")),
        deadline=_parse_deadline(raw.get("deadline")),
        checked=_bool(raw.get("checked")),
        added_at=_opt_str(raw.get("added_at")),
        completed_at=_opt_str(raw.get("completed_at")),
        updated_at=_opt_str(raw.get("updated_at")),
    )


def _parse_task_list(data: Any) -> list[TaskInfo] | str:  # noqa: ANN401 — raw JSON extraction
    """Parse a paginated task list response.

    Expects ``{"results": [...], "next_cursor": ...}``.
    """
    if not isinstance(data, dict):
        return "Unexpected response"
    results = data.get("results", [])
    if not isinstance(results, list):
        return "Unexpected results format"
    return [_parse_task(item) for item in results if isinstance(item, dict)]


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_tasks(
    project_id: str | None = None,
    section_id: str | None = None,
    parent_id: str | None = None,
    label: str | None = None,
    ids: list[str] | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> list[TaskInfo] | str:
    """List active tasks with optional filters.

    Returns a paginated list of active (non-completed) tasks. Combine filters
    to narrow results: by project, section, parent task, label name, or
    specific IDs.

    Args:
        project_id: Filter by project ID.
        section_id: Filter by section ID.
        parent_id: Filter by parent task ID (for subtasks).
        label: Filter by label name.
        ids: Filter by specific task IDs.
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of TaskInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {
        "project_id": project_id,
        "section_id": section_id,
        "parent_id": parent_id,
        "label": label,
        "limit": limit,
        "cursor": cursor,
    }
    if ids:
        params["ids"] = ",".join(ids)

    response: TodoistResult = await api_request(
        HttpMethod.GET, "/tasks", params=params,
    )
    if not response.success:
        return response.error or "Failed to fetch tasks"
    return _parse_task_list(response.data)


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_task(task_id: str) -> TaskInfo | str:
    """Get a single active task by ID.

    Args:
        task_id: The task ID.

    Returns:
        TaskInfo with full detail, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.GET, f"/tasks/{task_id}",
    )
    if not response.success:
        return response.error or "Failed to fetch task"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_task(data)


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_create_task(
    content: str,
    description: str | None = None,
    project_id: str | None = None,
    section_id: str | None = None,
    parent_id: str | None = None,
    labels: list[str] | None = None,
    priority: int | None = None,
    due_string: str | None = None,
    due_date: str | None = None,
    due_datetime: str | None = None,
    due_lang: str | None = None,
    deadline_date: str | None = None,
    deadline_lang: str | None = None,
    duration: int | None = None,
    duration_unit: str | None = None,
) -> TaskInfo | str:
    """Create a new task.

    Supports rich due date specification: use ``due_string`` for natural language
    (e.g. "tomorrow at 3pm"), ``due_date`` for a date (``YYYY-MM-DD``), or
    ``due_datetime`` for a precise time (``YYYY-MM-DDTHH:MM:SSZ``).

    Priority uses Todoist's internal scale: 1=normal, 2=medium, 3=high, 4=urgent.
    In the Todoist UI, p1 (urgent) corresponds to API priority 4.

    Args:
        content: Task content (title). Supports markdown.
        description: Task description. Optional.
        project_id: Project to add the task to. Defaults to Inbox.
        section_id: Section within the project. Optional.
        parent_id: Parent task ID for creating subtasks. Optional.
        labels: Label names to attach. Optional.
        priority: Priority (1=normal, 2=medium, 3=high, 4=urgent). Optional.
        due_string: Natural language due date (e.g. "tomorrow", "every monday").
        due_date: Due date in ``YYYY-MM-DD`` format.
        due_datetime: Due datetime in ``YYYY-MM-DDTHH:MM:SSZ`` format.
        due_lang: 2-char language code for ``due_string`` parsing.
        deadline_date: Hard deadline in ``YYYY-MM-DD`` format. Optional.
        deadline_lang: Language for deadline string parsing. Optional.
        duration: Task duration amount. Optional.
        duration_unit: Duration unit — ``minute`` or ``day``. Required with duration.

    Returns:
        Created TaskInfo, or an error string on failure.

    """
    body: dict[str, Any] = {"content": content}
    if description is not None:
        body["description"] = description
    if project_id is not None:
        body["project_id"] = project_id
    if section_id is not None:
        body["section_id"] = section_id
    if parent_id is not None:
        body["parent_id"] = parent_id
    if labels is not None:
        body["labels"] = labels
    if priority is not None:
        body["priority"] = priority
    if due_string is not None:
        body["due_string"] = due_string
    if due_date is not None:
        body["due_date"] = due_date
    if due_datetime is not None:
        body["due_datetime"] = due_datetime
    if due_lang is not None:
        body["due_lang"] = due_lang
    if deadline_date is not None:
        body["deadline_date"] = deadline_date
    if deadline_lang is not None:
        body["deadline_lang"] = deadline_lang
    if duration is not None:
        body["duration"] = duration
    if duration_unit is not None:
        body["duration_unit"] = duration_unit

    response: TodoistResult = await api_request(
        HttpMethod.POST, "/tasks", body=body,
    )
    if not response.success:
        return response.error or "Failed to create task"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_task(data)


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_update_task(
    task_id: str,
    content: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    priority: int | None = None,
    due_string: str | None = None,
    due_date: str | None = None,
    due_datetime: str | None = None,
    due_lang: str | None = None,
    deadline_date: str | None = None,
    deadline_lang: str | None = None,
    duration: int | None = None,
    duration_unit: str | None = None,
) -> TaskInfo | str:
    """Update an existing task.

    Only provided fields are modified; omitted fields are left unchanged.

    Args:
        task_id: The task ID to update.
        content: New task content. Optional.
        description: New description. Optional.
        labels: Replacement label names (replaces all). Optional.
        priority: New priority (1=normal, 2=medium, 3=high, 4=urgent). Optional.
        due_string: Natural language due date. Optional.
        due_date: Due date in ``YYYY-MM-DD`` format. Optional.
        due_datetime: Due datetime in ``YYYY-MM-DDTHH:MM:SSZ`` format. Optional.
        due_lang: 2-char language code for ``due_string`` parsing. Optional.
        deadline_date: Hard deadline in ``YYYY-MM-DD`` format. Optional.
        deadline_lang: Language for deadline parsing. Optional.
        duration: Task duration amount. Optional.
        duration_unit: Duration unit — ``minute`` or ``day``. Optional.

    Returns:
        Updated TaskInfo, or an error string on failure.

    """
    body: dict[str, Any] = {}
    if content is not None:
        body["content"] = content
    if description is not None:
        body["description"] = description
    if labels is not None:
        body["labels"] = labels
    if priority is not None:
        body["priority"] = priority
    if due_string is not None:
        body["due_string"] = due_string
    if due_date is not None:
        body["due_date"] = due_date
    if due_datetime is not None:
        body["due_datetime"] = due_datetime
    if due_lang is not None:
        body["due_lang"] = due_lang
    if deadline_date is not None:
        body["deadline_date"] = deadline_date
    if deadline_lang is not None:
        body["deadline_lang"] = deadline_lang
    if duration is not None:
        body["duration"] = duration
    if duration_unit is not None:
        body["duration_unit"] = duration_unit

    if not body:
        return "No fields to update"

    response: TodoistResult = await api_request(
        HttpMethod.POST, f"/tasks/{task_id}", body=body,
    )
    if not response.success:
        return response.error or "Failed to update task"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_task(data)


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_close_task(task_id: str) -> str:
    """Complete a task.

    For recurring tasks, the task is scheduled to its next occurrence.
    For non-recurring tasks, the task is marked as completed.

    Args:
        task_id: The task ID to complete.

    Returns:
        Confirmation message, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.POST, f"/tasks/{task_id}/close",
    )
    if not response.success:
        return response.error or "Failed to close task"
    return "Task closed successfully"


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_reopen_task(task_id: str) -> str:
    """Reopen a completed task.

    Restores the task to active status. If the task was completed and belongs
    to a completed parent or is in a completed project, those are also reopened.

    Args:
        task_id: The task ID to reopen.

    Returns:
        Confirmation message, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.POST, f"/tasks/{task_id}/reopen",
    )
    if not response.success:
        return response.error or "Failed to reopen task"
    return "Task reopened successfully"


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_delete_task(task_id: str) -> str:
    """Permanently delete a task.

    This action cannot be undone. The task and all its subtasks are removed.

    Args:
        task_id: The task ID to delete.

    Returns:
        Confirmation message, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.DELETE, f"/tasks/{task_id}",
    )
    if not response.success:
        return response.error or "Failed to delete task"
    return "Task deleted successfully"


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_move_task(
    task_id: str,
    project_id: str | None = None,
    section_id: str | None = None,
    parent_id: str | None = None,
) -> str:
    """Move a task to another project, section, or parent.

    Specify exactly one destination. Moving to a project clears the section.
    Moving to a section also moves to that section's project.

    Args:
        task_id: The task ID to move.
        project_id: Destination project ID. Optional.
        section_id: Destination section ID. Optional.
        parent_id: New parent task ID (makes this a subtask). Optional.

    Returns:
        Confirmation message, or an error string on failure.

    """
    body: dict[str, Any] = {}
    if project_id is not None:
        body["project_id"] = project_id
    if section_id is not None:
        body["section_id"] = section_id
    if parent_id is not None:
        body["parent_id"] = parent_id

    if not body:
        return "No destination specified"

    response: TodoistResult = await api_request(
        HttpMethod.POST, f"/tasks/{task_id}/move", body=body,
    )
    if not response.success:
        return response.error or "Failed to move task"
    return "Task moved successfully"


@tool(annotations=ToolAnnotations(readOnlyHint=False))
async def todoist_quick_add_task(text: str) -> TaskInfo | str:
    """Add a task using natural language Quick Add syntax.

    Parses natural language input to extract task content, due dates,
    priority, labels, and project. Uses the same parser as the Todoist
    Quick Add bar.

    Examples: ``"Buy milk tomorrow p1 #Shopping @errands"``

    Args:
        text: Natural language task input with Quick Add syntax.

    Returns:
        Created TaskInfo, or an error string on failure.

    """
    response: TodoistResult = await api_request(
        HttpMethod.POST, "/tasks/quick", body={"text": text},
    )
    if not response.success:
        return response.error or "Failed to quick-add task"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_task(data)


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_tasks_by_filter(
    query: str,
    limit: int = 50,
    cursor: str | None = None,
) -> list[TaskInfo] | str:
    """Get tasks matching a Todoist filter query.

    Uses Todoist's filter syntax for advanced task retrieval. Supports
    expressions like ``"today & p1"``, ``"overdue"``, ``"#Work & @urgent"``,
    ``"due before: next week"``.

    See https://todoist.com/help/articles/introduction-to-filters-V98wIH

    Args:
        query: Todoist filter expression.
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of matching TaskInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {
        "query": query,
        "limit": limit,
        "cursor": cursor,
    }
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/tasks/filter", params=params,
    )
    if not response.success:
        return response.error or "Failed to filter tasks"
    return _parse_task_list(response.data)


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_completed_tasks(
    project_id: str | None = None,
    section_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> list[TaskInfo] | str:
    """Get completed tasks by completion date range.

    Returns tasks completed within the specified time window, ordered by
    completion date. Useful for daily reviews and productivity reports.

    Args:
        project_id: Filter by project ID. Optional.
        section_id: Filter by section ID. Optional.
        since: Start of date range (ISO 8601 datetime). Optional.
        until: End of date range (ISO 8601 datetime). Optional.
        limit: Maximum results per page (default 50, max 200).
        cursor: Pagination cursor from a previous response.

    Returns:
        List of completed TaskInfo objects, or an error string on failure.

    """
    params: dict[str, Any] = {
        "project_id": project_id,
        "section_id": section_id,
        "since": since,
        "until": until,
        "limit": limit,
        "cursor": cursor,
    }
    response: TodoistResult = await api_request(
        HttpMethod.GET, "/tasks/completed/by_completion_date", params=params,
    )
    if not response.success:
        return response.error or "Failed to fetch completed tasks"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    items = data.get("items", [])
    if not isinstance(items, list):
        return "Unexpected items format"
    return [_parse_task(item) for item in items if isinstance(item, dict)]


task_tools = [
    todoist_get_tasks,
    todoist_get_task,
    todoist_create_task,
    todoist_update_task,
    todoist_close_task,
    todoist_reopen_task,
    todoist_delete_task,
    todoist_move_task,
    todoist_quick_add_task,
    todoist_get_tasks_by_filter,
    todoist_get_completed_tasks,
]

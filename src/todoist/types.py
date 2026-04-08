# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Typed models for Todoist API responses.

Result types (frozen dataclasses):
  TodoistResult        -- raw REST result wrapper
  DueInfo              -- task due date/time
  DeadlineInfo         -- task hard deadline
  TaskInfo             -- task summary
  ProjectInfo          -- project summary
  SectionInfo          -- section summary
  CommentInfo          -- task or project comment
  LabelInfo            -- personal label
  UserInfo             -- authenticated user profile

Type aliases:
  JSONPrimitive        -- scalar JSON values
  JSONValue            -- recursive JSON value (pre-3.12 TypeAlias)
  JSONObject           -- dict[str, JSONValue]
  JSONArray            -- list[JSONValue]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias


# --- JSON types ---

JSONPrimitive: TypeAlias = str | int | float | bool | None
"""Scalar JSON values. Non-recursive, safe as plain union."""

JSONValue: TypeAlias = str | int | float | bool | dict[str, Any] | list[Any] | None
"""Recursive JSON value: primitive, object, or array.

Cannot be truly recursive with TypeAlias (pre-3.12); uses Any for nesting.
PEP 695 ``type`` statements (3.12+) resolve this via lazy evaluation.
"""

JSONObject: TypeAlias = dict[str, JSONValue]
"""JSON object: string keys mapped to JSON values."""

JSONArray: TypeAlias = list[JSONValue]
"""JSON array: ordered sequence of JSON values."""


# --- Generic result ---


@dataclass(frozen=True, slots=True)
class TodoistResult:
    """Raw Todoist REST result.

    Used as the internal request return type for all API calls.
    """

    # fmt: off
    success: bool
    data:    JSONValue | None = None
    error:   str | None       = None
    # fmt: on


# --- Due dates ---


@dataclass(frozen=True, slots=True)
class DueInfo:
    """Task due date/time.

    Three flavors: full-day (``YYYY-MM-DD``), floating with time
    (``YYYY-MM-DDTHH:MM:SS``), and fixed timezone
    (``YYYY-MM-DDTHH:MM:SSZ`` + ``timezone``).
    """

    # fmt: off
    date:         str
    string:       str | None = None
    is_recurring: bool       = False
    timezone:     str | None = None
    lang:         str | None = None
    # fmt: on


@dataclass(frozen=True, slots=True)
class DeadlineInfo:
    """Task hard deadline.

    Simpler than due dates: date-only in ``YYYY-MM-DD`` format, non-recurring.
    """

    # fmt: off
    date: str
    lang: str | None = None
    # fmt: on


# --- Tasks ---


@dataclass(frozen=True, slots=True)
class TaskInfo:
    """Task summary.

    Priority values use Todoist's internal scale: 1=normal, 2=medium,
    3=high, 4=urgent. The UI displays these inverted (p1=urgent=API 4).
    """

    # fmt: off
    id:           str
    content:      str
    project_id:   str
    description:  str | None       = None
    section_id:   str | None       = None
    parent_id:    str | None       = None
    labels:       list[str]        = field(default_factory=list)
    priority:     int              = 1
    due:          DueInfo | None   = None
    deadline:     DeadlineInfo | None = None
    checked:      bool             = False
    added_at:     str | None       = None
    completed_at: str | None       = None
    updated_at:   str | None       = None
    # fmt: on


# --- Projects ---


@dataclass(frozen=True, slots=True)
class ProjectInfo:
    """Project summary."""

    # fmt: off
    id:               str
    name:             str
    color:            str | None = None
    is_shared:        bool       = False
    is_favorite:      bool       = False
    is_inbox_project: bool       = False
    view_style:       str | None = None
    # fmt: on


# --- Sections ---


@dataclass(frozen=True, slots=True)
class SectionInfo:
    """Section summary."""

    # fmt: off
    id:         str
    name:       str
    project_id: str
    order:      int = 0
    # fmt: on


# --- Comments ---


@dataclass(frozen=True, slots=True)
class CommentInfo:
    """Task or project comment."""

    # fmt: off
    id:         str
    content:    str
    task_id:    str | None = None
    project_id: str | None = None
    posted_at:  str | None = None
    # fmt: on


# --- Labels ---


@dataclass(frozen=True, slots=True)
class LabelInfo:
    """Personal label."""

    # fmt: off
    id:          str
    name:        str
    color:       str | None = None
    order:       int        = 0
    is_favorite: bool       = False
    # fmt: on


# --- User ---


@dataclass(frozen=True, slots=True)
class UserInfo:
    """Authenticated user profile."""

    # fmt: off
    id:        str
    full_name: str
    email:     str | None = None
    # fmt: on

# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""User tools.

Tools:
  todoist_get_user_info  -- get the authenticated user's profile
"""

from __future__ import annotations

from dedalus_mcp import HttpMethod, tool
from dedalus_mcp.types import ToolAnnotations

from todoist.request import _opt_str, _str, api_request
from todoist.types import JSONObject, TodoistResult, UserInfo


# --- Helpers ---


def _parse_user(raw: JSONObject) -> UserInfo:
    """Parse a raw user dict into a UserInfo.

    Args:
        raw: Untyped user object from the REST response.

    Returns:
        Parsed UserInfo with coerced fields.

    """
    return UserInfo(
        id=_str(raw.get("id")),
        full_name=_str(raw.get("full_name")),
        email=_opt_str(raw.get("email")),
    )


# --- Tools ---


@tool(annotations=ToolAnnotations(readOnlyHint=True))
async def todoist_get_user_info() -> UserInfo | str:
    """Get the authenticated user's profile.

    Returns basic profile information including name and email.

    Returns:
        UserInfo for the current user, or an error string on failure.

    """
    response: TodoistResult = await api_request(HttpMethod.GET, "/user")
    if not response.success:
        return response.error or "Failed to fetch user info"
    data = response.data
    if not isinstance(data, dict):
        return "Unexpected response"
    return _parse_user(data)


user_tools = [
    todoist_get_user_info,
]

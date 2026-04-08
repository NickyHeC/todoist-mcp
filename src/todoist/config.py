# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Todoist connection configuration.

Evaluated at import time, after ``load_dotenv()`` in ``main.py``
has already injected the .env file.

Todoist uses OAuth2 for authentication. The Dedalus platform handles
token exchange; the server only declares the secret name it expects.

Objects:
  todoist -- Connection with OAuth bearer token auth
"""

from __future__ import annotations

from dedalus_mcp.auth import Connection, SecretKeys


todoist = Connection(
    name="todoist",
    secrets=SecretKeys(token="TODOIST_ACCESS_TOKEN"),  # noqa: S106
    base_url="https://api.todoist.com/api/v1",
    auth_header_format="Bearer {api_key}",
)

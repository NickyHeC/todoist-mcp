# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Tool registry for todoist-mcp.

Modules:
  tasks      -- todoist_get_tasks, todoist_get_task, todoist_create_task,
                todoist_update_task, todoist_close_task, todoist_reopen_task,
                todoist_delete_task, todoist_move_task, todoist_quick_add_task,
                todoist_get_tasks_by_filter, todoist_get_completed_tasks
  projects   -- todoist_get_projects, todoist_get_project, todoist_create_project,
                todoist_update_project, todoist_delete_project, todoist_search_projects
  sections   -- todoist_get_sections, todoist_create_section
  comments   -- todoist_get_comments, todoist_create_comment
  labels     -- todoist_get_labels, todoist_create_label, todoist_search_labels
  user       -- todoist_get_user_info
"""

from __future__ import annotations

from tools.comments import comment_tools
from tools.labels import label_tools
from tools.projects import project_tools
from tools.sections import section_tools
from tools.tasks import task_tools
from tools.user import user_tools


todoist_tools = [
    *task_tools,
    *project_tools,
    *section_tools,
    *comment_tools,
    *label_tools,
    *user_tools,
]

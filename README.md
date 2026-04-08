# todoist-mcp

A [Todoist](https://todoist.com) MCP server for Dedalus.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- A Todoist account

## Setup

```bash
cd todoist-mcp
cp .env.example .env   # then fill in your values
uv sync
```

### Environment variables

Todoist uses OAuth2 for authentication. The Dedalus platform (DAuth) handles the
OAuth flow. The MCP server declares the secret name it needs (e.g. `TODOIST_ACCESS_TOKEN`).

OAuth provider configuration (consumed by the Dedalus platform):

| Variable | Description |
| --- | --- |
| `OAUTH_ENABLED` | `true` |
| `OAUTH_AUTHORIZE_URL` | `https://app.todoist.com/oauth/authorize` |
| `OAUTH_TOKEN_URL` | `https://api.todoist.com/oauth/access_token` |
| `OAUTH_CLIENT_ID` | Your Todoist OAuth app client ID |
| `OAUTH_CLIENT_SECRET` | Your Todoist OAuth app client secret |
| `OAUTH_SCOPES_AVAILABLE` | `data:read_write,data:delete,project:delete` |
| `OAUTH_BASE_URL` | `https://api.todoist.com` |

Dedalus client configuration (for `client.py` testing):

| Variable | Description |
| --- | --- |
| `DEDALUS_API_KEY` | Your Dedalus API key (`dsk_*`) |
| `DEDALUS_API_URL` | Defaults to `https://api.dedaluslabs.ai` |
| `DEDALUS_AS_URL` | Defaults to `https://as.dedaluslabs.ai` |

## Run the server

```bash
uv run src/main.py
```

## Test locally

```bash
uv run src/client.py --test-connection   # verify credentials, no server needed
uv run src/client.py                     # test tools against running server
```

## Lint and typecheck

```bash
uv run --group lint ruff format src/
uv run --group lint ruff check src/ --fix
uv run --group lint ty check src/
```

## Available tools

| Tool                          | R/W | Description                                            |
| ----------------------------- | --- | ------------------------------------------------------ |
| `todoist_get_tasks`           | R   | List active tasks with optional filters                |
| `todoist_get_task`            | R   | Get a single task by ID                                |
| `todoist_create_task`         | W   | Create a new task                                      |
| `todoist_update_task`         | W   | Update an existing task                                |
| `todoist_close_task`          | W   | Complete a task (recurring → next occurrence)          |
| `todoist_reopen_task`         | W   | Reopen a completed task                                |
| `todoist_delete_task`         | W   | Permanently delete a task                              |
| `todoist_move_task`           | W   | Move task to another project/section/parent            |
| `todoist_quick_add_task`      | W   | Add task using natural language Quick Add syntax       |
| `todoist_get_tasks_by_filter` | R   | Get tasks matching a Todoist filter query              |
| `todoist_get_completed_tasks` | R   | Get completed tasks by completion date range           |
| `todoist_get_projects`        | R   | List all active projects                               |
| `todoist_get_project`         | R   | Get a single project by ID                             |
| `todoist_create_project`      | W   | Create a new project                                   |
| `todoist_update_project`      | W   | Update an existing project                             |
| `todoist_delete_project`      | W   | Delete a project and all its tasks                     |
| `todoist_search_projects`     | R   | Search projects by name with wildcards                 |
| `todoist_get_sections`        | R   | List sections, optionally filtered by project          |
| `todoist_create_section`      | W   | Create a new section in a project                      |
| `todoist_get_comments`        | R   | List comments for a task or project                    |
| `todoist_create_comment`      | W   | Add a comment to a task or project                     |
| `todoist_get_labels`          | R   | List all personal labels                               |
| `todoist_create_label`        | W   | Create a new personal label                            |
| `todoist_search_labels`       | R   | Search labels by name with wildcards                   |
| `todoist_get_user_info`       | R   | Get the authenticated user's profile                   |

**25 tools** (13 read, 12 write)

## Architecture

Todoist uses a standard REST API with JSON request/response bodies. The request
layer in `src/todoist/request.py` dispatches calls through Dedalus's HTTP enclave,
which injects OAuth credentials transparently.

```plaintext
src/
├── todoist/
│   ├── config.py      # Connection definition (OAuth)
│   ├── request.py     # REST dispatch + coercion helpers
│   └── types.py       # Typed dataclass models
├── tools/
│   ├── tasks.py       # Task CRUD + close/reopen/move/quick-add/filter
│   ├── projects.py    # Project CRUD + search
│   ├── sections.py    # Section operations
│   ├── comments.py    # Comment operations
│   ├── labels.py      # Label operations + search
│   └── user.py        # User profile
├── server.py          # MCPServer setup
├── main.py            # Entry point
└── client.py          # ConnectionTester + tool smoke test
```

## Notes

- Todoist's API is **REST** with JSON. Every tool dispatches an HTTP request (GET, POST, or DELETE).
- Priority values use Todoist's internal scale: 1=normal, 2=medium, 3=high, 4=urgent.
  In the UI, p1 (urgent) corresponds to API priority 4 — the scale is inverted.
- All IDs are opaque strings.
- Cursor-based pagination is used for list endpoints. Default page size is 50, maximum 200.
- Due dates come in three flavors: full-day (`YYYY-MM-DD`), floating with time
  (`YYYY-MM-DDTHH:MM:SS`), and fixed timezone (`YYYY-MM-DDTHH:MM:SSZ` + timezone).
- Quick Add supports natural language parsing: `"Buy milk tomorrow p1 #Shopping @errands"`.
- Some features (reminders, activity log, file uploads) require paid Todoist plans.
- Authentication uses OAuth2 via DAuth. The server never sees raw OAuth tokens directly.

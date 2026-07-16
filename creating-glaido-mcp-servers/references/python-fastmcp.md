# Python + FastMCP (default)

The lightest path and the recommended default: a Python MCP server built with FastMCP,
managed and run with `uv`. Glaido launches it as `uv --directory <abs> run server.py`.

Copyable starter files live in [../assets/templates/python/](../assets/templates/python/).
Copy that folder, rename it, and adapt.

**Prerequisite:** `uv` must be installed (`command -v uv`). If it isn't, install it first - see
[installing-runtimes.md](installing-runtimes.md). You don't need a separate Python install: `uv
run` fetches a compatible Python and manages the environment for you, which is the whole reason
this skill defaults to uv.

## Folder layout

```text
my-server/
├── server.py          # FastMCP server + tool definitions
├── pyproject.toml      # dependencies (uv reads this)
├── mcp.json            # Glaido import config (absolute paths)
├── .env.example        # placeholder keys (committed)
├── .env                # real secrets (gitignored)
├── .gitignore
├── README.md
└── utils/              # optional: real logic, kept out of server.py
    ├── __init__.py
    └── <feature>.py
```

Keeping the API/business logic in `utils/` and the thin tool wrappers in `server.py` keeps
tools readable and testable.

## pyproject.toml

```toml
[project]
name = "glaido-mcp-my-server"
version = "0.1.0"
description = "A local MCP server for Glaido."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]",
    "python-dotenv",
    "httpx",        # only if the server calls an HTTP API
]
```

`mcp[cli]` provides FastMCP. Add only the dependencies the server actually uses.

## server.py

```python
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Load secrets from THIS folder's .env, regardless of where Glaido launches us.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Server-level instructions: tells the agent what this server is for and WHEN to use it.
# FastMCP puts this in the MCP `initialize` response, which the client passes to the model
# as a hint alongside the tool list. Write a "use this server to…" statement, not a label.
SERVER_INSTRUCTIONS = (
    "Use this server to <do X> with <service/domain>. "
    "Covers <the kinds of actions, e.g. searching, creating, updating items>."
)

mcp = FastMCP(name="My Server", instructions=SERVER_INSTRUCTIONS)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
)
def search_items(query: str, limit: Optional[int] = None) -> dict:
    """Search items by free-text query. Read-only."""
    # ... call your API / logic ...
    return {"status": "ok", "data": [...]}


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def delete_item(item_id: str) -> dict:
    """Delete an item by id. Destructive - Glaido will ask before running."""
    return {"status": "ok", "deleted": item_id}


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Key points:

- **`mcp.run(transport="stdio")`** is required - that's the transport Glaido uses for local
  servers.
- **Type your arguments and return a dict.** FastMCP turns the signature + docstring into the
  tool schema the agent sees. The docstring is the description the agent reads to decide
  whether to call the tool - write it for that purpose.
- **Annotate read-only vs destructive tools** with `ToolAnnotations`. Glaido uses these to
  decide whether a tool runs automatically or asks the user first. `openWorldHint=True` means
  the tool reaches an external system (an API); set it on tools that hit the network.
- Default arguments / `Optional[...]` make parameters optional in the schema.

## The stdout rule (critical)

The server speaks MCP over stdout. **Never `print()` to stdout.** A stray print corrupts the
stream and Glaido marks the server failed. For any logging, write to stderr:

```python
import sys
print("debug info", file=sys.stderr)          # safe
# or use the logging module - it defaults to stderr
import logging
logging.getLogger(__name__).info("started")    # safe
```

## Loading environment variables

```python
import os
api_key = os.getenv("SERVICE_API_KEY", "")
if not api_key:
    # Return a clear error from the tool rather than crashing the process.
    ...
```

`.env.example` (committed):

```bash
SERVICE_API_KEY=replace_with_your_key
```

Return a clean `{"status": "error", "error": "SERVICE_API_KEY is missing"}` when a key is
absent - far easier for the user to diagnose than a stack trace.

## mcp.json

```json
{
  "mcpServers": {
    "My Server": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/my-server", "run", "server.py"],
      "env": {}
    }
  }
}
```

Replace the path with the real absolute path - get it by running `pwd` inside the folder.
`uv --directory <path> run server.py` makes uv resolve dependencies and run from that folder,
so it works no matter where Glaido invokes it.

## Run and test locally

```bash
cd my-server
uv run server.py          # should start and wait on stdin without crashing or printing to stdout
```

For interactive inspection, the MCP Inspector is handy:

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

It lets you list tools and call them before importing into Glaido.

## Notes

- `uv` must be installed and on PATH.
- If you split logic into `utils/`, include `utils/__init__.py` so imports work under
  `uv run`.

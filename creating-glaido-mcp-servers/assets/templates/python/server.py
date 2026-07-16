"""Glaido MCP server (Python + FastMCP).

Replace the example tools with your own. Keep heavier logic in `utils/` and keep these
tool functions thin so the agent-facing schema stays readable.
"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Load secrets from THIS folder's .env, no matter where Glaido launches the process from.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Server-level instructions: tells the agent what this server is for and WHEN to use it.
# Sent to the model (via the MCP `initialize` response) as a hint alongside the tool list,
# so the agent knows whether to reach for this server at all. Write a "use this server to…"
# statement that names the domain and the kinds of actions it covers - not a label.
SERVER_INSTRUCTIONS = (
    "Use this server to <do X> with <service/domain>. "
    "Covers <the kinds of actions, e.g. searching, creating, updating items>."
)

mcp = FastMCP(name="My Server", instructions=SERVER_INSTRUCTIONS)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,    # does not change state
        destructiveHint=False,
        openWorldHint=True,   # reaches an external system (set False for purely local work)
    ),
)
def search_items(query: str, limit: Optional[int] = None) -> dict:
    """Search items by a free-text query. Read-only.

    The agent reads this docstring to decide when to call the tool - make it a clear
    capability statement.
    """
    # ... call your API or logic here ...
    return {"status": "ok", "data": []}


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,  # Glaido will ask before running this
    ),
)
def delete_item(item_id: str) -> dict:
    """Delete an item by id. Destructive."""
    # ... perform the deletion ...
    return {"status": "ok", "deleted": item_id}


if __name__ == "__main__":
    # stdio is the transport Glaido uses for local servers. Do not change this.
    mcp.run(transport="stdio")

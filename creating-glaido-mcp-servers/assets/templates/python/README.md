# My Server - Glaido MCP Server

Local Python MCP server for Glaido, built with FastMCP and run via `uv`.

## Tools

- `search_items` - search items by query (read-only)
- `delete_item` - delete an item by id (destructive; Glaido asks before running)

_Replace this list with the real tools._

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   - `SERVICE_API_KEY` - _where to get it_
2. Confirm it runs:
   ```bash
   uv run server.py
   ```
   It should start and wait silently. If anything prints to the screen, that output is going
   to stdout and will break the connection - move it to stderr.

## Import into Glaido

1. Fill in `.env` with real values.
2. Open **Glaido → Settings → MCP Servers**.
3. Click **Import** and select this folder.
4. Enable the server with its toggle.

> The path in `mcp.json` is absolute. If you move this folder, update that path and re-import.

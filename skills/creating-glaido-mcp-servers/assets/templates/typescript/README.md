# My Server — Glaido MCP Server

Local TypeScript MCP server for Glaido, built with `@modelcontextprotocol/sdk` and run via
Node.

## Tools

- `search_items` — search items by query (read-only)
- `delete_item` — delete an item by id (destructive; Glaido asks before running)

_Replace this list with the real tools._

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   - `SERVICE_API_KEY` — _where to get it_
2. Install and build (Glaido runs the compiled `dist/`):
   ```bash
   npm install
   npm run build
   node dist/index.js
   ```
   It should start and wait silently. Any `console.log` output goes to stdout and will break
   the connection — use `console.error` instead.

## Import into Glaido

1. Fill in `.env` and run `npm run build`.
2. Open **Glaido → Settings → MCP Servers**.
3. Click **Import** and select this folder.
4. Enable the server with its toggle.

> The path in `mcp.json` is absolute and points at `dist/`. Rebuild after code changes, and if
> you move this folder, update that path and re-import.

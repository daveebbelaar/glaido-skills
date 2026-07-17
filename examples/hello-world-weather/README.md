# Weather API - Glaido MCP Server

The simplest useful Glaido tool: ask for the weather in any city, out loud. Imports into
Glaido as **Weather API**. Built with FastMCP and run via `uv`. Uses the free
[Open-Meteo](https://open-meteo.com) API, so there is **no API key and no signup**.

## Tools

- `get_weather(city)` - current temperature, feels-like, humidity, wind, and conditions for
  any city in the world (read-only; Glaido runs it without asking)

## Setup

There are no secrets to configure. Just confirm it runs:

```bash
uv run server.py
```

It should start and wait silently. If anything prints to the screen, that output is going
to stdout and will break the connection - move it to stderr.

> Don't have `uv`? Install it from [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/).
> It handles Python and all dependencies for you.

## Import into Glaido

1. Put this folder somewhere it will stay put (for example `~/glaido-mcp-servers/hello-world-weather`).
2. Open **Glaido → Tools**, click **Import**, and select this folder.
3. Enable the server with its toggle.
4. Open Agent Mode and ask: *"What's the weather in Amsterdam?"*

No paths to edit: the `mcp.json` contains none, and Glaido runs the server from the folder
you imported. If you move the folder later, just import it again.

## Make it yours

This example exists to show the shape of a Glaido tool: one small server, a few clear
tools, imported as a folder. To build your own, point your coding agent at the
[`creating-glaido-mcp-servers`](../../creating-glaido-mcp-servers/) skill in this
repository and describe what you want.

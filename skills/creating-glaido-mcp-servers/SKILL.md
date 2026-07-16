---
name: creating-glaido-mcp-servers
description: >-
  Build a local MCP server that imports directly into the Glaido desktop app. Use this
  whenever someone wants to add a tool, capability, or integration to Glaido — scaffold an
  MCP server, write an mcp.json they can import, connect Glaido to a service (Notion, Slack,
  GitHub, Todoist, a custom API, a local script, etc.), or "make Glaido able to do X". Works
  in any language and defaults to Python + FastMCP run via uv. Produces a ready-to-import
  folder with mcp.json, environment setup, and run instructions. Trigger even when the user
  doesn't say "MCP" — phrases like "make a Glaido tool", "I want Glaido to be able to send
  Slack messages", "connect Glaido to my database", or "give Glaido access to my API" all
  apply.
---

# Creating Glaido MCP Servers

## What this produces

A self-contained folder that the Glaido desktop app can import as a local tool. The folder
always contains an `mcp.json` (the file Glaido reads on import) plus the server code, its
dependencies, and environment setup. After import, the server's tools become available to
Glaido's agent.

Glaido runs these servers as **local processes over stdio**. That focus drives every choice
below: the server is launched from disk by an absolute path, it talks MCP over stdin/stdout,
and its secrets live in a local `.env` next to the code.

The user never needs to know anything about Glaido's internals — only how to import the
folder and set their keys. Keep your explanations at that level.

## Step 0 — Decide: reuse or build?

Before writing any code, figure out which situation you're in. This is the single most
important decision and people often skip it.

**A. Connecting Glaido to an existing third-party service** (Notion, Slack, GitHub, Linear,
Stripe, Google Drive, a database, etc.) → **someone has probably already built an MCP server
for it.** Do not reinvent it. Go to Step 1A.

**B. Building a custom server** around the user's own API, script, business logic, or local
machine actions → there's nothing to reuse. Go to Step 1B.

If it's ambiguous (e.g. "I want Glaido to manage my tasks"), ask one quick question: are they
using a known product (reuse) or their own system (build)?

## Step 1A — Reuse path: find an existing server first

When the target is a known service, search before you build. Read
[references/existing-servers.md](references/existing-servers.md) for where to look and how to
vet what you find.

The short version:

1. **Search** npm (`@modelcontextprotocol/server-*` and community packages), GitHub, and the
   MCP server registries / awesome-mcp lists for that service. Use web search — your training
   data is stale on which servers exist.
2. **Present 1–3 options** to the user with what each does, what auth it needs, and tradeoffs.
   Don't silently pick one.
3. **Ask what they actually want**: which tools they need exposed, which to hide or disable,
   what scopes/permissions, and any behavior to adjust. A good third-party server often
   exposes 20 tools when the user wants 3.
4. **Bring it in as a local stdio server**: configure the run command (usually `npx -y
   <package>` or a cloned/vendored copy), put its credentials in `.env`, and write the
   `mcp.json`. Then continue to Step 5 (env) and Step 6 (mcp.json).

Only fall back to building from scratch if nothing suitable exists, the existing options are
low quality, or the user explicitly wants their own.

## Step 1B — Build path: gather the spec

For a custom server, pin down before scaffolding:

- **What tools** the server should expose — each as a verb the agent can call (e.g.
  `create_invoice`, `search_contacts`, `restart_service`). Name them clearly; the agent picks
  tools by name and description.
- **Inputs and outputs** per tool — typed arguments and a structured (usually dict/JSON)
  return so the agent can reason over results.
- **What it talks to** — an HTTP API, a local file/db, a CLI, the user's own code.
- **Secrets** it needs — API keys, tokens, base URLs.
- **Which tools are destructive** vs read-only — this drives Glaido's approval defaults
  (see Step 4).

## Step 2 — Choose language and a stable location

**Language:** default to **Python + FastMCP, run via `uv`** when the user has no preference —
it's the lightest path and the most reliable for first-time setups. Otherwise match the
user's stack. The skill is language-agnostic; pick the reference for the chosen language:

- Python → [references/python-fastmcp.md](references/python-fastmcp.md)
- TypeScript / Node → [references/typescript-mcp.md](references/typescript-mcp.md)
- Anything else (Go, Rust, Java, C#, …) → [references/other-languages.md](references/other-languages.md)

**Location:** create the server in its own folder somewhere it will stay put. Glaido stores an
**absolute path** to this folder and launches the server from there on every run. If the
folder moves later, the import breaks until the path is updated. A dedicated folder like
`~/glaido-mcp-servers/my-server` works well.

**Runtime:** confirm the launcher the server will use is actually installed before scaffolding
— a first-time user often doesn't have it yet. Quick check:

```bash
command -v uv      # Python servers (recommended launcher)
command -v node    # TypeScript servers
command -v npx     # running published servers / TypeScript
```

If it's missing, install it before continuing — see
[references/installing-runtimes.md](references/installing-runtimes.md) for per-OS commands.
For Python, **recommend `uv`**: `uv run` creates the isolated environment, installs
dependencies, and even fetches Python for you, so the user never has to deal with virtualenvs
or a separate Python install. Don't assume it's there — check.

## Step 3 — Scaffold the folder

Copy and adapt the template for the chosen language from
[assets/templates/](assets/templates/). A finished folder looks like:

```
my-server/
├── mcp.json          # what Glaido reads on import (absolute paths inside)
├── .env.example      # placeholder keys, committed to git
├── .env              # real secrets, gitignored, NOT committed
├── .gitignore        # ignores .env
├── README.md         # tools + how to import + which keys to set
└── <server code>     # server.py / src/index.ts / etc.
```

The language reference tells you exactly which files to create and what goes in each.

## Step 4 — Implement the server

Whichever language, these rules make a server that behaves well inside Glaido:

- **Give the server a clear `instructions` string — it's how the agent knows the server
  exists and when to reach for it.** MCP sends this server-level text to the model (in the
  `initialize` response) as a hint about what the whole server is for, separate from the
  per-tool descriptions. Write it as a "use this server to…" statement that names the domain
  and the kinds of actions it covers (e.g. "Use to manage the user's Todoist tasks — search,
  create, complete, and delete."), not a throwaway label. The per-tool descriptions tell the
  agent *which* tool to call; the server instructions tell it *whether to look here at all*.
  The language reference shows exactly where to set it (e.g. FastMCP's `instructions=`).
- **Name and describe each tool for an agent, not a human reading docs.** The agent decides
  what to call based on the tool name + description, so write them as clear capability
  statements ("Create a task in the user's inbox with optional due date").
- **Type the arguments and return structured data.** Return a dict / JSON object, not a bare
  string, so the agent can use the result.
- **Mark read-only vs destructive tools.** Glaido decides whether a tool runs automatically or
  asks the user first, and it keys off the tool's annotations: read-only tools can run
  automatically, destructive ones should prompt. Set `readOnlyHint` / `destructiveHint` (see
  the language reference). Getting this right is what makes the server safe to use without
  babysitting.
- **Never write anything to stdout except the MCP protocol.** This is the #1 reason a local
  server fails to connect. stdout *is* the communication channel. Any stray `print`,
  `console.log`, banner, or progress bar corrupts the stream and Glaido shows the server as
  failed. Send all logging and debug output to **stderr** instead. The language references
  show the safe pattern.

## Step 5 — Set up environment variables

Default approach (chosen for this skill): **the server loads its own `.env` from its own
folder.**

- Put every required key in **`.env.example`** with a placeholder value (e.g.
  `SERVICE_API_KEY=replace_with_your_key`) and commit it. This documents what's needed.
- Put real values in **`.env`** and make sure `.gitignore` excludes it. Never commit secrets.
- In the server code, load `.env` **relative to the code file**, not the current directory, so
  it works no matter where Glaido launches it from. The language references give the exact one
  line (e.g. Python `load_dotenv(Path(__file__).resolve().parent / ".env")`).
- Tell the user precisely which keys to set and where to obtain each one.

There is also a built-in alternative: Glaido passes the `env` block from `mcp.json` straight to
the process. That's simpler (no dotenv dependency) but the secret then lives inside the config
the user imports. Prefer `.env` for secrets; the `env` block is fine for non-secret config like
a base URL or a feature flag. Details and the tradeoff are in
[references/glaido-integration.md](references/glaido-integration.md).

## Step 6 — Write the mcp.json

This is the file Glaido reads. It must be named exactly `mcp.json` and sit at the folder root.
Full schema and field reference: [references/glaido-integration.md](references/glaido-integration.md).
The essentials:

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

- **`type` is `stdio`** for local servers — that's what this skill targets.
- **`command` must be resolvable on the user's PATH** (`uv`, `npx`, `node`, `python3`, …). If
  it might not be, use an absolute path to the binary.
- **Every path must be absolute.** Relative paths are not expanded. Generate the real path with
  `pwd` in the server folder and substitute it — don't leave the placeholder.
- The key (`"My Server"`) is the display name; Glaido derives a clean ID from it.

## Step 7 — Validate before handing off

Run the bundled checker against the folder — it catches the common import-blockers (missing or
malformed `mcp.json`, relative paths, a `command` not on PATH, committed secrets, and whether
the process even launches):

```bash
python3 <path-to-this-skill>/scripts/validate_glaido_mcp.py /ABSOLUTE/PATH/TO/my-server
```

(The script is [scripts/validate_glaido_mcp.py](scripts/validate_glaido_mcp.py), relative to
this skill's folder.)

Then start the server by hand to confirm it boots and exposes its tools without crashing — the
language reference gives the exact command (e.g. `uv run server.py`). Fix anything the checker
or the launch surfaces before telling the user it's ready.

## Step 8 — Hand off: how the user imports it

Give the user these steps (and fill in the real folder name and keys):

1. Set your secrets: open `<folder>/.env` and fill in the real values (copy from
   `.env.example` if `.env` doesn't exist yet).
2. Open **Glaido → Settings → MCP Servers**.
3. Click **Import** and select the `<folder>` you just created.
4. The server appears in the list — enable it with its toggle.
5. The agent can now use its tools. Destructive tools may ask for approval the first time,
   which is expected.

If the server doesn't connect, point them at the troubleshooting section in
[references/glaido-integration.md](references/glaido-integration.md) (the usual causes are an
unset key, a moved folder, or stray stdout output).

## Quick reference

| Need | Go to |
|------|-------|
| How Glaido imports, mcp.json schema, env behavior, troubleshooting | [references/glaido-integration.md](references/glaido-integration.md) |
| Installing uv / Node / Python (and the GUI-PATH gotcha) | [references/installing-runtimes.md](references/installing-runtimes.md) |
| Python + FastMCP server (default) | [references/python-fastmcp.md](references/python-fastmcp.md) |
| TypeScript / Node server | [references/typescript-mcp.md](references/typescript-mcp.md) |
| Go / Rust / Java / C# / other | [references/other-languages.md](references/other-languages.md) |
| Reusing an existing third-party server | [references/existing-servers.md](references/existing-servers.md) |
| Copyable starter files | [assets/templates/](assets/templates/) |

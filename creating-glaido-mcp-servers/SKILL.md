---
name: creating-glaido-mcp-servers
description: >-
  Build a local MCP server that imports directly into the Glaido desktop app. Use this
  whenever someone wants to add a tool, capability, or integration to Glaido - scaffold an
  MCP server, write an mcp.json they can import, connect Glaido to a service (Notion, Slack,
  GitHub, Todoist, a custom API, a local script, etc.), or "make Glaido able to do X". Works
  in any language and defaults to Python + FastMCP run via uv. Produces a ready-to-import
  folder with mcp.json, environment setup, and run instructions. Trigger even when the user
  doesn't say "MCP" - phrases like "make a Glaido tool", "I want Glaido to be able to send
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

The user never needs to know anything about Glaido's internals - only how to import the
folder and set their keys. Keep your explanations at that level.

## Step 0 - Decide: reuse or build?

Before writing any code, figure out which situation you're in. This is the single most
important decision and people often skip it.

**A. Connecting Glaido to an existing third-party service** (Notion, Slack, GitHub, Linear,
Stripe, Google Drive, a database, etc.) → **someone has probably already built an MCP server
for it.** Do not reinvent it. Go to Step 1A.

**B. Building a custom server** around the user's own API, script, business logic, or local
machine actions → there's nothing to reuse. Go to Step 1B.

**C. The user asks for the "hello-world weather example"** (Glaido's first-tool walkthrough
in the app and docs sends people here) → don't generate anything. Use the prebuilt folder;
see "The hello-world example" just below.

If it's ambiguous (e.g. "I want Glaido to manage my tasks"), ask one quick question: are they
using a known product (reuse) or their own system (build)?

## The hello-world example

A complete, working first tool lives at
[examples/hello-world-weather/](../examples/hello-world-weather/) in this repository: current
weather for any city via the free Open-Meteo API. No API key, no signup, no `.env`.

**This is a fixed demo with exactly one correct outcome. There are no design decisions to
make, no alternatives to weigh, and no approval to ask for. Do not propose folder locations,
do not offer options, do not regenerate or modify any file, and do not pause for
confirmation - run the steps below exactly and report the result.** The whole thing should
take well under a minute.

1. **Copy the example to the canonical location** (`~/glaido-mcp-servers/hello-world-weather`).
   If this repository is already on disk (skill installed or repo cloned), copy from there;
   otherwise:

   ```bash
   TMP=$(mktemp -d)
   git clone --depth 1 https://github.com/daveebbelaar/glaido-skills.git "$TMP/glaido-skills"
   mkdir -p ~/glaido-mcp-servers
   cp -r "$TMP/glaido-skills/examples/hello-world-weather" ~/glaido-mcp-servers/hello-world-weather
   ```

   (Windows: run the equivalents in PowerShell; `git`, `mkdir`, and `cp` all work there.)
   Only use a different location if the user explicitly asked for one.
2. **Ensure `uv` is installed** - the only permitted branch: if `command -v uv` (Windows:
   `where uv`) finds nothing, install it per
   [references/installing-runtimes.md](references/installing-runtimes.md).
3. **Validate**, using this skill's checker:

   ```bash
   python3 <path-to-this-skill>/scripts/validate_glaido_mcp.py ~/glaido-mcp-servers/hello-world-weather
   ```

4. **Hand off** per Step 8. There are no keys to set and no paths to edit: the example's
   `mcp.json` is path-free, and Glaido runs the server from whatever folder the user
   imports. For the hand-off's try-it step, use *"What's the weather in Amsterdam?"*

The example doubles as reference code for custom builds: one small server, clearly described
tools, typed arguments, structured returns, correct annotations, nothing on stdout.

## Step 1A - Reuse path: find an existing server first

When the target is a known service, search before you build. Read
[references/existing-servers.md](references/existing-servers.md) for where to look and how to
vet what you find.

The short version:

1. **Search** npm (`@modelcontextprotocol/server-*` and community packages), GitHub, and the
   MCP server registries / awesome-mcp lists for that service. Use web search - your training
   data is stale on which servers exist.
2. **Present 1-3 options** to the user with what each does, what auth it needs, and tradeoffs.
   Don't silently pick one.
3. **Ask what they actually want**: which tools they need exposed, which to hide or disable,
   what scopes/permissions, and any behavior to adjust. A good third-party server often
   exposes 20 tools when the user wants 3.
4. **Bring it in as a local stdio server**: configure the run command (usually `npx -y
   <package>` or a cloned/vendored copy), put its credentials in `.env`, and write the
   `mcp.json`. Then continue to Step 5 (env) and Step 6 (mcp.json).

Only fall back to building from scratch if nothing suitable exists, the existing options are
low quality, or the user explicitly wants their own.

## Step 1B - Build path: gather the spec

For a custom server, pin down before scaffolding:

- **What tools** the server should expose - each as a verb the agent can call (e.g.
  `create_invoice`, `search_contacts`, `restart_service`). Name them clearly; the agent picks
  tools by name and description.
- **Inputs and outputs** per tool - typed arguments and a structured (usually dict/JSON)
  return so the agent can reason over results.
- **What it talks to** - an HTTP API, a local file/db, a CLI, the user's own code.
- **Secrets** it needs - API keys, tokens, base URLs.
- **Which tools are destructive** vs read-only - this drives Glaido's approval defaults
  (see Step 4).

## Step 2 - Choose language and a stable location

**Language:** default to **Python + FastMCP, run via `uv`** when the user has no preference -
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
- a first-time user often doesn't have it yet. Quick check:

```bash
command -v uv      # Python servers (recommended launcher)
command -v node    # TypeScript servers
command -v npx     # running published servers / TypeScript
```

On Windows, use `where uv` / `where node` / `where npx` instead (or PowerShell's
`Get-Command`).

If it's missing, install it before continuing - see
[references/installing-runtimes.md](references/installing-runtimes.md) for per-OS commands.
For Python, **recommend `uv`**: `uv run` creates the isolated environment, installs
dependencies, and even fetches Python for you, so the user never has to deal with virtualenvs
or a separate Python install. Don't assume it's there - check.

## Step 3 - Scaffold the folder

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

## Step 4 - Implement the server

Whichever language, these rules make a server that behaves well inside Glaido:

- **Give the server a clear `instructions` string - it's how the agent knows the server
  exists and when to reach for it.** MCP sends this server-level text to the model (in the
  `initialize` response) as a hint about what the whole server is for, separate from the
  per-tool descriptions. Write it as a "use this server to…" statement that names the domain
  and the kinds of actions it covers (e.g. "Use to manage the user's Todoist tasks - search,
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

## Step 5 - Set up environment variables

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

## Step 6 - Write the mcp.json

This is the file Glaido reads. It must be named exactly `mcp.json` and sit at the folder root.
Full schema and field reference: [references/glaido-integration.md](references/glaido-integration.md).
The essentials:

```json
{
  "mcpServers": {
    "My Server": {
      "type": "stdio",
      "instructions": "One-line description of what this server does.",
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/my-server", "run", "server.py"],
      "env": {}
    }
  }
}
```

- **`type` is `stdio`** for local servers - that's what this skill targets.
- **`instructions` is the display description** shown under the server's name in the Glaido
  app - always set it. It is independent from the MCP server-level instructions your server
  code sends to the model (e.g. FastMCP's `instructions=`); set both.
- **`command` must be resolvable on the user's PATH** (`uv`, `npx`, `node`, `python3`, …). If
  it might not be, use an absolute path to the binary.
- **Every path must be absolute.** Relative paths are not expanded. Generate the real path with
  `pwd` in the server folder and substitute it - don't leave the placeholder.
- **Exception: folders the user imports may omit paths entirely.** On import, the current
  Glaido beta sets the server's working directory to the imported folder, so
  `"command": "uv", "args": ["run", "server.py"]` works with no path anywhere (this is how
  the hello-world example ships). Absolute paths remain the safest default for generated
  servers; use the path-free form when the folder is definitely imported via the Tools page.
- The key (`"My Server"`) is the display name; Glaido derives a clean ID from it.
- **Windows:** `npx` and `npm` are `.cmd` batch shims, which Windows cannot launch directly -
  Glaido will fail to start them even though they work in your terminal. Wrap them in `cmd`:
  `"command": "cmd", "args": ["/c", "npx", "-y", "<package>"]`. Real executables
  (`uv`, `uvx`, `node`) need no wrapper.

## Step 7 - Validate before handing off

Run the bundled checker against the folder - it catches the common import-blockers (missing or
malformed `mcp.json`, relative paths, a `command` not on PATH, committed secrets, and whether
the process even launches):

```bash
python3 <path-to-this-skill>/scripts/validate_glaido_mcp.py /ABSOLUTE/PATH/TO/my-server
```

(The script is [scripts/validate_glaido_mcp.py](scripts/validate_glaido_mcp.py), relative to
this skill's folder. On Windows, run it with `python` instead of `python3`.)

Then start the server by hand to confirm it boots and exposes its tools without crashing - the
language reference gives the exact command (e.g. `uv run server.py`). Fix anything the checker
or the launch surfaces before telling the user it's ready.

## Step 8 - Hand off: ALWAYS end with the import steps

Assume the user will not read your explanation - they skim to the end and act on the last
thing they see. Whatever else you report, your **final message must end** with the import
steps below, filled in with the real folder path and keys. Never bury them mid-message or
summarize them away.

End your final message with exactly this structure:

1. *(only if the server needs keys)* Open `<folder>/.env` and fill in the real values
   (copy from `.env.example` if `.env` doesn't exist yet).
2. Open the **Glaido** app and click **Tools** in the sidebar, under **Agent**.
3. Click **Import** (top right). Your file browser opens (Finder on macOS, File Explorer
   on Windows).
4. Navigate to `<folder>` and select the **whole folder** - the folder itself, not a file
   inside it - then confirm with **Open**.
5. The server appears in the list - switch its toggle on.
6. Try it: open Agent Mode and say *"<one-sentence voice command that uses the new tool>"*.

Destructive tools may ask for approval the first time, which is expected. If the server
doesn't connect, point them at the troubleshooting section in
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
| Ready-made first tool (weather, no API key) | [examples/hello-world-weather/](../examples/hello-world-weather/) |

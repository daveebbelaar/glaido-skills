# Glaido Integration Reference

Everything about how a local MCP server connects to the Glaido desktop app: the `mcp.json`
file Glaido reads, how it runs the server, how environment variables reach the process, and
how to fix a server that won't connect.

## Table of contents

- [The mcp.json file](#the-mcpjson-file)
- [Field reference](#field-reference)
- [How Glaido runs the server](#how-glaido-runs-the-server)
- [Environment variables](#environment-variables)
- [Importing in the Glaido app](#importing-in-the-glaido-app)
- [Tool approval](#tool-approval)
- [Requirements checklist](#requirements-checklist)
- [Troubleshooting](#troubleshooting)

## The mcp.json file

`mcp.json` is the only file Glaido requires to import a server. It must:

- be named exactly `mcp.json` (a legacy `.mcp.json` is also accepted, but use `mcp.json`),
- sit at the **root** of the folder the user imports,
- be valid JSON with a top-level `mcpServers` object.

Minimal local (stdio) server:

```json
{
  "mcpServers": {
    "My Server": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/Users/you/servers/my-server", "run", "server.py"],
      "env": {}
    }
  }
}
```

You can define more than one server under `mcpServers`, but one server per folder is the
clean default.

## Field reference

Each entry under `mcpServers` is keyed by a **display name** and supports:

| Field | Required | Default | Meaning |
|-------|----------|---------|---------|
| `type` | no | `stdio` | Transport. Use `stdio` for local servers - this is what the skill targets. Remote types (`sse`, `http`) can be listed but are read-only in the app and configured by hand. |
| `command` | **yes** | - | Executable to launch, resolved on the user's PATH (`uv`, `npx`, `node`, `python3`). Use an absolute path if it might not be on PATH. |
| `args` | no | `[]` | Arguments passed to `command`, each as its own array element. |
| `workingDirectory` | no | - | Absolute path the command runs in. If omitted, Glaido infers it from a `--directory` arg or the command's parent directory. |
| `env` | no | `{}` | Environment variables passed to the process as string key/value pairs. |
| `name` | no | the key | Friendly display name; falls back to the object key. |
| `instructions` | no | - | Short description of what the server does, shown in the **app UI**. `description` works as a fallback. Note: this is a Glaido display field - *not* the MCP server-level `instructions` your SDK sets (FastMCP's `instructions=`), which goes to the model. The two are independent; set both. |
| `status` | no | `enabled` | `enabled` or `disabled`. |
| `toolApproval` | no | `{}` | Per-tool approval policy: `{ "tool_name": "auto" \| "ask" \| "deny" }`. See [Tool approval](#tool-approval). |

The display-name key is turned into a clean internal id (lowercased, non-alphanumerics → `_`),
so prefer simple names like `"Todoist"` or `"My Server"`.

## How Glaido runs the server

On every run, Glaido spawns the process as:

```
<command> <args...>     # in workingDirectory (or the inferred directory)
```

with the `env` entries injected. The server is expected to speak MCP (JSON-RPC) over
**stdin/stdout**. Two consequences matter:

1. **The folder is referenced by absolute path and is not copied.** The server runs from
   wherever it lives on disk. If the user moves the folder after importing, the path in the
   stored config is stale and the server fails to launch until updated. Keep the folder in a
   stable location.
2. **stdout is the protocol channel.** Anything the server prints to stdout that isn't an MCP
   message corrupts the stream. All logging must go to stderr. (See Troubleshooting.)

## Environment variables

There are two ways to get secrets and config into the server. They are not mutually exclusive.

### 1. Local `.env` loaded by the server (default for this skill)

The server loads a `.env` file from its own folder at startup, using the language's standard
dotenv loader.

- `.env.example` (committed) lists the keys with placeholder values.
- `.env` (gitignored) holds the real values.
- Load relative to the **code file**, not the working directory, so it's robust:
  - Python: `load_dotenv(Path(__file__).resolve().parent / ".env")`
  - Node: `dotenv.config({ path: path.join(__dirname, ".env") })`

Why prefer this: secrets stay in a local, gitignored file next to the code and never end up
inside the config the user imports.

### 2. The `env` block in mcp.json

Glaido passes every key/value in a server's `env` object to the process as an environment
variable. No dotenv needed:

```json
"env": { "SERVICE_BASE_URL": "https://api.example.com", "FEATURE_FLAG": "true" }
```

Use this for **non-secret configuration** (base URLs, flags, regions). You *can* put secrets
here too, but then the secret lives inside `mcp.json` - which is easy to commit by accident
and is copied into Glaido's own config on import. Prefer `.env` for anything sensitive.

A clean combination: non-secret config in the `env` block, secrets in `.env`.

## Importing in the Glaido app

Tell the user to:

1. Open **Glaido → Settings → MCP Servers**.
2. Click **Import**.
3. Select the **folder** that contains `mcp.json` (select the folder, not the file).
4. The server shows up in the list; toggle it on to enable it.
5. If a key is missing or wrong, the server shows as failed/disconnected - fix `.env` and
   re-enable.

If the folder doesn't contain an `mcp.json`, Glaido reports an import failure - that's the
first thing to check.

## Tool approval

Glaido can run a tool automatically or pause to ask the user first. By default it decides per
tool from the tool's annotations:

- A tool marked **read-only** (`readOnlyHint: true`) can run automatically.
- A tool marked **destructive** (`destructiveHint: true`) prompts for approval.
- Unmarked tools are treated conservatively (prompt).

So annotate your tools honestly (the language references show how). You can also hard-set
policy in `mcp.json` via `toolApproval`, e.g. force a sensitive tool to always ask or to be
denied entirely:

```json
"toolApproval": { "delete_everything": "deny", "send_email": "ask", "list_items": "auto" }
```

## Requirements checklist

A folder is ready to import when:

- [ ] `mcp.json` exists at the folder root and is valid JSON with `mcpServers`.
- [ ] Each server has a non-empty `command` resolvable on PATH (or an absolute path).
- [ ] Every path in `args` / `workingDirectory` is **absolute**.
- [ ] `type` is `stdio` for local servers.
- [ ] The server writes nothing but MCP protocol to stdout (logs → stderr).
- [ ] Required keys are documented in `.env.example`; real secrets are in `.env` (gitignored).
- [ ] The server starts locally and lists its tools without crashing.

The bundled `scripts/validate_glaido_mcp.py` checks most of these automatically.

## Troubleshooting

**Server shows as failed / disconnected right after enabling**
- Most often stray stdout output. Confirm nothing prints to stdout except MCP messages - move
  every log/print/banner to stderr. A single stray line breaks the handshake.
- A missing or wrong key. Check `.env` has the real values and the server loads it from its
  own folder (by `__file__` path, not the cwd).

**"Import failed" / folder rejected**
- The selected folder has no `mcp.json` at its root, or the JSON is invalid. Validate it.

**Server connected before but broke later**
- The folder was moved or renamed. Glaido stored an absolute path; update `mcp.json` (and
  re-import or edit the config) to the new location.

**`command` not found**
- The launcher isn't on PATH in the environment Glaido runs in. Use an absolute path to the
  binary (e.g. the full path to `uv` or `node`), or install it where it's discoverable.

**Tool runs but errors on auth**
- The key is present but invalid/expired, or the server reads the wrong variable name. Confirm
  the variable name in code matches the one in `.env` / the `env` block.

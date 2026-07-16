# Reusing an existing third-party MCP server

When the goal is to connect Glaido to a **known service** — Notion, Slack, GitHub, Linear,
Stripe, Sentry, Postgres, Google Drive, Brave Search, filesystem access, and hundreds more —
there is very likely a maintained MCP server already. Reusing it is faster, more complete, and
better maintained than anything written from scratch in one session. Search before you build.

## Step 1 — Search (don't rely on memory)

Which servers exist changes constantly, so **use web search / a docs tool** rather than your
training data. Look in:

- **npm** — official servers are published under `@modelcontextprotocol/server-<name>`;
  community ones are often `<service>-mcp-server` or `mcp-server-<service>`.
- **GitHub** — the `modelcontextprotocol/servers` repo (reference + archived examples) and the
  service vendor's own org (many vendors now ship an official MCP server).
- **MCP registries / "awesome-mcp-servers" lists** — good for discovering community options.

Search queries like `"<service> MCP server"`, `"<service> modelcontextprotocol"`, or
`"@modelcontextprotocol/server <service>"`.

## Step 2 — Vet what you find

For each candidate, note:

- **What tools it exposes** and whether they cover what the user asked for.
- **Auth** it needs — API key, OAuth token, a local credential file — and whether the user can
  obtain it.
- **How it runs** — usually `npx -y <package>` (Node) or `uvx <package>` (Python). Both fit
  Glaido's local stdio model with no build step.
- **Maintenance and trust** — recent commits, downloads/stars, whether it's official. The
  user is granting it whatever access its credentials allow, so prefer official/well-used ones
  and read what it does.
- **Local vs remote** — this skill targets **local** servers. Prefer one that runs locally
  over stdio. (A hosted/remote server is configured by hand in Glaido and is out of scope
  here.)

## Step 3 — Ask the user what they actually want

A capable third-party server often exposes far more than the user needs. Before wiring it up,
ask:

- Which capabilities do you need? (e.g. "read issues and comment" vs "full repo admin")
- Anything that should be **off-limits** — destructive tools to disable or deny?
- What account / workspace / scope should it use?
- Any defaults to change?

Use the answers to decide which tools to enable and what approval policy to set.

## Step 4 — Wire it into a Glaido-ready folder

Create a folder for it (same shape as a built server) and an `mcp.json` that runs it. Two
common patterns:

**Run a published package directly (preferred — no vendoring):**

```json
{
  "mcpServers": {
    "GitHub": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {}
    }
  }
}
```

Python-published servers use `uvx`:

```json
{ "command": "uvx", "args": ["some-mcp-server"], "env": {} }
```

**Vendor (clone) it** only if you need to modify behavior, pin a version, or it isn't
published. Clone into the folder, build/install per its README, and point `command`/`args` at
the local entrypoint with an absolute path.

## Step 5 — Credentials and tool scoping

- **Secrets:** put the server's required keys/tokens in the folder's `.env` (gitignored) and
  document them in `.env.example`. If the third-party server only reads its config from the
  process environment (most do), pass them via the `mcp.json` `env` block instead — non-secret
  values are fine inline; for secrets, prefer the `.env` and have the user fill it in, or warn
  them the value will live in the config.
- **Disabling unwanted tools:** if the user wanted only a subset, set the others to `"deny"` in
  `toolApproval` so they never run, and `"ask"` for anything destructive they want to keep but
  gate. See [glaido-integration.md](glaido-integration.md#tool-approval).

## Step 6 — Validate and hand off

Run `scripts/validate_glaido_mcp.py` on the folder, confirm the server launches (`npx -y
<pkg>` / `uvx <pkg>` should start and wait on stdin), then give the user the standard import
steps and tell them which keys to set in `.env`.

## When to build instead

Fall back to building a custom server (the Step 1B path in SKILL.md) when:

- nothing exists for the service, or the options are unmaintained/low quality;
- the user wants to wrap **their own** API, database, scripts, or local actions;
- the user explicitly wants a minimal custom server they fully control.

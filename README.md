# Glaido Skills

Agent skills for building with [Glaido](https://glaido.com) - the AI dictation and voice
assistant for your desktop.

A **skill** is a folder of instructions, references, and templates that coding agents (Claude
Code, Cursor, Codex, and others) load on demand to do a specific job well. The skills in this
repository teach your agent how to extend and integrate with Glaido, so you can say "make
Glaido able to send Slack messages" and get a working result.

## Quick start: your first tool

You don't need to clone anything or write any code. Copy this prompt into your coding agent
(Claude Code, Cursor, Codex, or any other) and let it do the rest:

> I'm setting up Tools for the Glaido dictation app. Read this guide and follow the
> instructions for coding agents: https://docs.glaido.com/docs/beta/tools
>
> Build the hello-world weather example from the guide (current weather for any city, using
> the free Open-Meteo API, no API key needed). It's a fixed demo: just run the commands from
> the guide without planning or questions, then tell me the exact folder to pick when I
> click Import on Glaido's Tools page.

The agent fetches the skill from this repository, copies the ready-made
[hello-world weather server](examples/hello-world-weather/), and hands you a folder to import
on Glaido's Tools page. Then describe the tool you actually want, the same way.

## Available skills

- [`creating-glaido-mcp-servers`](creating-glaido-mcp-servers/) - Build a local MCP server
  that imports directly into the Glaido desktop app: scaffold the server (Python, TypeScript,
  or any language), wire up secrets, write the `mcp.json`, validate it, and import it. Also
  covers reusing existing third-party MCP servers.

## Using a skill

### Claude Code

Copy the skill folder into your project's `.claude/skills/` (or `~/.claude/skills/` to make it
available everywhere):

```bash
git clone https://github.com/daveebbelaar/glaido-skills.git
mkdir -p ~/.claude/skills
cp -r glaido-skills/creating-glaido-mcp-servers ~/.claude/skills/
```

Then just ask for what you want - for example, *"connect Glaido to my Notion workspace"* - and
the skill triggers automatically.

### Codex (OpenAI)

Copy the skill folder into your project's `.agents/skills/` (or `~/.agents/skills/` to make it
available everywhere):

```bash
git clone https://github.com/daveebbelaar/glaido-skills.git
mkdir -p ~/.agents/skills
cp -r glaido-skills/creating-glaido-mcp-servers ~/.agents/skills/
```

Codex picks up new skills automatically. Run `/skills` to confirm it's listed, or type `$` to
mention it directly; otherwise it triggers on matching requests just like in Claude Code.

### Other agents

Any agent that supports [agent skills](https://agentskills.io) can use these - point it at the
skill folder, or paste the `SKILL.md` as context. The referenced files (`references/`,
`assets/`, `scripts/`) live alongside it.

> The commands above are safe to re-run: `mkdir -p` does nothing if the folder already exists,
> and copying only adds or updates this one skill without touching any other skills you have
> installed. On Windows, run them in PowerShell.

## Repository layout

```text
creating-glaido-mcp-servers/
    ├── SKILL.md            # Entry point the agent reads first
    ├── references/         # Deep-dive docs the skill links to
    ├── scripts/            # Validation tooling
    └── assets/templates/   # Copyable starter projects
examples/
    └── hello-world-weather/  # Ready-to-import first tool (no API key)
```

## Examples

- [`examples/hello-world-weather`](examples/hello-world-weather/) - the simplest useful
  Glaido tool: current weather for any city via the free Open-Meteo API. No API key, no
  `.env`, nothing to sign up for, no paths to edit. Import the folder on Glaido's Tools
  page as-is and ask *"What's the weather in Amsterdam?"*

## Links

- [Glaido](https://glaido.com)
- [Glaido documentation](https://docs.glaido.com)
- [Model Context Protocol](https://modelcontextprotocol.io)

## License

[MIT](LICENSE)

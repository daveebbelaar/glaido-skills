# Glaido Skills

Agent skills for building with [Glaido](https://glaido.com) - the AI dictation and voice
assistant for your desktop.

A **skill** is a folder of instructions, references, and templates that coding agents (Claude
Code, Cursor, Codex, and others) load on demand to do a specific job well. The skills in this
repository teach your agent how to extend and integrate with Glaido, so you can say "make
Glaido able to send Slack messages" and get a working result.

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

### Other agents

Any agent that supports [agent skills](https://agentskills.io) can use these - point it at the
skill folder, or paste the `SKILL.md` as context. The referenced files (`references/`,
`assets/`, `scripts/`) live alongside it.

## Repository layout

```text
creating-glaido-mcp-servers/
    ├── SKILL.md            # Entry point the agent reads first
    ├── references/         # Deep-dive docs the skill links to
    ├── scripts/            # Validation tooling
    └── assets/templates/   # Copyable starter projects
```

## Contributing

Issues and pull requests are welcome. If you've built something with Glaido that others could
reuse - a skill, a template, an integration pattern - we'd love to include it.

## Links

- [Glaido](https://glaido.com)
- [Glaido documentation](https://docs.glaido.com)
- [Model Context Protocol](https://modelcontextprotocol.io)

## License

[MIT](LICENSE)

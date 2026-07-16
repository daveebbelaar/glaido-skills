# TypeScript / Node MCP server

A local MCP server built with the official TypeScript SDK
(`@modelcontextprotocol/sdk`), run with Node over stdio. Glaido launches it like
`node /abs/path/dist/index.js` (or via `npx` for a published package).

Copyable starter files live in [../assets/templates/typescript/](../assets/templates/typescript/).

**Prerequisite:** Node.js must be installed (`command -v node` and `command -v npx`). If it
isn't, install the LTS first — see [installing-runtimes.md](installing-runtimes.md).

## Folder layout

```text
my-server/
├── src/
│   └── index.ts        # server + tool definitions
├── dist/               # compiled output (built before import)
├── package.json
├── tsconfig.json
├── mcp.json            # Glaido import config (absolute paths)
├── .env.example
├── .env                # gitignored
├── .gitignore
└── README.md
```

Glaido runs compiled JS, so **build before importing** (`npm run build`) and point `mcp.json`
at `dist/index.js`. (Alternatively run TypeScript directly with `tsx`, but shipping built JS
is the most reliable.)

## package.json

```json
{
  "name": "glaido-mcp-my-server",
  "version": "0.1.0",
  "type": "module",
  "bin": { "glaido-mcp-my-server": "dist/index.js" },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "dotenv": "^16.4.5",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "@types/node": "^22.0.0"
  }
}
```

## src/index.ts

```typescript
import { fileURLToPath } from "node:url";
import path from "node:path";
import { config as loadEnv } from "dotenv";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Load secrets from THIS folder's .env, regardless of cwd.
const __dirname = path.dirname(fileURLToPath(import.meta.url));
loadEnv({ path: path.join(__dirname, "..", ".env") });

// `instructions` is server-level guidance: it goes into the MCP `initialize` response, which
// the client passes to the model as a hint about what this server is for and WHEN to use it
// (separate from the per-tool descriptions). Write a "use this server to…" statement.
const server = new McpServer(
  { name: "My Server", version: "0.1.0" },
  {
    instructions:
      "Use this server to <do X> with <service/domain>. " +
      "Covers <the kinds of actions, e.g. searching, creating, updating items>.",
  },
);

server.registerTool(
  "search_items",
  {
    description: "Search items by free-text query. Read-only.",
    inputSchema: { query: z.string(), limit: z.number().optional() },
    annotations: { readOnlyHint: true, openWorldHint: true },
  },
  async ({ query, limit }) => {
    const data = await doSearch(query, limit); // your logic
    return { content: [{ type: "text", text: JSON.stringify({ status: "ok", data }) }] };
  },
);

server.registerTool(
  "delete_item",
  {
    description: "Delete an item by id. Destructive — Glaido will ask before running.",
    inputSchema: { id: z.string() },
    annotations: { readOnlyHint: false, destructiveHint: true },
  },
  async ({ id }) => ({
    content: [{ type: "text", text: JSON.stringify({ status: "ok", deleted: id }) }],
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

Key points:

- **`StdioServerTransport`** is what Glaido uses for local servers.
- **Describe each tool clearly** — the description is what the agent reads to choose the tool.
- **Use `zod` for `inputSchema`**; it becomes the argument schema the agent sees.
- **Annotate read-only vs destructive** via `annotations` — Glaido uses these to decide
  whether a tool runs automatically or prompts the user. Set `openWorldHint: true` for tools
  that reach an external system.
- Return content as text; JSON-stringified structured data lets the agent reason over results.

## The stdout rule (critical)

stdout is the MCP channel. **Never `console.log`** — it corrupts the stream and Glaido marks
the server failed. Use `console.error` (stderr) for any logging:

```typescript
console.error("debug info"); // safe — stderr
// console.log("...")        // BREAKS the server
```

## Environment variables

`.env.example` (committed): `SERVICE_API_KEY=replace_with_your_key`

```typescript
const apiKey = process.env.SERVICE_API_KEY ?? "";
```

Return a structured error from the tool when a key is missing rather than throwing at startup.

## mcp.json

Published package (no local build needed):

```json
{
  "mcpServers": {
    "My Server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "glaido-mcp-my-server"],
      "env": {}
    }
  }
}
```

Local built output:

```json
{
  "mcpServers": {
    "My Server": {
      "type": "stdio",
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/my-server/dist/index.js"],
      "env": {}
    }
  }
}
```

Replace the path with the real absolute path (`pwd`). `node`/`npx` must be on PATH.

## Build, run, test

```bash
cd my-server
npm install
npm run build
node dist/index.js        # should start and wait on stdin without printing to stdout

# inspect interactively:
npx @modelcontextprotocol/inspector node dist/index.js
```

Rebuild (`npm run build`) after any code change before re-testing in Glaido, since it runs the
compiled `dist/`.
